"""
填充应用程序运行所需的数据

1. 填充数据库记录
2. 复制文件到指定的目录

目录结构抽象图

/
├── alice
│   ├── data            <-- 提取码共享整个目录
│   │   └── video
│   │       └── rm
│   ├── cp              <-- 匿名共享
│   ├── ls              <-- 提取码共享
│   └── mv              <-- 不共享
├── bob
│   ├── data            <-- 提取码共享整个目录
│   │   └── video
│   │       └── cat
│   ├── cut             <-- 匿名共享
│   ├── head            <-- 提取码共享
│   └── tail            <-- 不共享
└── charlie
    ├── data            <-- 提取码共享整个目录
    │   └── video
    │       └── grep
    ├── awk             <-- 匿名共享
    ├── sed             <-- 提取码共享
    └── sort            <-- 不共享

"""

import os
from os.path import abspath, dirname
import sys
import hashlib
import random
from datetime import timedelta
import subprocess as sub

import django
from django.utils import timezone

basedir = dirname(dirname(abspath(__file__)))
os.chdir(basedir)
sys.path.insert(0, '')
os.environ['DJANGO_SETTINGS_MODULE'] = 'pro1.settings'
django.setup()

from django.contrib.auth.models import User
from share.models import File, Directory, FileObject, Share


def digest(text=None, bytes=None, buffer=None, path=None):
    if text is bytes is buffer is path is None:
        raise TypeError('one of text/bytes/buffer/path is required')

    if text is not None:
        hash = hashlib.sha1(text.encode())
    elif bytes is not None:
        hash = hashlib.sha1(bytes)
    else:
        if buffer is None:
            buffer = open(path, 'rb')
        hash = hashlib.sha1()
        while True:
            chunk = buffer.read(512)
            if not chunk:
                break
            hash.update(chunk)
    return hash.hexdigest()


def gen_code():
    num = 8
    chars = [chr(x) for x in list(range(97, 123))
                + list(range(65, 91)) + list(range(48, 58))]
    picked = [random.choice(chars) for x in range(num)]
    return ''.join(picked)


def which(name):
    return sub.getoutput('which %s' % name)


def get_size(path):
    return os.path.getsize('/bin/bash')


def make_time():
    return timezone.now() - timedelta(days=random.randint(1,10))


def make_path(time, digest):
    return os.path.join(time.strftime('%Y%m%d'), digest)


users = [
    {'name': 'alice', 'password': 'abcd/1234'},
    {'name': 'bob', 'password': 'abcd/1234'},
    {'name': 'charlie', 'password': 'abcd/1234'},
]

files = ['rm', 'cp', 'ls', 'mv', 'cat', 'cut', 'head',
         'tail', 'grep', 'awk', 'sed', 'sort']

media_dir = os.path.join(basedir, 'media')

# 创建数据库记录：用户，文件，文件对象，目录，共享
for user in users:
    print('creating user %s' % user['name'])
    u = User(username=user['name'])
    u.set_password(user['password'])
    u.save()

    # 创建目录home/data/video
    print('creating Directories')
    home = Directory.objects.create(name=user['name'], owner=u)
    data_dir = Directory.objects.create(name='data', owner=u, parent=home)
    video_dir = Directory.objects.create(name='video', owner=u, parent=data_dir)
    home.add(data_dir)
    data_dir.add(video_dir)

    # 共享data目录
    Share.objects.create(target=data_dir.pk, kind='directory', code=gen_code(),
                         expire=timezone.now()+timedelta(days=12))

    file_names = files[:4]
    files = files[4:]
    for i, name in enumerate(file_names):
        abspath = which(name)
        size = get_size(abspath)
        time = make_time()
        sha1 = digest(abspath)
        store_path = make_path(time, sha1)

        print('creating FileObject record for %s' % name)
        fo = FileObject.objects.create(
                size=size, received=size, time=time, digest=sha1,
                path=store_path, finished=True, links=1)

        print('creating File record for %s' % name)
        file = File.objects.create(name=name, owner=u, fo=fo)

        print('creating Share record for %s' % name)
        if i == 1:  # 创建匿名共享
            Share.objects.create(target=file.pk, kind='file',
                                 expire=timezone.now()+timedelta(days=10+i))
        elif i == 2:    # 提取码共享
            Share.objects.create(target=file.pk, kind='file', code=gen_code(),
                                 expire=timezone.now()+timedelta(days=10+i))

        # 把第一个文件放到video中，其它的放到home中
        if i == 0:
            video_dir.add(file)
        else:
            home.add(file)

        print('copying file %s' % abspath)
        dst = os.path.join(media_dir, store_path)
        dst_dir = os.path.dirname(dst)
        os.makedirs(dst_dir, mode=0o755, exist_ok=True)
        os.system('cp -v %s %s' % (abspath, dst))
