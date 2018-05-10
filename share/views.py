from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm

from .forms import LoginForm
from .models import DirectoryFile, RegularFile, File


@login_required
def index(request):
    """
    用户主页，显示用户资源的相关链接：文件，共享。
    """
    user = request.user
    home = get_object_or_404(File, name=user.username,
                             owner=user, is_regular=False)
    dirs, files, parents = get_items(home)
    context = {'dirs': dirs, 'files': files, 'parents': parents}
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
    context = {'dirs': dirs, 'files': files, 'parents': parents}
    return render(request, 'share/list_dir.html', context=context)


@login_required
def list_shares(request):
    """查看所有的共享"""
    return render(request, 'share/list_shares.html')


@login_required
def edit(request, pk):
    """修改文件"""
    return render(request, 'share/edit.html')


@login_required
def share(request, pk):
    """共享文件"""
    return render(request, 'share/share.html')


@login_required
def delete(request, pk):
    """删除文件"""
    return render(request, 'share/delete.html')


def login(request):
    next_url = request.GET.get('next', reverse('share:index'))
    if request.user.is_authenticated():
        return HttpResponseRedirect(next_url)

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = auth.authenticate(username=username, password=password)
            if user is not None and user.is_active:
                auth.login(request, user)
                return HttpResponseRedirect(next_url)
    else:
        form = LoginForm()
    return render(request, 'share/login.html', context={'form': form})


def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(reverse('share:index'))


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = auth.authenticate(username=username, password=raw_password)
            auth.login(request, user)
            return HttpResponseRedirect(reverse('share:index'))
    else:
        form = UserCreationForm()
    return render(request, 'share/signup.html', {'form': form})
