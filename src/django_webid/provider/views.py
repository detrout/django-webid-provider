#!/usr/bin/python
# vim: set expandtab tabstop=4 shiftwidth=4:
# -*- coding: utf-8 -*-

#
# Copyright (C) 2011 julia dot anaya at gmail dot com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
"""
    views
    ~~~~~~~~

    :authors:       Ben Carrillo, Julia Anaya
    :organization:  rhizomatik labs
    :copyright:     author
    :license:       GNU GPL version 3 or any later version
                    (details at http://www.gnu.org)
    :contact:       bennomadic at gmail dot com
    :dependencies:  python (>= version 2.6)
    :change log:
    :TODO:
"""
import hashlib
import logging
import os
import random
import re

#from datetime import datetime

from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect,\
        get_object_or_404
from django.template import RequestContext
from django import template
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from django.db import models

#XXX this import should be handled on certs.utils now
from OpenSSL import crypto

#XXX FIXME fix relative imports
#from .models import PubKey,
from .models import WebIDUser, CertConfig
#from .certs.utils import create_cert # deprecated
from .certs.utils import CertCreator


#XXX PKCS12 SHIT
#... that we could shut down by the moment...
from .certs.utils import gen_httpwebid_selfsigned_cert_pemfile, pemfile_2_pkcs12file

from .forms import WebIdIdentityForm


from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from django.db.models.signals import post_save
from django.dispatch import receiver




#############################################################
# VIEWS BEGIN
#############################################################


################
# CREATE USER
################

def create_user(request):
    """
    creates user and redirects to the page
    for installing a cert.
    """
    #XXX should check it's anon_login,
    #or redirect to logout in other case.

    #This view SHOULD NOT be available if this config
    #is not allowed in settings. We can do that by
    #manually removing from urls.
    #We could also put here a decorator that checks
    #the settings and allows/denies access to view.

    #XXX TODO
    #on this view (or another different??) we should
    #introduce an **email verification** step.

    errors = False
    messages = []

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            if not errors:
                u = form.save()

                if settings.DEBUG:
                    logging.debug('created user... %s' % u)
                    logging.debug('active? %s' % u.is_active)

                u.backend = 'django.contrib.auth.backends.ModelBackend'
                auth_login(request, u)

                return redirect('webidprovider-add_cert')


            return render_to_response('django_webid/provider/create_user.html', {
                'form': form,
                "MEDIA_URL": settings.MEDIA_URL,
                "STATIC_URL": settings.STATIC_URL,
                'messages': messages,
                },
                context_instance=RequestContext(request))
    else:
        form = UserCreationForm()

    return render_to_response('django_webid/provider/create_user.html',
     {
        'form': form,
        "MEDIA_URL": settings.MEDIA_URL,
        "STATIC_URL": settings.STATIC_URL,
        'messages': messages,
     }, context_instance=RequestContext(request))



#####################
# CERT:ADD
#####################

@login_required
#XXX doubt... will this decorator work also for webid-auth?
#if not logged in, it should check if anon register is allowed
#and redirect there...
#XXX but now it's redirecting to the accounts url that is not
#being loaded...
def add_cert_to_user(request):
    messages = []
    if request.method == 'POST':
        if request.POST.has_key('pubkey'):
            user = request.user
            spkac_str = str(request.POST['pubkey'])

            #XXX should catch exception here (bad pubkey???)
            #XXX or tampered challenge :)

            kwargs = {}
            #XXX get kwargs from the post advanced fields

            ####################################################
            #XXX DEBUG ------------------ TO BE REMOVED
            #FIXME !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            #import datetime
            #kwargs['for_days']=90
            #kwargs['from_days']=60
            ##kwargs['valid_from_ts'] = datetime.datetime(2012,1,1,12,0,0)
            ##kwargs['expires_ts'] = datetime.datetime(2012, 12, 31, 12, 0)
            #FIXME !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            ####################################################

            c = CertCreator(spkac_str, user, **kwargs)
            c.create_cert()
            certdump = c.get_cert_dump()

            r = HttpResponse(mimetype="application/x-x509-user-cert")
            r.write(certdump)
            return r

    app_conf = CertConfig.objects.single()
    r = random.getrandbits(100)
    challenge = hashlib.sha1(str(r)).hexdigest()

    return render_to_response('django_webid/provider/webid_add_to_user.html',
        {
        "HIDE_KEYGEN_FORM": app_conf.hide_keygen_form,
        "MEDIA_URL": settings.MEDIA_URL,
        "ADMIN_MEDIA_PREFIX": settings.ADMIN_MEDIA_PREFIX,
        "STATIC_URL": settings.STATIC_URL,
        "challenge": challenge,
        'messages': messages},
        context_instance=RequestContext(request))


###########################################
# WEBID VIEWS                             #
###########################################

def render_webid(request, username=None):
    uu = get_object_or_404(WebIDUser,
            username=username)
    return render_to_response('django_webid/provider/foaf/webid_rdfa.html',
             {
             "webiduser": uu,
             "MEDIA_URL": settings.MEDIA_URL,
             "STATIC_URL": settings.STATIC_URL,
             })
             #, context_instance=RequestContext(request))


###########################################
# CERTS VIEWS                             #
###########################################
# functions for add / display / remove (remove
# should maybe mark a cert as non active??)
# we could change the manager... objects = filter(active=True)
# and leave the old manager as a legacy manager objects_all




###################################################
###########################################
# OLD VIEWS THAT WE CAN KEEP BUT NEED TO BE
# REFACTORED TO USE NEW FUNCTIONS
###########################################
###################################################


def webid_identity_keygen(request):
    """
    Create only http-WebID certificate
    using keygen in the browser
    """
    #XXX FIXME
    # REFACTOR using above functions... :/
    #XXX TODO:
    #Detect if using IExplorer (support needed?)
    #and leave the .p12 as a fallback mechanism.
    #they say it's a good fallback for things like iphone
    #sending the pkcs12 (w/ pass) by email.

    #XXX TODO: try also javascript CSR creation... which
    #format does it produce??

    errors = False
    messages = []

    if request.method == 'POST':
        form = WebIdIdentityForm(request.POST)
        if form.is_valid():
            if not errors:
                webid = str(form.cleaned_data['webid'])
                nick = str(form.cleaned_data['nick'])

                #XXX REFACTOR ##############################
                pubkey = re.sub('\s', '', str(request.POST['pubkey']))
                if settings.DEBUG:
                    logging.debug('PUBKEY=%s' % pubkey)
                    #print('PUBKEY=%s' % pubkey)
                spki = crypto.NetscapeSPKI(pubkey)
                cert = crypto.X509()
                cert.get_subject().C = "US"
                cert.get_subject().ST = "Minnesota"
                cert.get_subject().L = "Minnetonka"
                cert.get_subject().O = "my company"
                cert.get_subject().OU = "WebID"
                cert.get_subject().CN = nick
                cert.set_serial_number(001)
                cert.gmtime_adj_notBefore(0)
                cert.gmtime_adj_notAfter(10*365*24*60*60)
                cert.set_issuer(cert.get_subject())
                URI_STR = 'URI:%s' % (webid)
                ext = crypto.X509Extension('subjectAltName', 1,
                    URI_STR)
                cert.add_extensions([ext])
                cert.set_version(2) # version 3 (decimal)
                #we get the pubkey from the spkac
                cert.set_pubkey(spki.get_pubkey())
                res = crypto.dump_certificate(crypto.FILETYPE_ASN1, cert)
                r = HttpResponse(mimetype="application/x-x509-user-cert")
                r.write(res)
                return r
                #XXX REFACTOR ##############################

            return render_to_response('django_webid/provider/webid_identity_keygen.html', {
                'form': form,
                "MEDIA_URL": settings.MEDIA_URL,
                "STATIC_URL": settings.STATIC_URL,
                'messages': messages,
            }, context_instance=RequestContext(request))
    else:
        form = WebIdIdentityForm() # An unbound form

    return render_to_response('django_webid/provider/webid_identity_keygen.html', {
        #XXX TODO: add randomchars challenge...
        'form': form,
        "MEDIA_URL": settings.MEDIA_URL,
        "STATIC_URL": settings.STATIC_URL,
        'messages': messages,
    }, context_instance=RequestContext(request))



def webid_identity(request):
    """
    Create only http-WebID certificate
    """

    #XXX TODO
    #this is very similar to above
    #function, but creates the cert as a pkcs12.
    #XXX TODO CHANGE VIEW NAME!!! --> TO PKCS12_IDENTITY
    #OR SOMETHING LIKE THAT...

    #REFACTOR!! ################################

    #Detect if using IExplorer (support needed?)
    #and leave the .p12 as a fallback mechanism.

    errors = False
    messages = []

    if request.method == 'POST':
        form = WebIdIdentityForm(request.POST)
        if form.is_valid():
            if not errors:
                webid = str(form.cleaned_data['webid'])
                nick = str(form.cleaned_data['nick'])
                try:
                    gen_httpwebid_selfsigned_cert_pemfile(webid, nick=nick)
                    #XXX THIS IS THE SECOND MIX USE OF OPENSSL/M2CRYPTO
                    path = pemfile_2_pkcs12file()
                    print "PKC12 path: " + path
                except Exception, e:
                    message = "Error trying to generate client certificate: " + str(e)
                    print message
                    messages.append(message)
                    # can not continue
                else:
                    fp = open(path)
                    content = fp.read()
                    fp.close()
                    length = os.path.getsize(path)
                    r = HttpResponse(mimetype="application/x-x509-user-cert")
                    #handle = webid.split('/')[-1] # XXX ugly, but has to be something!
                    r['Content-Disposition'] = 'attachment; filename=%s%s' % (nick, "_cert.p12")
                    r["Content-Length"] = length
                    r["Accept-Ranges"] ="bytes"
                    r.write(content)
                    messages.append("created")
                    return r
#            finally:
            # if exception or not is happend and no return is already executed
            return render_to_response('django_webid/provider/webid_identity.html', {
                'form': form,
                "MEDIA_URL": settings.MEDIA_URL,
                "STATIC_URL": settings.STATIC_URL,
                'messages': messages,
            }, context_instance=RequestContext(request))
    else:
        form = WebIdIdentityForm()

    return render_to_response('django_webid/provider/webid_identity.html', {
        'form': form,
        "MEDIA_URL": settings.MEDIA_URL,
        "STATIC_URL": settings.STATIC_URL,
        'messages': messages,
    }, context_instance=RequestContext(request))





###########################################
#            SIGNALS                      #
###########################################


@receiver(post_save, sender=User)
def init_blank_profile_for_new_user(sender, **kwargs):
    """
    initializes a blank profile for webiduser
    in the moment of its creation.
    """
    if kwargs.get('created', None):
        user = kwargs.get('instance')
        webiduser = WebIDUser.objects.get(id=user.id)

        profile_model = settings.AUTH_PROFILE_MODULE
        app_split = profile_model.split('.')
        if len(app_split) == 2:
            app_label, mod_label = app_split
        else:
            app_label, mod_label = app_split[-2:]
        pklss = models.get_model(app_label, mod_label)

        pklss.objects.create(user=webiduser)
