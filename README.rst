WebID Provider Django App
=========================

Authors:
  Ben Carrillo <bennomadic@gmail.com> / <ben@futeisha.org>
  Julia Anaya <julia.anaya@gmail.com>

**Warning**!
------------

**This package is still in early alpha!** The database models are likely to change for the next few releases,
and the api is still subject to changes. By the moment I won't bother in using south for schema migrations,
so assume **things still will break for some time**. You've been warned! :P
  
Introduction
------------
A reusable django app that turns any django-powered site into a `WebID provider <http://webid.info/spec>`_.

The main Django 1.5 application is in 'webidprovider'. It just binds 2 sub components :
 - 'webid_provider' : the main engine of the WebID provider application
 - 'example_webid_provider' : the visual identity of the site

Issues / contributing
---------------------
You can use either the `github bug tracker <https://github.com/bennomadic/django-webid-provider/issues>`_ or the `official tracker at Quinode's redmine <http://redmine.django.coop/projects/webid-provider>`_. Patches by mail or pull requests are also welcome :)

Testing
-------

 $ python ./manage.py [command]

Use fabric magic::

  fab init
  fab test
  fab clean

Installation
------------
You can either::

  pip install django-webid-provider

or::

  git clone git://github.com/bennomadic/django-webid-provider.git
  python setup.py install

Note that fabric will initialize a clean virtualenv with all the deps for you. From the root folder of the distribution::

  pip install fabric
  fab init

