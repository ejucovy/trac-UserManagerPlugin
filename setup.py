#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#
# Copyright 2007-2008 Optaros, Inc
#

from setuptools import setup

setup(name="TracUserManagerPlugin",
      version="0.4",
      packages=['tracusermanager', 
                'tracusermanager.account', 
                'tracusermanager.permissions',
                'tracusermanager.profile'],
      author="Catalin Balan", 
      author_email="cbalan@optaros.com", 
      url="http://code.optaros.com/trac/oforge",
      description="Trac User Manager",
      license="BSD",
      entry_points={'trac.plugins': [
            'tracusermanager.api = tracusermanager.api',
            'tracusermanager.admin = tracusermanager.admin',
            'tracusermanager.account = tracusermanager.account',
            'tracusermanager.permissions = tracusermanager.permissions',
            'tracusermanager.profile = tracusermanager.profile'
            ]},
      package_data={'tracusermanager' : ['htdocs/js/*.js', 
                                         'htdocs/css/*.css', 
                                         'templates/*.html',
                                         'htdocs/img/*.png']},
      
      test_suite = 'tracusermanager.tests'
      ) 
