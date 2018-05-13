"""
填充应用程序运行所需的数据

1. 填充数据库记录
2. 复制文件到指定的目录

目录结构抽象图

/
├── alice
│   ├── multimedia      <-- 提取码共享整个目录
│   │   ├── anv
│   │   │   ├── genesis.mp3
│   │   │   └── goodday.mp4
│   │   └── earth.png
│   ├── calculus.pdf    <-- 提取码共享
│   ├── data.tar
│   ├── data.tar.bz2
│   ├── data.tar.gz
│   ├── data.zip
│   ├── info.bin
│   └── license.txt     <-- 匿名共享
├── bob
│   ├── ...
│   ...
│   ...
└── charlie
    ├── ...
    ...
    ...

"""

import os
from os.path import abspath, dirname
import sys
import hashlib
import random
from datetime import timedelta

import django
from django.utils import timezone

basedir = dirname(dirname(abspath(__file__)))
os.chdir(basedir)
sys.path.insert(0, '')
os.environ['DJANGO_SETTINGS_MODULE'] = 'pro1.settings'
django.setup()

from django.contrib.auth.models import User
from share.models import RegularFile, DirectoryFile, File, Share


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


def get_abspath(name):
    dir = dirname(abspath(__file__))
    path = os.path.join(dir, 'test_files', name)
    return path


def get_size(path):
    return os.path.getsize(path)


def make_time():
    return timezone.now() - timedelta(days=random.randint(1,10))


def make_path(time, digest):
    return os.path.join(time.strftime('%Y%m%d'), digest)


def create_directory(name, owner):
    fo = DirectoryFile.objects.create()
    dir = File.objects.create(name=name, owner=owner, is_regular=False)
    dir.link(fo)
    return dir


# 创建数据库记录：用户，文件，文件对象，目录，共享
def work():
    for user in users:
        print('creating user %s' % user['name'])
        u = User(username=user['name'])
        u.set_password(user['password'])
        u.save()

        # 创建目录home/multimedia/anv
        print('creating Directories')
        home = create_directory(user['name'], u)
        multimedia_dir = create_directory('multimedia', u)
        anv_dir = create_directory('anv', u)
        home.add(multimedia_dir)
        multimedia_dir.add(anv_dir)

        # 共享multimedia目录
        Share.objects.create(target=multimedia_dir, code=gen_code(),
                             expire=timezone.now()+timedelta(days=12))

        for i, name in enumerate(files):
            abspath = get_abspath(name)
            size = get_size(abspath)
            time = make_time()
            sha1 = digest(path=abspath)
            store_path = make_path(time, sha1)

            print('creating RegularFile record for %s' % name)
            fo = RegularFile.objects.create(
                        size=size, received=size, time=time, digest=sha1,
                        path=store_path, finished=True)

            print('creating File record for %s' % name)
            file = File.objects.create(name=name, owner=u)
            file.link(fo)
            if name in ['genesis.mp3', 'goodday.mp4']:
                anv_dir.add(file)
            elif name == 'earth.png':
                multimedia_dir.add(file)
            else:
                home.add(file)

            print('creating Share record for %s' % name)
            if name == 'license.txt':  # 创建匿名共享
                Share.objects.create(target=file,
                                     expire=timezone.now()+timedelta(days=10+i))
            elif name == 'calculus.pdf':    # 提取码共享
                Share.objects.create(target=file, code=gen_code(),
                                     expire=timezone.now()+timedelta(days=10+i))

            print('copying file %s' % abspath)
            dst = os.path.join(media_dir, store_path)
            dst_dir = os.path.dirname(dst)
            os.makedirs(dst_dir, mode=0o755, exist_ok=True)
            os.system('cp -v %s %s' % (abspath, dst))


users = [
    {'name': 'alice', 'password': 'abcd/1234'},
    {'name': 'bob', 'password': 'abcd/1234'},
    {'name': 'charlie', 'password': 'abcd/1234'},
]

files = ['calculus.pdf', 'data.tar', 'data.tar.bz2', 'data.tar.gz', 'data.zip',
         'earth.png', 'genesis.mp3', 'goodday.mp4', 'info.bin', 'license.txt']

media_dir = os.path.join(basedir, 'media')


if __name__ == '__main__':
    work()
