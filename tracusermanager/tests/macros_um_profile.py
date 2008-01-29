# -*- coding: utf-8 -*-

import unittest

from tracusermanager.profile.macros import MacroArguments

class MacrosTestCase(unittest.TestCase):
    
    def test_macros_arguments(self):
            
        testString="intVar=10,strVar=balamuc,list=abc\,cucu\,piscot,dict={piscina=123\,masca=123}"
        
        args=MacroArguments(testString)
        self.assertEquals(args.get_int('intVar'), 10)
        self.assertEquals(args.get('strVar'), 'balamuc')
        self.assertEquals(args.get_list('list'), ['abc','cucu','piscot'])
        self.assertEquals(args.get_dict('dict'),dict(piscina="123",masca="123"))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MacrosTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')