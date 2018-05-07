from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm

from .forms import LoginForm


@login_required
def index(request):
    """
    用户主页，显示用户资源的相关链接：文件，共享。
    """
    return render(request, 'share/index.html')


@login_required
def list_files(request, dir=None):
    """查看目录下的文件"""
    return render(request, 'share/list_files.html')


@login_required
def list_shares(request):
    """查看所有的共享"""
    return render(request, 'share/list_shares.html')


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
