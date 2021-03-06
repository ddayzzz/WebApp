# coding=utf-8
# Thanks to https://github.com/icemilk00/Python_L_Webapp/blob/master/www/app.py

"""
异步http服务器端
"""

import logging 
logging.basicConfig(level=logging.INFO)

import asyncio, os, json, time
from datetime import datetime

from aiohttp import web
from jinja2 import Environment, FileSystemLoader

import pool  # 数据库连接存储池
from webform import add_routes, add_static  # web框架

# import config
import config


# 定义模板引擎 http://docs.jinkan.org/docs/jinja2/
def init_jinja2(app, **kw):
    logging.info('init jinja2...')
    options = dict(
        autoescape=kw.get('autoescape', True),
        block_start_string=kw.get('block_start_string', '{%'),
        block_end_string=kw.get('block_end_string', '%}'),
        variable_start_string=kw.get('variable_start_string', '{{'),
        variable_end_string=kw.get('variable_end_string', '}}'),
        auto_reload = kw.get('auto_reload', True)
    )
    path = kw.get('path', None)
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    logging.info('set jinja2 template path: %s' % path)
    env = Environment(loader=FileSystemLoader(path), **options)
    filters = kw.get('filters', None)
    if filters is not None:
        for name, f in filters.items():
            env.filters[name] = f
    app['__templating__'] = env


# 显示一个请求
async def logger_factory(app, handler):
    async def logger(request):
        logging.info('Request: %s %s' % (request.method, request.path))
        return (await handler(request))  # 转到下一步response_factory
    return logger


# 数据处理
async def data_factory(app, handler):
    async def parse_data(request):
        if request.method == 'POST':
            # 检查HTTP头的Content-Type
            if request.content_type.startswith('application/json'):
                request.__data__ = await request.json()  # 格式化为JSON
                logging.info('request json: %s' % str(request.__data__))
            elif request.content_type.startswith('application/x-www-form-urlencoded'):
                request.__data__ = await request.post()  # 这个是表格的
                logging.info('request form: %s' % str(request.__data__))
        return (await handler(request))
    return parse_data


# 响应的抽象工厂
async def response_factory(app, handler):
    async def response(request):
        logging.info('Response handler...')
        r = await handler(request)  # 等待logger的处理完成
        if isinstance(r, web.StreamResponse):
            return r
        if isinstance(r, bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
        if isinstance(r, str):
            if r.startswith('redirect:'):
                return web.HTTPFound(r[9:])
            resp = web.Response(body=r.encode('utf-8'))
            resp.content_type = 'text/html;charset=utf-8'
            return resp
        if isinstance(r, dict):
            template = r.get('__template__')
            if template is None:
                resp = web.Response(body=json.dumps(r, ensure_ascii=False, default=lambda o: o.__dict__).encode('utf-8'))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else:
                resp = web.Response(body=app['__templating__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp
        if isinstance(r, int) and r >= 100 and r < 600:
            return web.Response(r)
        if isinstance(r, tuple) and len(r) == 2:
            t, m = r
            if isinstance(t, int) and t >= 100 and t < 600:
                return web.Response(t, str(m))
        # default:
        resp = web.Response(body=str(r).encode('utf-8'))
        resp.content_type = 'text/plain;charset=utf-8'
        return resp
    # 这都返回了正确的构造对象
    return response  # 处理完成 现在都是Response的对象 接下来就有路由关联的函数处理，也就是ResponseHandler


def datetime_filter(t):
    delta = int(time.time() - t)
    if delta < 60:
        return u'1分钟前'
    if delta < 3600:
        return u'%s分钟前' % (delta // 60)
    if delta < 86400:
        return u'%s小时前' % (delta // 3600)
    if delta < 604800:
        return u'%s天前' % (delta // 86400)
    dt = datetime.fromtimestamp(t)
    return u'%s年%s月%s日' % (dt.year, dt.month, dt.day)


async def init(loop):
    conf = config.configs
    await pool.create_pool(loop=loop, host=conf['db']['host'], port=conf['db']['port'], user=conf['db']['user'], password=conf['db']['password'], db=conf['db']['db'])
    # middlewares 是中间件，响应会经过logger_factor -> response_factory处理。handler是下一个处理对象
    app = web.Application(loop=loop, middlewares=[
        logger_factory, data_factory, response_factory
    ])
    init_jinja2(app, filters=dict(datetime=datetime_filter))
    add_routes(app, 'handlers')
    add_static(app)
    srv = await loop.create_server(app.make_handler(), conf['host'], conf['port'], )
    logging.info('server started at %s:%d' % (conf['host'], conf['port']))
    return srv

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()