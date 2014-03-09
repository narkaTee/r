from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^home/$', 'r.views.home', name='home'),
    url(r'^summary/$', 'r.views.summary', name='summary'),
)