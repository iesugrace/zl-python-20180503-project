from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^signup/$', views.signup, name='signup'),
    url(r'^list/(?P<pk>[0-9a-z]+)/$', views.list_dir, name='list_dir'),
    url(r'^detail/(?P<pk>[0-9]+)/$', views.detail, name='detail'),
    url(r'^view/(?P<pk>[0-9]+)/$', views.view, name='view'),
    url(r'^download/(?P<pk>[0-9]+)/$', views.download, name='download'),
    url(r'^edit/(?P<pk>[0-9]+)/$', views.edit, name='edit'),
    url(r'^delete/(?P<pk>[0-9]+)/$', views.delete, name='delete'),
    url(r'^share/list/$', views.list_shares, name='list_shares'),
    url(r'^share/create/(?P<pk>[0-9]+)/$', views.create_share, name='create_share'),
    url(r'^share/edit/(?P<pk>[0-9]+)/$', views.edit_share, name='edit_share'),
    url(r'^share/delete/(?P<pk>[0-9]+)/$', views.delete_share, name='delete_share'),
    url(r'^post_code/(?P<pk>[0-9]+)/$', views.post_code, name='post_code'),
    url(r'^captcha/', views.gen_captcha, name='gen_captcha'),
]
