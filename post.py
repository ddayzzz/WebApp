# coding=utf-8
#  POST发送请求 
import json
import requests


login = {'username': 'shu'}
url = 'http://localhost:9000/login'
header = {'Content-Type': 'application/json'}
r = requests.post(url, data=json.dumps(login), headers=header)
print(r.status_code)
print(r.content.decode('utf-8'))
