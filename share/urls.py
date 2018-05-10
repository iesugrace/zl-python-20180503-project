from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^signup/$', views.signup, name='signup'),
    url(r'^list/(?:(?P<dir>[0-9a-z]+)/)?$', views.list_dir, name='list_dir'),
    url(r'^shares/', views.list_shares, name='shares'),
    url(r'^edit/(?P<pk>[0-9]+)/$', views.edit, name='edit'),
    url(r'^share/(?P<pk>[0-9]+)/$', views.share, name='share'),
    url(r'^delete/(?P<pk>[0-9]+)/$', views.delete, name='delete'),
]
