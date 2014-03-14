from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^home/$', 'r.views.home', name='home'),
    url(r'^setup/$', 'r.views.setup', name='setup'),
    url(r'^scripts/$', 'r.views.scripts', name='scripts'),
    url(r'^packages/$', 'r.views.packages', name='packages'),
)