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


@get('/blog/{id}')
async def blog(id):
    return {
        id
    }


@post('/login')
async def login(username, password, email='none'):
    return {
        'hahaha',
        username,
        password,
        email
    }
