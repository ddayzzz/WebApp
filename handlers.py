# coding=utf-8
# 路由与处理绑定的模块
from webform import get, post
import models
import time

' url handlers '


@get('/')
async def index(request):
    summary = 'This is a universal summary for all the pages'
    blogs = [
        models.Blog(id='1', name='TEST BLOG', summary=summary, created_at=time.time()-120),
        models.Blog(id='2', name='TEST BLOG2', summary=summary, created_at=time.time()-3600)
    ]
    return {
        '__template__': 'index.html',
        'blogs': blogs  # 关键字可以直接在由jiaja2定义的html中使用
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
