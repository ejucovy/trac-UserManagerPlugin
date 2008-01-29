# -*- coding: utf-8 -*-

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
