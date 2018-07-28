#!/usr/bin/env python
"""
Copyright (C) 2013-2017  Andrew Speakman

This file is part of UKPlanning, a library of scrapers for UK planning applications

UKPlanning is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

UKPlanning is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>."""
from scrapers import tests
try:
    from ukplanning import myutils
except ImportError:
    import myutils
import unittest
import run
import importlib
import logging
import os

def get_scraper_tests(test_class):
    'get the test list from a test class '
    testloader = unittest.TestLoader()
    return testloader.getTestCaseNames(test_class)
    
def get_module_scrapers(scraper_module): # gets names only - not classes
    'get the test list from a test class '
    this_mod = importlib.import_module(scraper_module)
    return run.get_scraper_names(this_mod)
    
def get_scraper_test_classes(test_module): # not used?
    ' get a dict of all scraper test classes in a module '
    result = {}
    for name in dir(test_module):
        this_obj = getattr(test_module, name)
        if isinstance(this_obj, type) and issubclass(this_obj, tests.BaseScraperTest):
            result[this_obj.__name__] = this_obj
    return result

def get_suite(scraper_list=None, module=None, test_list=None, group=None, kwargs={}):
    suite = unittest.TestSuite()
    if not scraper_list:
        scraper_list = get_module_scrapers(module) 
    for scraper in scraper_list:
        scraper_class = run.get_scraper_class(scraper)
        if not scraper_class:
            raise NameError("Cannot find class for %s scraper" % scraper)
        scraper_test_class = getattr(tests, scraper_class._test_class)
        if test_list:
            these_tests = test_list
        elif group and scraper_test_class.test_groups.get(group):
            these_tests = scraper_test_class.test_groups[group]
        else:
            these_tests = get_scraper_tests(scraper_test_class)
        for test in these_tests:
            testcase = scraper_test_class(test, scraper_class, kwargs)
            suite.addTest(testcase)
    return suite

def run_suite(suite, verbosity=1):
    unittest.TextTestRunner(verbosity=verbosity).run(suite)

if __name__ == "__main__":
    import sys
    import argparse

    print 'Getting scraper modules'
    log_choices = [ c for c in logging._levelNames.keys() if not isinstance(c, int) ]
    v_choices = [ '0', '1', '2' ]
    s_modules = run.all_scraper_modules() # slow?
    t_groups = tests.BaseScraperTest.test_groups.keys()

    parser = argparse.ArgumentParser(description='Test planning scrapers')
    parser.add_argument("-v", "--verbosity", help="verbosity level", default='1', choices=v_choices)
    parser.add_argument("-l", "--level", help="log level", default='DEBUG', choices=log_choices)
    parser.add_argument("-f", "--logfile", help="log file", default='../tests.log')
    
    excl1 = parser.add_mutually_exclusive_group(required=True)
    excl1.add_argument("-m", "--module", help="scraper module to test", choices=s_modules)
    excl1.add_argument("-s", "--scraper", help="name of a scraper or scrapers to test")
    
    excl2 = parser.add_mutually_exclusive_group()
    excl2.add_argument("-n", "--names", help="names of tests to run", nargs=argparse.REMAINDER)
    excl2.add_argument("-g", "--group", help="group of tests to run", choices=t_groups)
    args = parser.parse_args()

    #logging.basicConfig(format='%(asctime)s:%(name)s:%(levelname)s: %(message)s', 
    #    level=args.level, datefmt='%Y-%m-%dT%H:%M:%S',
    #    filename=args.logfile, filemode='w',
    #    )
    # this sets up a default console logger at ERROR level
    logging.basicConfig(format='%(name)s-%(levelname)s[%(asctime)s]: %(message)s', 
            datefmt='%Y-%m-%dT%H:%M:%S', level=logging.ERROR)
    # note need to explicitly set the root stream handler to same logging level
    handlers = logging.getLogger('').handlers
    for h in handlers:
        h.setLevel(logging.ERROR)
    
    if not args.scraper:
        scraper = None 
    else:
        if ',' in args.scraper:
            scraper = args.scraper.split(',')
        else:
            scraper = [args.scraper]
        
    try:
        os.remove(myutils.log_path(args.logfile, '.'))
    except:
        pass
        
    kwargs = { 'log_level': args.level, 'log_name': args.logfile, 'log_directory': '.' }
    print 'Getting test suite'
    suite = get_suite(scraper, args.module, args.names, args.group, kwargs)
    print 'Running test suite'
    run_suite(suite, int(args.verbosity))



