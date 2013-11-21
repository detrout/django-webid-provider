# from django.conf.urls.defaults import *
# #from django.views.generic.simple import redirect_to
# from django.views.generic import RedirectView
# #from django.views.generic.list_detail import object_list
from webid_provider import views, webidprofile
# #from django_webid.provider.models import Cert

from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

 
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
#     #Main, WORKING urls
# 
#     #temporary REDIRECT
#     # XXX move to the sample project
#     #url(r'^$', redirect_to, {'url': 'cert/add'}),
#     url(r'^$', RedirectView.as_view(url='cert/add')),
    url(r'^$', TemplateView.as_view(template_name='webid_provider/webid_index.html'), name="home"),

    # Binding with django-registration
    url(r'^accounts/', include('registration.backends.default.urls')),
    #url(r'^accounts/login/', 'django.contrib.auth.views.login'),
    url(r'^logout$', "webid_provider.views.logout_view", name="webidprovider-logout"),
 
     ###################################
     #BEGIN django_webid.provider views
 
     #certs/all/ --> take all objects from pubkey manager (currently should
     #be only active)
    #url(r'^certs$', views.cert_list_by_user, name="webidprovider-cert_list"),
    url(r'^certs$', views.CertListView.as_view(), name="webidprovider-cert_list"),
    url(r'^cert/add$', views.add_cert_to_user, name="webidprovider-add_cert"),
    url(r'^cert/added$', views.cert_post_inst,
        name="webidprovider-cert-postinst"),
    url(r'^cert/(?P<cert_id>\d+)/$', views.CertDetailView.as_view(),
        name="webidprovider-cert-detail"),

    url(r'^cert/(?P<cert_id>\d+)/revoke$', views.cert_revoke,
        name="webidprovider-cert-revoke"),
 
    #Our simple user creation view.
    #XXX we should move it to example site too.
    url(r'^user/add$', views.create_user, name='webidprovider-create_user'),
# 
    #ajax utility views
    url(r'^ajax/checkcertdlvrd', views.check_cert_was_delivered,
        name='webidprovider-checkcertdlvrd'),
    url(r'^ajax/certnameit', views.cert_nameit,
        name='webidprovider-nameit'),
 
 
    #WebID Profile / Foaf publishing...
    #XXX can we do some magic here? (asking settings, finstance)
    #XXX should be "%s/foo" % settings.WEBID_PATH
    #XXX We MUST allow for other app to take control of this
    #XXX but at the same time provide a fallback mechanism...
 
    url(r'^(?P<username>\w+)$',
        webidprofile.WebIDProfileView.as_view(), name="webidprovider-webid_uri"),

#
#     ################################################
#     ################################################
#     # Some other, older tests: to be cleaned from here...
#     # Might be BROKEN
# 
#     url(r'^cert/p12/add$', views.webid_identity,
#         name='webidprovider-webid_identity1'),
#     url(r'^cert/keygen$', views.webid_identity_keygen,
#         name='webidprovider-webid_identity_keygen'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
 
    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
