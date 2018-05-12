import os
from io import BytesIO

from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.http import (HttpResponseRedirect, StreamingHttpResponse,
                         HttpResponseBadRequest, HttpResponse)
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import LoginForm, RenameForm, ShareForm
from .models import DirectoryFile, RegularFile, File, Share
from .libs import make_abspath, gen_code
from .views_libs import (create_directory, get_session_id,
                         get_session_data, set_session_data,
                         share_approved, permission_ok, make_image, gentext)


@login_required
def index(request):
    """
    用户主页，显示用户资源的相关链接：文件，共享。
    """
    user = request.user
    home = get_object_or_404(File, name=user.username,
                             owner=user, is_regular=False)
    dirs, files, parents = get_items(home)
    context = {'dirs': dirs, 'files': files,
               'parents': parents, 'title': 'File sharing'}
    return render(request, 'share/list_dir.html', context=context)


def get_items(dir):
    # 列出目錄下的內容，就是子目錄和文件，同時返回所有父目錄
    dirs = records_from_ids(dir.object.subdirs)
    files = records_from_ids(dir.object.files)
    parents = [dir]
    while dir.parent:
        parents.append(dir.parent)
        dir = dir.parent
    parents = parents[::-1]
    return dirs, files, parents


def records_from_ids(ids):
    # ids format: :id1:id2:id3
    # 每一个id的前面都有一个冒号
    if not ids:
        return []
    ids = [int(id) for id in ids.strip(':').split(':')]
    return File.objects.filter(pk__in=ids).order_by('name')


@login_required
def list_dir(request, dir=None):
    """查看目录下的文件"""
    user = request.user
    dir = get_object_or_404(File, pk=dir, owner=user)
    dirs, files, parents = get_items(dir)
    context = {'dirs': dirs, 'files': files,
               'parents': parents, 'title': 'File list'}
    return render(request, 'share/list_dir.html', context=context)


@require_POST
def post_code(request, pk):
    file = get_object_or_404(File, pk=pk)
    if request.method == 'POST':
        code = request.POST['code']
        for share, _ in file.shares():
            if share.code == code:
                shares = get_session_data(request, 'shares') or []
                shares.append(share.pk)
                set_session_data(request, 'shares', shares)
                url = reverse('share:detail', args=(pk,))
                return HttpResponseRedirect(url)
        return HttpResponse('invalid code')


def detail(request, pk):
    """查看文件详情"""
    file = get_object_or_404(File, pk=pk)
    context = {'file': file}
    if request.user.is_authenticated():
        # 登录用户，显示所有信息
        template_file = "share/detail.html"
        context['title'] = 'File detail'
    elif file.shared_to_all():
        # 匿名共享文件，显示基本信息及下载链接
        template_file = "share/detail_share_to_all.html"
        context['title'] = 'Shared file info'
    elif file.shared_with_code():
        # 分享码共享文件，显示基本信息，
        # 如果已经提交了有效的分享码，就显示链接，
        # 否则，就显示提交分享码的表单
        template_file = "share/detail_share_with_code.html"
        context['title'] = 'Shared file info'
        context['approved'] = share_approved(request, file)
    else:
        url = reverse('share:login') + '?next=' + request.META['PATH_INFO']
        return HttpResponseRedirect(url)
    return render(request, template_file, context=context)


def view(request, pk):
    """查看文件内容"""
    file = get_object_or_404(File, pk=pk)

    if not permission_ok(request, file):
        url = reverse('share:login') + '?next=' + request.META['PATH_INFO']
        return HttpResponseRedirect(url)

    if file.is_viewable():
        abspath = make_abspath(file.object.path)
        buf = open(abspath, 'rb')
        response = StreamingHttpResponse(buf)
        response['Content-Type'] = file.raw_mimetype()
        return response
    else:
        context = {'file': file, 'title': 'View file content'}
        return render(request, 'share/view.html', context=context)


def download(request, pk):
    """下载文件"""
    file = get_object_or_404(File, pk=pk)

    if not permission_ok(request, file):
        url = reverse('share:login') + '?next=' + request.META['PATH_INFO']
        return HttpResponseRedirect(url)

    if not file.is_regular:
        return HttpResponseBadRequest("Only a regular file can be downloaded.")

    abspath = make_abspath(file.object.path)
    buf = open(abspath, 'rb')
    response = StreamingHttpResponse(buf)
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="%s"' % file.name
    return response


@login_required
def list_shares(request):
    """查看所有的共享"""
    user = request.user
    now = timezone.now()
    shares = Share.objects.filter(target__owner=user)
    shares = [x for x in shares if not x.is_expired()]
    shares = sorted(shares, key=(lambda x: x.target.is_regular))
    context = {'shares': shares, 'title': 'Share list'}
    return render(request, 'share/list_shares.html', context=context)


@login_required
def create_share(request, pk):
    """共享文件"""
    file = get_object_or_404(File, pk=pk)
    if request.method == 'POST':
        form = ShareForm(request.POST)
        form.errors.clear()
        try:
            if 'anonymous' in request.POST:
                code = None
            else:
                code = form['code'].field.clean(request.POST['code'])
        except ValidationError as e:
            form.add_error('code', e)
        try:
            if 'never_expire' in request.POST:
                expire = None
            else:
                expire = form['expire'].field.clean(request.POST['expire'])
        except ValidationError as e:
            form.add_error('expire', e)

        if not form.errors:
            Share.objects.create(target=file, code=code, expire=expire)
            url = reverse('share:detail', args=(pk,))
            return HttpResponseRedirect(url)

        form['code'].field.disabled = 'anonymous' in request.POST
        form['expire'].field.disabled = 'never_expire' in request.POST
    else:
        form = ShareForm(initial={'code': gen_code()})

    notice = ('note: if you share a directory, all files under '
              'the directory tree will be shared.')
    context={'file_name': file.name, 'form': form,
             'notice': notice, 'title': 'Create share'}
    return render(request, 'share/create_share.html', context=context)


@login_required
def edit_share(request, pk):
    """修改共享"""
    share = get_object_or_404(Share, pk=pk)
    if request.method == 'POST':
        form = ShareForm(request.POST)
        form.errors.clear()
        try:
            if 'anonymous' in request.POST:
                code = None
            else:
                code = form['code'].field.clean(request.POST['code'])
        except ValidationError as e:
            form.add_error('code', e)
        try:
            if 'never_expire' in request.POST:
                expire = None
            else:
                expire = form['expire'].field.clean(request.POST['expire'])
        except ValidationError as e:
            form.add_error('expire', e)

        if not form.errors:
            share.code = code
            share.expire = expire
            share.save()
            next_url = request.POST['next']
            return HttpResponseRedirect(next_url)

        form['code'].field.disabled = 'anonymous' in request.POST
        form['expire'].field.disabled = 'never_expire' in request.POST
    else:
        init_data = {'code': share.code, 'expire': share.expire,
                     'anonymous': share.code is None,
                     'never_expire': share.expire is None}
        form = ShareForm(initial=init_data)
        form['code'].field.disabled = init_data['anonymous']
        form['expire'].field.disabled = init_data['never_expire']

    next_url = request.META['HTTP_REFERER']
    context={'file_name': share.target.name, 'form': form,
             'next': next_url, 'title': 'Edit share'}
    return render(request, 'share/create_share.html', context=context)


@login_required
def delete_share(request, pk):
    """删除共享"""
    share = get_object_or_404(Share, pk=pk)
    if request.method == 'POST':
        if request.POST.get('submit', '') == 'Delete':
            share.delete()
            return HttpResponseRedirect(request.POST['next'])
    next_url = request.META['HTTP_REFERER']
    context={'file_name': share.target.name, 'next': next_url,
             'title': 'Delete share'}
    return render(request, 'share/delete_share.html', context=context)


@login_required
def edit(request, pk):
    """修改文件"""
    file = get_object_or_404(File, pk=pk)
    if request.method == 'POST':
        form = RenameForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            file.name = name
            file.save()
            return HttpResponseRedirect(reverse('share:detail', args=(pk,)))
    else:
        form = RenameForm({'name': file.name})
    context = {'form': form, 'title': 'Edit file'}
    return render(request, 'share/edit.html', context=context)


@login_required
def delete(request, pk):
    """删除文件"""
    file = get_object_or_404(File, pk=pk)
    if not file.is_regular:
        return HttpResponseBadRequest("Only a regular file can be deleted.")

    if request.method == 'POST':
        if request.POST.get('submit', '') == 'Delete':
            file.unlink()
            next_url = request.POST['next']
            return HttpResponseRedirect(next_url)
    next_url = request.META['HTTP_REFERER']
    context={'file_name': file.name, 'next': next_url, 'title': 'Delete file'}
    return render(request, 'share/delete.html', context=context)


def login(request):
    next_url = request.GET.get('next', reverse('share:index'))
    if request.user.is_authenticated():
        return HttpResponseRedirect(next_url)

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            # 先对比验证码，在校验用户名字和密码
            posted_captcha = form.cleaned_data['captcha']
            saved_captcha = get_session_data(request, 'captcha')
            if (saved_captcha is not None
                    and posted_captcha.lower() == saved_captcha):
                username = form.cleaned_data['username']
                password = form.cleaned_data['password']
                user = auth.authenticate(username=username, password=password)
                if user is not None and user.is_active:
                    auth.login(request, user)
                    return HttpResponseRedirect(next_url)
            else:
                form.add_error('captcha','验证码不匹配')
    else:
        form = LoginForm()
    context = {'form': form, 'title': 'Login', 'login_page': True}
    return render(request, 'share/login.html', context=context)


def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(reverse('share:index'))


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            home = create_directory(name=user.username, owner=user)
            username = user.username
            raw_password = form.cleaned_data.get('password1')
            user = auth.authenticate(username=username, password=raw_password)
            auth.login(request, user)
            return HttpResponseRedirect(reverse('share:index'))
    else:
        form = UserCreationForm()
    context = {'form': form, 'title': 'Sign up'}
    return render(request, 'share/signup.html', context=context)


def gen_captcha(request):
    """ 生成验证码图片 """
    text = gentext(4)
    # 把验证码内容存到session中
    set_session_data(request, 'captcha', text.lower())
    im = make_image(text)
    imgout = BytesIO()
    im.save(imgout, format='png')
    img_bytes = imgout.getvalue()
    return HttpResponse(img_bytes, content_type='image/png')
