# coding=utf-8
# pool.py
# created:2017-05-25
# description:用来创建连接池
# ref01：http://lib.csdn.net/snippet/python/47292
# ref02：https://github.com/wl356485255/pythonORM/blob/master/orm.py
# ref03：https://github.com/wl356485255/pythonORM/blob/master/ormTest.py
import asyncio
import logging
import aiomysql


global __pool  # 存储池


logging.basicConfig(level=logging.INFO)


def log(sql, args=()):
    logging.info('SQL: %s' % (sql))


@asyncio.coroutine
def create_pool(loop, **kw):
    logging.info('create database connetion pool...')
    global __pool
    __pool = yield from aiomysql.create_pool(
        host=kw.get('host', 'localhost'),
        port=kw.get('port', 3306),
        user=kw['user'],
        password=kw['password'],
        db=kw['db'],
        charset=kw.get('charset', 'utf8'),  # http://www.liaoxuefeng.com/discuss/001409195742008d822b26cf3de46aea14f2b7378a1ba91000/001451894920450a22651047f7f4a4ca2d0aea99d1452a2000
        autocommit=kw.get('autocommit', True),
        maxsize=kw.get('maxsize', 10),
        minsize=kw.get('minsize', 1),
        loop=loop
    )


# 这个是封装SQL的select语句
async def select(sql, args, size=None):
    log(sql, args)
    global __pool
    async with __pool.get() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql.replace('?', '%s'), args or ())
            if size:
                rs = await cur.fetchmany(size)
            else:
                rs = await cur.fetchall()
        logging.info('rows returned: %s' % len(rs))
        return rs


# 封装INSERT, UPDATE, DELETE 语句
# 返回操作影响的行号
async def execute(sql, args, autocommit=True):
    log(sql)
    global __pool
    async with __pool.get() as conn:
        if not autocommit:
            await conn.begin()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql.replace('?', '%s'), args)
                affected = cur.rowcount
            if not autocommit:
                await conn.commit()  # 如果没有自动保存修改就会立即修改
        except BaseException as e:
            if not autocommit:
                await conn.rollback()
            raise
        return affected


# 根据输入的参数生成的占位符列表
def create_args_string(num):
    L = []
    for n in range(num):
        L.append('?')
    return ','.join(L)


# 定义Field类，负责保存(数据库)表的字段名和字段类型
class Field(object):

    # 表的字段的名字、类型、是否为主键、默认值
    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    # 打印数据库 __reper__ __str__也是可以的
    def __str__(self):
        print('<%s, %s, %s>' % (self.__class__.__name__, self.column_type, self.name))


# -*- 定义不同类型的衍生Field -*-
# -*- 表的不同列的字段的类型不一样
class StringField(Field):

    def __init__(self, name=None, primary_key=False, default=None, column_type='var'):
        super().__init__(name, column_type, primary_key, default)

    def __str__(self):  # 特例化的
        return 'StringField'


class BooleanField(Field):

    def __init__(self, name=None, default=None):
        super().__init__(name, 'boolean', False, default)

    def __str__(self):
        return 'BooleanField'


class IntegerField(Field):

    def __init__(self, name=None, primary_key=False, default=None):
        super().__init__(name, 'bigint', primary_key, default)

    def __str__(self):
        return 'IntegerField'


class FloatField(Field):

    def __init__(self, name=None, primary_key=False, default=None):
        super().__init__(name, 'real', primary_key, default)

    def __str__(self):
        return 'FloatField'


class TextField(Field):

    def __init__(self, name=None, default=None):
        super().__init__(name, 'Text', False, default)

    def __str__(self):
        return 'TextField'


# -*-定义Model的元类
 
# 所有的元类都继承自type
# ModelMetaclass元类定义了所有Model基类(继承ModelMetaclass)的子类实现的操作
 
# -*-ModelMetaclass的工作主要是为一个数据库表映射成一个封装的类做准备：
# ***读取具体子类(user)的映射信息
# 创造类的时候，排除对Model类的修改
# 在当前类中查找所有的类属性(attrs)，如果找到Field属性，就将其保存到__mappings__的dict中，同时从类属性中删除Field(防止实例属性遮住类的同名属性)
# 将数据库表名保存到__table__中
 
# 完成这些工作就可以在Model中定义各种数据库的操作方法
class ModelMetaclass(type):
    # __new__控制__init__的执行，所以在其执行之前
    # cls:代表要__init__的类，此参数在实例化时由Python解释器自动提供(例如下文的User和Model)
    # bases：代表继承父类的集合
    # attrs：类的方法集合
    def __new__(cls, name, bases, attrs):
        # 排除Model
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)
        # 获取table名词
        tableName = attrs.get('__table__', None) or name
        logging.info('found model %s (table: %s)' % (name, tableName))
        # 获取Field和主键的名称
        mappings = dict()
        fields = []
        primaryKey = None  # 这个是主键
        for k, v in attrs.items():
            if isinstance(v, Field):
                logging.info('  found mapping: %s ---> %s' % (k, v))
                mappings[k] = v
                # 是否是主键
                if v.primary_key:
                    if primaryKey:
                        raise RuntimeError('Duplicate primary key for field:')
                    primaryKey = k
                else:
                    fields.append(k)  # 所有非主键
        if not primaryKey:  # 不可能没有主键
            raise RuntimeError('No primary key')
        for k in mappings.keys():  # 把所有属性相同的属性去掉
            attrs.pop(k)
        escaped_fields = list(map(lambda f: '`%s`' % f, fields))  

        attrs['__mappings__'] = mappings
        attrs['__table__'] = tableName
        attrs['__primary_key__'] = primaryKey  # 这个是主键（关键字）
        attrs['__fields__'] = fields

        attrs['__select__'] = 'select `%s`, %s from `%s`' % (primaryKey, ', '.join(escaped_fields), tableName)
        attrs['__insert__'] = 'insert into  `%s` (%s, `%s`) values(%s)' % (tableName, ', '.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tableName, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)
        attrs['__delete__'] = 'delete from  `%s` where `%s`=?' % (tableName, primaryKey)
        return type.__new__(cls, name, bases, attrs)

# 定义ORM所有映射的基类：Model
# Model类的任意子类可以映射一个数据库表
# Model类可以看作是对所有数据库表操作的基本定义的映射
# 基于字典查询形式
# Model从dict继承，拥有字典的所有功能，同时实现特殊方法__getattr__和__setattr__，能够实现属性操作
# 实现数据库操作的所有方法，定义为class方法，所有继承自Model都具有数据库操作方法


class Model(dict, metaclass=ModelMetaclass):

    def __init__(self, **kw):
        super(Model, self).__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r'"Model" objct has not attribute: %s' % (key))

    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self, key):
        return getattr(self, key, None)

    def getValueOrDefault(self, key):
        value = getattr(self, key, None)
        if not value:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
            logging.debug('using default value for %s: %s' % (key, str(value)))
            setattr(self, key, value)
        return value

    @classmethod
    # 类方法有类变量cls传入，从而可以用cls做一些相关的处理。并且有子类继承时，调用该类方法时，传入的类变量cls是子类，而非父类。
    async def findAll(cls, where=None, args=None, **kw):
        '''find objects by where clause'''
        sql = [cls.__select__]

        if where:
            sql.append('where')
            sql.append(where)

        if args is None:
            args = []

        orderBy = kw.get('orderBy', None)
        if orderBy:
            sql.append('order by')
            sql.append(orderBy)

        limit = kw.get('limit', None)
        if limit is not None:
            sql.append('limit')
            if isinstance(limit, int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append('?,?')
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value: %s' % str(limit))
        rs = await select(' '.join(sql), args)
        return [cls(**r) for r in rs]

    @classmethod
    async def findNumber(cls, selectField, where=None, args=None):
        '''find number by select and where.'''
        sql = ['select %s __num__ from `%s`' % (selectField, cls.__table__)]
        if where:
            sql.append('where')
            sql.append(where)
        rs = await select(' '.join(sql), args, 1)
        if len(rs) == 0:
            return None
        return rs[0]['__num__']

    @classmethod
    async def find(cls, primarykey):
        '''find object by primary key'''
        rs = await select('%s where `%s`=?' % (cls.__select__, cls.__primary_key__), [primarykey], 1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])

    async def save(self):
        args = list(map(self.getValueOrDefault, self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        print(self.__insert__)
        rows = await execute(self.__insert__, args)
        if rows != 1:
            logging.warn('failed to insert record: affected rows: %s' % rows)  # 这些会报错不知道为什么

    async def update(self):
        args = list(map(self.getValue, self.__fields__))
        args.append(self.getValue(self.__primary_key__))
        rows = await execute(self.__update__, args)
        if rows != 1:
            logging.warn('failed to update by primary key: affected rows: %s' % rows)

    async def remove(self):
        args = [self.getValue(self.__primary_key__)]
        rows = await execute(self.__delete__, args)
        if rows != 1:
            logging.warn('failed to remove by primary key: affected rows: %s' %rows)


async def destory_pool():
    global __pool
    if __pool is not None:
        __pool.close()
        await __pool.wait_closed()


""" 不需要的测试代码
async def insert(loop):
    await create_pool(loop=loop, user='dev', password='19971222', db='users', host='localhost', port=3306)
    # 创建一个实例：
    u = User(idb=999999992, username='peic', email='peic@python.org', password='password')
    print(u)
    u.find(135)
    await u.save()
    await destory_pool()


async def remove(loop):
    await create_pool(loop=loop, user='dev', password='19971222', db='users', host='localhost', port=3306)
    d = await User.find(99999999)
    await d.remove()
    await destory_pool()


async def update1(loop):
    await create_pool(loop=loop, user='dev', password='19971222', db='users', host='localhost', port=3306)
    d = await User.find(12345)
    d.email = '54444878'
    d.password = 'dddfwf45445'
    await d.update()
    await destory_pool()


async def test(loop):
    await insert(loop)
    print('Insertion Ok...')
    await remove(loop)
    print('remove okay')
    await update1(loop)
    print('updating okay')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test(loop))
    loop.close()
"""


