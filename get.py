# coding=utf-8
#  GET发送请求 
import requests


login = {'cap': 'fffffds854'}
url = 'http://localhost:9000/blog'
# header = {'Content-Type': 'application/json'}
r = requests.get(url, params=login)
print(r.url)
print(r.status_code)
print(r.content.decode('utf-8'))
