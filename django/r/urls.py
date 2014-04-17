from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^$', 'r.views.default', name='default'),
    url(r'^setup/$', 'r.views.setup', name='setup'),
    url(r'^examples/$', 'r.views.examples', name='examples'),
    url(r'^scripts/$', 'r.views.scripts', name='scripts'),
    url(r'^scripts/(\w+)/$', 'r.views.script', name='script'),
    url(r'^packages/$', 'r.views.packages', name='packages'),
    url(r'^install_package/$', 'r.views.install_package', name='install_package'),
    url(r'^package_state/$', 'r.views.package_state', name='package_state'),
)