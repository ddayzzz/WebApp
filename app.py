# coding=utf-8
# app.py
# created:2017-05-25
import logging
import asyncio, os, json, time
from datetime import datetime
from aiohttp import web


logging.basicConfig(level=logging.INFO)


def index(request):
    return web.Response(body=b'<h1>Awsome</h1>', content_type='text/html')  # 设置处理/请求发送的数据


@asyncio.coroutine
def init(loop):
    app = web.Application(loop=loop)
    app.router.add_route('GET', '/', index)  # 处理主页的请求的协程
    srv = yield from loop.create_server(app.make_handler(), '127.0.0.1', 9000)  # 监听的端口
    logging.info('server started at http://127.0.0.1:9000')
    return srv


loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()
