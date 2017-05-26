# coding=utf-8
import asyncio
import webform


__author__ = 'Michael Liao'

' url handlers '


@webform.get('/blog/{id}&{un}')
def get_blog_get(**kw):
    return dict(**kw)


@webform.post('/login')
def get_login_post(*kw):
    return dict(*kw)
