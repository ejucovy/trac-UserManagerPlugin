# -*- coding: utf-8 -*-
#
# Copyright 2008 Optaros, Inc.
#

import doctest
import unittest

from tracusermanager.tests import api, macros_um_profile

def suite():    
    suite = unittest.TestSuite()
    suite.addTest(api.suite())
    suite.addTest(macros_um_profile.suite())
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
