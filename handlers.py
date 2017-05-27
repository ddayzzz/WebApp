# coding=utf-8
# 路由与处理绑定的模块
from webform import get, post
import models

' url handlers '


@get('/')
async def index(request):
    users = await models.User.findAll()
    return {
        '__template__': 'home.html',  # 指定了模板的网页
        'users': users
    }


# 可以自定义查询参数的blog示例
@get('/blog')
async def blog(username, email='ff', **kw):
    print(kw)
    return {
        username,
        email
    }


# match_path指定的类型
@get('/blog/{id}')
async def blog_id(id):
    return id


# POST接受
@post('/login')
async def login(username, password, email='none'):
    return {
        'hahaha',
        username,
        password,
        email
    }
