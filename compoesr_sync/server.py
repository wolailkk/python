#!/usr/bin/python3.5
#coding=utf8
from flask import Flask,json,request,jsonify
from config import config
import os
import hashlib
import zipfile
import redis

app = Flask(__name__)
@app.route('/sync', methods=['POST'])

def sync():

    if request.method == 'POST':
        queueCode = config['queue']
        redisPort = config['redisPort']
        redisHost = config['redisHost']
        re_queue = redis.Redis(host=redisHost, port=redisPort)
        data    = request.json
        projectName   = data['project']['name']
        gitUrl        = data['project']['http_url']
        # gitUrl        = "http://mygitlab.com:8081/root/composer-sync.git"
        params = {"projectName":projectName,"gitUrl":gitUrl}
        res = re_queue.lpush(queueCode, json.dumps(params))
        print('加入队列序号')
        print(res)
        return "加入队列"
    else:
        return "<h1>请使用post方式</h1>"
if __name__ =='__main__':
    app.run(host='0.0.0.0', port=5000,debug=True)