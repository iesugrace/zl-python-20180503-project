# 设置Django的运行环境
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

from share.models import User, File, FileObject, Share

users = [
    {'name': 'alice', 'password': 'a9993e364706816aba3e25717850c26c9cd0d89d'},
    {'name': 'bob', 'password': 'a9993e364706816aba3e25717850c26c9cd0d89d'},
    {'name': 'charlie', 'password': 'a9993e364706816aba3e25717850c26c9cd0d89d'},
]

files = [
    {'name': 'bash',
     'owner': 'alice',
     'size': 1021112,
     'received': 1021112,
     'time': timezone.now() - timedelta(days=1),
     'digest': 'f8a66b192aa0cf8a2fea773f6bc78ef9b96275e0',
     'path':  (timezone.now() - timedelta(days=1)).strftime('%Y%m%d') + '/f8a66b192aa0cf8a2fea773f6bc78ef9b96275e0',
     'finished': True,
     'links': 1},
    {'name': 'cp',
     'owner': 'alice',
     'size': 130304,
     'received': 130304,
     'time': timezone.now() - timedelta(days=2),
     'digest': '781a6e4fe0cb8167ce423fc476240bded698d676',
     'path':  (timezone.now() - timedelta(days=2)).strftime('%Y%m%d') + '/781a6e4fe0cb8167ce423fc476240bded698d676',
     'finished': True,
     'links': 1},
    {'name': 'mv',
     'owner': 'alice',
     'size': 122088,
     'received': 122088,
     'time': timezone.now() - timedelta(days=3),
     'digest': 'a570e581d7e1d5308e88154967c3bde3593da50d',
     'path':  (timezone.now() - timedelta(days=3)).strftime('%Y%m%d') + '/a570e581d7e1d5308e88154967c3bde3593da50d',
     'finished': True,
     'links': 1},

    {'name': 'ls',
     'owner': 'bob',
     'size': 110080,
     'received': 110080,
     'time': timezone.now() - timedelta(days=10),
     'digest': '5848386f77b4c60319c68b69c4594e29959381a2',
     'path':  (timezone.now() - timedelta(days=10)).strftime('%Y%m%d') + '/5848386f77b4c60319c68b69c4594e29959381a2',
     'finished': True,
     'links': 1},
    {'name': 'grep',
     'owner': 'bob',
     'size': 191952,
     'received': 191952,
     'time': timezone.now() - timedelta(days=11),
     'digest': 'd39d8732dd68c6167aba7ff8f126db377b509c73',
     'path':  (timezone.now() - timedelta(days=11)).strftime('%Y%m%d') + '/d39d8732dd68c6167aba7ff8f126db377b509c73',
     'finished': True,
     'links': 1},
    {'name': 'sed',
     'owner': 'bob',
     'size': 73352,
     'received': 73352,
     'time': timezone.now() - timedelta(days=12),
     'digest': '1892c906fc5208a501f934d61fbd2e5ad9ab2fe0',
     'path':  (timezone.now() - timedelta(days=12)).strftime('%Y%m%d') + '/1892c906fc5208a501f934d61fbd2e5ad9ab2fe0',
     'finished': True,
     'links': 1},

    {'name': 'awk',
     'owner': 'charlie',
     'size': 441512,
     'received': 441512,
     'time': timezone.now() - timedelta(days=13),
     'digest': 'c53d7c1c580979561333c345210276e51b4d517a',
     'path':  (timezone.now() - timedelta(days=13)).strftime('%Y%m%d') + '/c53d7c1c580979561333c345210276e51b4d517a',
     'finished': True,
     'links': 1},
    {'name': 'cut',
     'owner': 'charlie',
     'size': 43680,
     'received': 43680,
     'time': timezone.now() - timedelta(days=14),
     'digest': '21c0a42179bf4a6c2e58ddf1a1bf58c668830a50',
     'path':  (timezone.now() - timedelta(days=14)).strftime('%Y%m%d') + '/21c0a42179bf4a6c2e58ddf1a1bf58c668830a50',
     'finished': True,
     'links': 1},
    {'name': 'sort',
     'owner': 'charlie',
     'size': 101760,
     'received': 101760,
     'time': timezone.now() - timedelta(days=15),
     'digest': '76fcb8813682cc8697af1e5c6ddd5fb1dfdea23c',
     'path':  (timezone.now() - timedelta(days=15)).strftime('%Y%m%d') + '/76fcb8813682cc8697af1e5c6ddd5fb1dfdea23c',
     'finished': True,
     'links': 1},
]

media_dir = os.path.join(basedir, 'media')

def digest(data):
    if isinstance(data, str):
        data = data.encode()
    hash = hashlib.sha1(data)
    return hash.hexdigest()


def gen_code():
    num = 8
    chars = [chr(x) for x in list(range(97, 123))
                + list(range(65, 91)) + list(range(48, 58))]
    picked = [random.choice(chars) for x in range(num)]
    return ''.join(picked)


# 创建数据库记录：用户，文件，文件对象，共享
for user in users:
    print('creating user %s' % user['name'])
    u = User.objects.create(name=user['name'], password=digest(user['password']))
    files_info = [x for x in files if x['owner'] == u.name]
    for i, info in enumerate(files_info):
        name = info['name']
        print('creating FileObject record for %s' % name)
        fo = FileObject.objects.create(
            size=info['size'],
            received=info['received'],
            time=info['time'],
            digest=info['digest'],
            path=info['path'],
            finished=info['finished'],
            links=info['links']
        )

        print('creating File record for %s' % name)
        file = File.objects.create(name=name, owner=u, fo=fo)

        print('creating Share record for %s' % name)
        if i == 0:  # 创建匿名共享
            Share.objects.create(
                    target=file.pk,
                    kind='file',
                    expire=timezone.now()+timedelta(days=10+i)
            )
        elif i == 1:    # 提取码共享
            Share.objects.create(
                    target=file.pk,
                    kind='file',
                    code=gen_code(),
                    expire=timezone.now()+timedelta(days=10+i)
            )

        print('copying file %s' % name)
        src = sub.getoutput('which %s' % name)
        dst = os.path.join(media_dir, info['path'])
        dst_dir = os.path.dirname(dst)
        os.makedirs(dst_dir, mode=0o755, exist_ok=True)
        os.system('cp -v %s %s' % (src, dst))
