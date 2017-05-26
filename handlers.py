# coding=utf-8
# 
import asyncio
import webform


__author__ = 'Michael Liao'

' url handlers '


@webform.get('/blog/{id}')
def get_blog(id):
    body = '<h1>Blog id:%s</h1>' % id.match_info['id']
    return body
