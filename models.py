# coding=utf-8
# 定义的模型 目前定义了用户的信息
import pool
from pool import IntegerField, StringField, FloatField


class User(pool.Model):
        __table__ = 'User'
        id = IntegerField('id', primary_key=True)
        name = StringField('name')
        email = StringField('email')
        passwd = StringField('passwd')


class Blog(pool.Model):
        __table__ = 'Blog'
        id = IntegerField('id', primary_key=True)
        name = StringField('name')
        user_id = StringField('user_id')
        summary = StringField('summary')
        created_at = FloatField('created_at')
