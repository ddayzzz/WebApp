# coding=utf-8
# 定义的模型 目前定义了用户的信息
import pool
from pool import IntegerField, StringField, FloatField


class User(pool.Model):
        __table__ = 'User'
        idb = IntegerField('idb', primary_key=True)
        username = StringField('username')
        email = StringField('email')
        password = StringField('password')
