#!/usr/bin/env python

import os
import sys
import pysftp
from os import path

conf_name=".sftp.conf"
conf={}

class MyException(BaseException):
    def __init__(self,arg):
        self.arg = arg

def load_conf():
    conf_path = find_conf_path() 
    if not conf_path:
        raise MyException("no " + conf_name)

    conf["CONF_PATH"]=conf_path

    for line in open(conf_path+'/'+conf_name):
        if line.startswith('#'):
            continue

        s = line.split('=',2)
        conf[s[0].strip()]=s[1].strip()

    for k in ['USER_NAME','PASSWORD','HOST','PORT','REMOTE_BASE_DIR']:
        if not conf.has_key(k) or conf[k] == '':
            raise MyException("require %s" % k)

    if not conf.has_key('LOCAL_BASE_DIR') or conf['LOCAL_BASE_DIR']:
        conf['LOCAL_BASE_DIR'] = conf_path

def find_conf_path():
    conf_path = path.abspath(path.curdir)
    check = lambda : path.isfile(conf_path+'/'+conf_name)

    if check() :
        return conf_path

    while conf_path != "/":
        conf_path = path.dirname(conf_path)
        if check() :
            return conf_path

    return ""

def get_relpath():
    cur_path=os.getcwd()
    if not cur_path.startswith(conf['LOCAL_BASE_DIR']):
        raise MyException("not in current work directory")  

    relpath = path.relpath(cur_path ,conf['LOCAL_BASE_DIR'])
    return relpath


def get_local_relpath():
    src = sys.argv[2]
    if not path.isabs(src):
        src = path.abspath(src)
    
    if path.isfile(src):
        src = path.dirname(src)

    if not src.startswith(conf['LOCAL_BASE_DIR']):
        raise MyException("not in current work directory") 
    
    relpath = path.relpath(src ,conf['LOCAL_BASE_DIR'])
    return relpath

def get_conn():
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None 
    info = {"host":conf["HOST"],"port":int(conf["PORT"]),"username":conf["USER_NAME"],"password":conf["PASSWORD"]}
    sftp = pysftp.Connection(cnopts=cnopts,**info)
    try:
        sftp.makedirs(conf['REMOTE_BASE_DIR'])
        sftp.cwd(conf['REMOTE_BASE_DIR'])
    except:
        raise MyException("invalid REMOTE_BASE_DIR %s" % conf['REMOTE_BASE_DIR']) 

    return sftp

def get_remote_relpath():
    src = sys.argv[2]
    if not path.isabs(src):
        src = path.abspath(src) 
    src,tmp = path.split(src)

    if not src.startswith(conf['LOCAL_BASE_DIR']):
        raise MyException("not in current work directory") 
    
    relpath = path.relpath(src ,conf['LOCAL_BASE_DIR'])
    return relpath

def upload(target):
    relpath = get_relpath()
    sftp = get_conn()
    sftp.makedirs(relpath,mode=755)
    sftp.chdir(relpath)

    if path.isfile(target):
        sftp.put(target)
    else:
        if not sftp.exists(target):
            sftp.makedirs(target, mode=755)
        sftp.put_r(target, target, preserve_mtime=True) 

def download(target):
    sftp = get_conn()
    if not sftp.exists(target):
        raise MyException("%s does not exist" % target)

    relpath = get_relpath()
    sftp.chdir(relpath)
    print sftp.pwd
    print target
    if sftp.isfile(target):
        abspath = path.abspath(target)
        print abspath
        os.makedirs(path.dirname(target),mode=0777)
        sftp.get(target, abspath, preserve_mtime=True)
    else:
        abspath = path.abspath(target)
        print abspath
        sftp.get_r(target, os.getcwd(), preserve_mtime=True)

def diff(target):
    if not path.isfile(target):
        raise MyException("local %s is not a file" % target)

    sftp = get_conn()
    if not sftp.exists(target):
        raise MyException("%s does not exist" % target)
    if not sftp.isfile(target):
        raise MyException("remote %s is not a file" % target) 

    os.system("vimdiff %s scp://%s@%s:%s/%s/%s" % (target,conf["USER_NAME"], conf["HOST"],conf["PORT"],conf['REMOTE_BASE_DIR'],target))


if __name__ == "__main__":
    load_conf()

    command = sys.argv[1]
    targets =sys.argv[2:]
    if not targets:
        raise MyException("no target")

    if command == "upload":
        for i in targets:
            upload(i)
    elif command == "download":
        for i in targets:
            download(i)
    elif command == "diff":
        diff(targets[0])
    else:
        print "unknown command %s" % command

        
