#!/usr/bin/python3.5
#coding=utf8
from config import config
import redis
import time
import json
import os
import hashlib
import zipfile

def cli():
    queueCode = config['queue']
    redisPort = config['redisPort']
    redisHost = config['redisHost']
    re_queue  = redis.Redis(host=redisHost, port=redisPort)

    if re_queue.llen(queueCode) <= 0:
        print('当前队列无消息！')
        return False
    else:
        return True

def doing():
    redisPort   = config['redisPort']
    redisHost   = config['redisHost']
    re_queue    = redis.Redis(host=redisHost, port=redisPort)
    queueCode   = config['queue']
    try:
        result = re_queue.rpop(queueCode)
        result = json.loads(result)
    except:
        print('脏数据忽略'+result)

    try:
        workPath    = config['workPath']#工作路径
        queueCode   = config['queue']
        outputPath  = config['outputPath']
        fileName    = config['fileName']
        zipPath     = config['zipPath']

        # 接收值，简单优化后加入队列
        if not os.path.exists(workPath):
            os.makedirs(workPath)# 创建工作目录
        gitUrl         = result['gitUrl']
        projectName    = result['projectName']
        # gitUrl = "http://mygitlab.com:8081/root/composer-sync.git"

        ProjectWorkPath = workPath + projectName + '/'
        if os.path.exists(ProjectWorkPath):
            gitStatus = os.system("cd " + ProjectWorkPath + " && git pull " + gitUrl)# pull
        else:
            gitStatus = os.system("cd " + workPath + " && git clone " + gitUrl)# clone


        # if gitStatus == 0:
        #     print('无任何更新，不需要做任何动作')
        #     return


        # 检查comoser文件
        composer_file = ProjectWorkPath + fileName
        composerInfo = open(composer_file, 'r+')
        composerInfo = composerInfo.read()

        md5Val = hashlib.md5()
        composerInfo = composerInfo.encode(encoding='utf-8')
        md5Val.update(composerInfo)
        md5Json = md5Val.hexdigest()

        # 检查版本库是否有此文件(当无版本文件则执行compoer update)
        zipFileName = outputPath +projectName + '_' + md5Json + '.zip'
        if os.path.exists(zipFileName):
            print('当前版本已有压缩包'+zipFileName)
            return '当前版本已有压缩包'
        #更新composer

        res = os.system("cd " + ProjectWorkPath + " && composer update")
        if res != 0:
            print('更新失败')
            #调用插入队列def
            RollbackJob(re_queue,result)

        createZip(ProjectWorkPath+zipPath,zipFileName)
        #检查文件是否生成
        if os.path.exists(zipFileName):
            print('版本包已生成')
        else:
            RollbackJob(re_queue,result)
            print('调用回滚队列方法')
            RollbackJob(re_queue,result)
    except Exception as ex_results:
        print('捕获异常',ex_results)
        res = re_queue.lpush(queueCode, json.dumps(result))


def RollbackJob(re_queue,params):
    result = re_queue.lpush(json.dumps(params))
    print('回滚状态')
    print(result)

def createZip(filePath,savePath,note = ''):
    '''
    将文件夹下的文件保存到zip文件中。
    :param filePath: 待备份文件
    :param savePath: 备份路径
    :param note: 备份文件说明
    :return:
    '''
    fileList=[]
    if len(note) == 0:
        target = savePath
    else:
        target = savePath
    newZip = zipfile.ZipFile(target,'w')
    for dirpath,dirnames,filenames in os.walk(filePath):
        for filename in filenames:
            fileList.append(os.path.join(dirpath,filename))
    for tar in fileList:
        newZip.write(tar,tar[len(filePath):])#tar为写入的文件，tar[len(filePath)]为保存的文件名
    newZip.close()
    print('backup to',target)

if __name__ =='__main__':
    status = cli()
    if status == True:
        doing()