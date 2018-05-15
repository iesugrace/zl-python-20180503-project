"""
这是用来访问文件共享服务的命令行客户端，可以独立运行，不依赖文件共享服务程序的代码。

功能：

1. 获取登录用户的文件列表 (list dir)
2. 获取文件的详情，适用于登录用户/匿名访问/分享码访问 (detail)
3. 下载单个文件，适用于登录用户/匿名访问/分享码访问 (download)
4. 下载文件时支持断点续传
5. 上传单个文件，适用于登录用户 (upload)
6. 上传文件时支持断点续传
7. 上传时不重复上传服务器上已有的文件，通过计算校验和来实现 (秒传)
8. 上传时，如果已经存在可用的文件校验和，则不重复计算校验和
9. 支持下载多个文件或者目录
10. 支持上传多个文件或者目录
11. 支持session和登入登出

"""

import os
import sys

import json
import requests

basedir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, basedir)
from thinap import ArgParser


def help():
    text = """available commands: login logout ls mkdir cp fetch

路径表示法：

    1. 远程路径的开始标记是一个冒号，冒号之后是路径，
        路径以斜杠开始就是绝对路径，否则就是相对于家目录的路径。
    2. 本地路径的表示法与Linux的文件系统表示法相同。

login/logout 命令用于登入和登出，登入成功后服务器的信息会被记录下来，供后续命令使用。

ls 命令用于列出远程文件/目录的信息

    -l 参数显示详情，不加-l 则只显示名字
    -d 参数只会影响目录的显示，有此参数则列出目录本身，无则列出目录内容

mkdir 命令用于创建远程目录

    -p 参数用于创建不存在的父目录，目标存在时也不出错
    -v 参数用于显示过程

cp 命令用于上传下载，远程路径写在前面是下载，写在后面是上传

    -o 参数使得不上传服务器上已有的文件 （秒传）
    -d 参数用于上传下载目录
    -v 参数用于显示过程

fetch 命令用于下载分享的文件或目录。

    -O 参数用于指定下载的文件（非目录）的本地存放路径
    -P 参数用于指定路径的前缀（不影响-O 参数）

    如果需要提供分享码，则分享码写在url中，形式如下（假设分享码是abcd）：

    http://abcd@hostname/path/to/target


范例：

1. login/logout

    login -u alice -p password      登入
    logout                          登出

2. ls 命令

    ls                  列出家目录下所有的子目录和文件的名字
    ls data             列出家目录下的data中所有子目录和文件的名字
    ls -ld videos       列出家目录下的videos 目录本身的详细信息
    ls -l videos        列出家目录下的videos 目录中所有子目录和文件的详情

3. 在远程家目录下创建目录 multimedia/anv，如果multimedia 不存在，就一并创建

    mkdir -p multimedia/anv

4. 上传本地文件 genesis.mp3 到远程 multimedia/anv/ 目录下面

    cp genesis.mp3 :multimedia/anv/

5. 上传多个本地文件到远程

    cp genesis.mp3 goodday.mp4 :multimedia/anv/

6. 上传文件和/或目录到远程的家目录中

    cp -r multimedia calculus.pdf data.tar :
    cp -r multimedia :

7. 下载远程文件，存放到本地的当前目录中（留意命令后面的点）

    cp :calculus.pdf .

8. 下载远程文件和目录，存放到本地的fetched目录中

    cp -r :multimedia :calculus.pdf fetched

9. fetch 命令

    fetch http://host/download/13/                  下载到当前目录
    fetch -O /tmp/a.mp3 http://host/download/13/    指定保存的路径
    fetch -P downloaded http://host/download/13/    指定文件存储的目录
"""
    print(text, end='')


def save_session(data):
    path = '/tmp/.client_of_share_session'
    with open(path, 'w') as f:
        f.write(json.dumps(data))


def load_session():
    path = '/tmp/.client_of_share_session'
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.loads(f.read())


def login(args, api):
    """登入，并保存cookie"""
    request = {'username': {'flag': '-u', 'arg': 1},
               'password': {'flag': '-p', 'arg': 1}}
    p = ArgParser()
    params = p.parse_args(args, request)
    mapping = params[0]
    username = mapping.get('username')
    password = mapping.get('password')
    assert username and password, 'user name and password are required'

    r = requests.post(api, data={'username': username, 'password': password})
    if r.ok:
        sid = r.cookies.get('sessionid')
        if sid:
            save_session({'sessionid': sid})
            return True
    return False


def logout(args, api):
    """登出，并清除cookie"""
    path = '/tmp/.client_of_share_session'
    r = requests.get(api)
    save_session({})
    return True


def send_request(api, data):
    cookies = load_session()
    r = requests.post(api, data=data, cookies=cookies)
    if r.ok:
        return r.json()
    else:
        print('request failed (code %s)' % r.status_code)


def ls(args, api):
    request = {'long': {'flag': '-l'},
               'directory': {'flag': '-d'}}
    p = ArgParser()
    params = p.parse_args(args, request)
    mapping = params[0]
    long = mapping.get('long', False)
    directory = mapping.get('directory', False)
    names = params[1] or []

    data = dict(long=long, directory=directory, names=names)
    res = send_request(api, data)
    if not res:
        return False

    # 输出文件的信息
    if long:
        files = []
        for block in res['output']:
            files.extend(list(block.values())[0])
        format_output(files)
    else:
        for block in res['output']:
            for key, files in block.items():
                if not files:
                    continue
                for file in files:
                    print(file)
    # 输出错误信息
    if not res['status']:
        for e in res['errors']:
            print('error:', e)


def format_output(files):
    # 字段：regular, owner, size, time, name
    sizes = [len(str(f['size'])) for f in files]
    size_len = max(sizes)
    for f in files:
        type = '-' if f['regular'] else 'd'
        fmt = '%%s %%s %%%ds %%s %%s' % size_len
        line = fmt % (type, f['owner'], f['size'], f['time'], f['name'])
        print(line)


def mkdir(args, api):
    request = {'parents': {'flag': '-p'},
               'verbose': {'flag': '-v'}}
    p = ArgParser()
    params = p.parse_args(args, request)
    mapping = params[0]
    parents = mapping.get('parents', False)
    verbose = mapping.get('verbose', False)
    names = params[1] or []

    data = dict(parents=parents, verbose=verbose, names=names)
    res = send_request(api, data)
    if not res:
        return False

    # -v, 输出详细信息
    if verbose:
        for name in res['output']:
            print('created directory: %s' % name)

    # 输出错误信息
    if not res['status']:
        for e in res['errors']:
            print('error:', e)


def rmdir(args, api):
    request = {'parents': {'flag': '-p'},
               'verbose': {'flag': '-v'}}
    p = ArgParser()
    params = p.parse_args(args, request)
    mapping = params[0]
    parents = mapping.get('parents', False)
    verbose = mapping.get('verbose', False)
    names = params[1] or []

    data = dict(parents=parents, verbose=verbose, names=names)
    res = send_request(api, data)
    if not res:
        return False

    # -v, 输出详细信息
    if verbose:
        for name in res['output']:
            print('removing directory: %s' % name)

    # 输出错误信息
    if not res['status']:
        for e in res['errors']:
            print('error:', e)


def cp(args, api):
    ...


def fetch(args, api):
    ...


if __name__ == '__main__':
    if '--help' in sys.argv:
        help()
        exit(0)
    elif len(sys.argv) < 2:
        fmt = 'usage: %(name)s <command> [options] [arguments]'
        fmt += '\nfor more info, run %(name)s --help'
        print(fmt % {'name': os.path.basename(sys.argv[0])})
        exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        'login': {'name': login, 'api': 'http://127.0.0.1:8000/share/api/login/'},
        'logout': {'name': logout, 'api': 'http://127.0.0.1:8000/share/api/logout/'},
        'ls': {'name': ls, 'api': 'http://127.0.0.1:8000/share/api/ls/'},
        'mkdir': {'name': mkdir, 'api': 'http://127.0.0.1:8000/share/api/mkdir/'},
        'rmdir': {'name': rmdir, 'api': 'http://127.0.0.1:8000/share/api/rmdir/'},
        'cp': {'name': cp, 'api': 'http://127.0.0.1:8000/share/api/cp/'},
        'fetch': {'name': fetch, 'api': 'http://127.0.0.1:8000/share/api/fetch/'},
    }

    command = commands.get(cmd, {}).get('name')

    # 无效的命令
    if not command:
        print('invalid command %s' % cmd)
        exit(1)

    # 执行命令
    api = commands.get(cmd, {}).get('api')
    try:
        status = command(args, api)
    except AssertionError as e:
        print(e)
        exit(1)
    exit(0 if status else 1)
