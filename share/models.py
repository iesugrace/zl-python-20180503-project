import os
import re

import magic
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


class File(models.Model):
    # 文件名字
    name = models.CharField(max_length=256)
    # 上传者/拥有者
    owner = models.ForeignKey(User)
    # 后面的文件对象
    fo = models.ForeignKey('FileObject')


class Directory(models.Model):
    # 目录名字
    name = models.CharField(max_length=256)
    # 上传者/拥有者
    owner = models.ForeignKey(User)
    # 所属的父目录
    parent = models.ForeignKey('Directory', null=True)
    # 下一级节点
    # 下一级目录/文件的表示法：
    # '123:34567:15379'
    subdirs = models.CharField(max_length=204800, default='')
    files = models.CharField(max_length=204800, default='')

    def add(self, other):
        if isinstance(other, Directory):
            name = 'subdirs'
        elif isinstance(other, File):
            name = 'files'
        else:
            raise ValueError('must be either Directory or File')
        text = ':%s' % other.pk
        value = getattr(self, name)
        if text not in value:
            setattr(self, name, value + text)
            self.save()

    def remove(self, other):
        if isinstance(other, Directory):
            name = 'subdirs'
        elif isinstance(other, File):
            name = 'files'
        else:
            raise ValueError('must be either Directory or File')
        text = ':%s' % other.pk
        value = getattr(self, name)
        if text in value:
            setattr(self, name, value.replace(text, ''))
            self.save()


class FileObject(models.Model):
    # 文件尺寸
    size = models.IntegerField()
    # 已经接收的数据量（用于断点续传）
    received = models.IntegerField()
    # 开始上传时间
    time = models.DateTimeField()
    # 文件的校验和 (sha1)
    digest = models.CharField(max_length=40)
    # 文件在服务器上的文件系统中的相对路径
    path = models.CharField(max_length=4096)
    # 文件上传是否完成
    finished = models.BooleanField(default=False)
    # 文件的链接数（类似文件系统的硬链接）
    links = models.IntegerField(default=1)

    def mimetype(self):
        """
        检测文件类型，检测以下类型，返回相应的字符串：
            image: image/*
            audio: audio/*
            video: video/*
            text: text/*
            pdf: application/pdf
            gzip: application/gzip
            bzip2: application/x-bzip2
            zip: application/zip
            tar: application/x-tar
            octet: all others
        """
        maps = [('image', r'^image/.*'),
                ('audio', r'^audio/.*'),
                ('video', r'^video/.*'),
                ('text', r'^text/.*'),
                ('pdf', r'^application/pdf$'),
                ('gzip', r'^application/gzip$'),
                ('bzip2', r'^application/x-bzip2$'),
                ('zip', r'^application/zip$'),
                ('tar', r'^application/x-tar$')]
        mime = magic.Magic(mime=True)
        path = os.path.join(settings.MEDIA_ROOT, self.path)
        type_text = mime.from_file(path)
        m = [name for name, pat in maps if re.match(pat, type_text)]
        if m:
            return m[0]
        else:
            return 'octet'


class Share(models.Model):
    target = models.IntegerField()
    kind = models.CharField(max_length=10)  # directory/file
    # 提取码，当为None时，表示是匿名下载
    code = models.CharField(max_length=8, null=True)
    # 该共享的失效时间
    expire = models.DateTimeField()
