import os
import re

import magic
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


class File(models.Model):
    # 文件名字
    name = models.CharField(max_length=256)
    # 拥有者
    owner = models.ForeignKey(User)
    # 所属的父目录
    parent = models.ForeignKey('File', null=True)

    # 后面的文件对象，通过property的方法根据文件类型，
    # 指向文件对象或目录对象
    object_pk = models.IntegerField()
    is_regular = models.BooleanField(default=True)  # directory/file

    @property
    def object(self):
        if self.is_regular:
            return RegularFile.objects.get(pk=self.object_pk)
        else:
            return DirectoryFile.objects.get(pk=self.object_pk)

    def add(self, other):
        """往目录中添加子目录或常规文件"""
        fo = self.object
        assert isinstance(fo, DirectoryFile), "only valid for directories"

        if other.is_regular:
            name = 'files'
        else:
            name = 'subdirs'
        text = ':%s' % other.pk
        value = getattr(fo, name)
        if text not in value:
            setattr(fo, name, value + text)
            fo.size = len(fo.subdirs) + len(fo.files)
            fo.save()
            other.parent = self
            other.save()

    def remove(self, other):
        fo = self.object
        assert isinstance(fo, DirectoryFile), "only valid for directories"

        if other.is_regular:
            name = 'files'
        else:
            name = 'subdirs'
        text = ':%s' % other.pk
        value = getattr(fo, name)
        if text in value:
            setattr(fo, name, value.replace(text, ''))
            fo.size = len(fo.subdirs) + len(fo.files)
            fo.save()

    def mimetype(self):
        if not self.is_regular:
            return "dir"

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
        path = os.path.join(settings.MEDIA_ROOT, self.object.path)
        type_text = mime.from_file(path)
        m = [name for name, pat in maps if re.match(pat, type_text)]
        if m:
            return m[0]
        else:
            return 'octet'


class DirectoryFile(models.Model):
    # 下一级节点，子目录/文件的表示法：':123:34567:15379'
    subdirs = models.CharField(max_length=204800, default='')
    files = models.CharField(max_length=204800, default='')
    # 创建时间
    time = models.DateTimeField(auto_now_add=True)
    # 目录的大小: subdirs和files的总长度
    size = models.IntegerField(default=0)


class RegularFile(models.Model):
    # 文件尺寸
    size = models.IntegerField()
    # 已经接收的数据量（用于断点续传）
    received = models.IntegerField()
    # 开始上传时间
    time = models.DateTimeField(auto_now_add=True)
    # 文件的校验和 (sha1)
    digest = models.CharField(max_length=40)
    # 文件在服务器上的文件系统中的相对路径
    path = models.CharField(max_length=4096)
    # 文件上传是否完成
    finished = models.BooleanField(default=False)
    # 文件的链接数（类似文件系统的硬链接）
    links = models.IntegerField(default=1)


class Share(models.Model):
    target = models.ForeignKey('File')
    # 提取码，当为None时，表示是匿名下载
    code = models.CharField(max_length=8, null=True)
    # 该共享的失效时间
    expire = models.DateTimeField()
