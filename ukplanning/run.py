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
import scrapers
from scrapers.base import BaseScraper
import types
import importlib
import logging
import pkgutil

# note this module finds named scraper classes based on their internal '_authority_name' attribute

logger = logging.getLogger(__name__)

def run_scraper(scraper_name, function_name = None, *args, **kwargs):
    """ instantiate a scraper by name and run one of its functions with the supplied arguments
    "log_level", "log_directory" are named arguments passed to get_scraper
    any other arguments go to the function"""
    newargs = {}
    accept = ['log_level', 'log_directory', 'log_name' ]
    for x in [x for x in kwargs.keys() if x in accept]:
        newargs[x] = kwargs.pop(x)
    this_scraper = get_scraper(scraper_name, **newargs)
    if not this_scraper:
        raise RuntimeError('instance of %s scraper already running' % scraper_name)
    if function_name:
        return getattr(this_scraper, function_name)(*args, **kwargs)
    else:
        return this_scraper(*args, **kwargs) # invokes __call__ method of class instance

def get_scraper(scraper_name, **kwargs):
    """ instantiate a scraper by name using the supplied arguments
    "log_level", "log_directory", "log_name" named arguments to scraper
    all other named arguments are ignored"""
    this_class = get_scraper_class(scraper_name)
    if not this_class:
        raise AttributeError('cannot find class for: %s' % scraper_name)
    newargs = {}
    accept = ['log_level', 'log_directory', 'log_name' ]
    for x in [x for x in kwargs.keys() if x in accept]:
        newargs[x] = kwargs.pop(x)
    return this_class.create(**newargs) # get singleton instance, returns None if already exists
    
def get_class(module_name, class_name, parent_class=BaseScraper):
    this_obj = None
    try:
        module_ = importlib.import_module(module_name)
        this_obj = getattr(module_, class_name, None)
    except ImportError:
        return None
    if not this_obj or not issubclass(this_obj, parent_class) or getattr(this_obj, '_disabled', False):
        return None
    else:
        return this_obj

def get_scraper_class(scraper_name, parent_class=BaseScraper, include_disabled=False):
    ' return a valid scraper class if the name matches '
    package = scrapers
    prefix = package.__name__ + "."
    for importer, modname, ispkg in pkgutil.walk_packages(package.__path__, prefix):
        if not ispkg:
            #module = __import__(modname, fromlist="dummy")
            module = importlib.import_module(modname)
            class_obj = get_module_scraper_class(module, scraper_name, parent_class, include_disabled)
            if class_obj:
				return class_obj
    return None
    
def all_scraper_classes(parent_class=BaseScraper, include_disabled=False):
    ' get a dict of all scraper classes in all sub-packages - where keys are authority names, values are classes '
    result = {}
    package = scrapers
    prefix = package.__name__ + "."
    for importer, modname, ispkg in pkgutil.walk_packages(package.__path__, prefix):
        if not ispkg:
            #module = __import__(modname, fromlist="dummy")
            module = importlib.import_module(modname)
            class_dict = get_scraper_classes(module, parent_class, include_disabled)
            result.update(class_dict)
    return result
    
def all_scraper_names(parent_class=BaseScraper, include_disabled=False):
    ' get a list of all scraper class names in all sub-packages - where values are authority names '
    result = []
    package = scrapers
    prefix = package.__name__ + "."
    for importer, modname, ispkg in pkgutil.walk_packages(package.__path__, prefix):
        if not ispkg:
            #module = __import__(modname, fromlist="dummy")
            module = importlib.import_module(modname)
            name_list = get_scraper_names(module, parent_class, include_disabled)
            result.extend(name_list)
    return result
    
def all_scraper_attributes(parent_class=BaseScraper):
    """ get a dict of all scrapers in all sub-packages - 
    where keys are authority names, values are dicts of relevant attributes """
    result = {}
    classes = all_scraper_classes(parent_class, True) # gets disabled scrapers
    for k, v in classes.items():
        result[k] = {
            'scraper': v._authority_name,
            'scraper_type': v._scraper_type if v._scraper_type else 'Custom',
            'base_type': v._base_type,
            'disabled': v._disabled,
            'class_name': v.__name__,
            'class': v,
            'module_name': v.__module__,
            'uid_only': v._uid_only,
            'uid_num': v._uid_num_sequence,
            'comment': v._comment if v._comment else ''
        }
    return result
    
def all_scraper_modules(parent_class=BaseScraper, include_disabled=False):
    ' get a list of names of all modules with valid scrapers in  '
    result = []
    package = scrapers
    prefix = package.__name__ + "."
    for importer, modname, ispkg in pkgutil.walk_packages(package.__path__, prefix):
        if not ispkg:
            #module = __import__(modname, fromlist="dummy")
            module = importlib.import_module(modname)
            has_scrapers = has_scraper_classes(module, parent_class, include_disabled)
            if has_scrapers:
                result.append(modname)
    return result
    """
        print "Found submodule %s (is a package: %s)" % (modname, ispkg)
    #    module = __import__(modname, fromlist="dummy")
    #    print "Imported", module
    for package in scrape_packages:
        _temp = importlib.import_module(package)
        objdict = vars(_temp)
        for key, obj in objdict.items():
            if isinstance(obj, types.ModuleType):
                class_dict = get_scraper_classes(obj, parent_class)
                result.update(class_dict)
    return result"""
    
def get_scraper_classes(module, parent_class=BaseScraper, include_disabled=False):
    ' get a dict of scraper classes in a module - where keys are authority names, values are classes '
    ' note abstract classes are not returned because they have no defined authority name '
    result = {}
    for name in dir(module):
        this_obj = getattr(module, name)
        if isinstance(this_obj, type) and issubclass(this_obj, parent_class):
            authority = getattr(this_obj, '_authority_name', None)
            disabled = getattr(this_obj, '_disabled', False)
            if authority and (include_disabled or not disabled):
                result[authority] = this_obj
    return result
	
def get_scraper_names(module, parent_class=BaseScraper, include_disabled=False):
    ' get a list of valid scraper names in a module '
    ' note abstract classes are not returned because they have no defined authority name '
    result = []
    for name in dir(module):
        this_obj = getattr(module, name)
        if isinstance(this_obj, type) and issubclass(this_obj, parent_class):
            authority = getattr(this_obj, '_authority_name', None)
            disabled = getattr(this_obj, '_disabled', False)
            if authority and (include_disabled or not disabled):
                result.append(authority)
    return result
    
def has_scraper_classes(module, parent_class=BaseScraper, include_disabled=False):
    ' flag if a module contains any valid scraper classes '
    for name in dir(module):
        this_obj = getattr(module, name)
        if isinstance(this_obj, type) and issubclass(this_obj, parent_class):
            authority = getattr(this_obj, '_authority_name', None)
            disabled = getattr(this_obj, '_disabled', False)
            if authority and (include_disabled or not disabled):
                return True
    return False
	
def get_module_scraper_class(module, scraper_name, parent_class=BaseScraper, include_disabled=False):
    ' get a named valid scraper class it it exists in a module '
    for name in dir(module):
        this_obj = getattr(module, name)
        if isinstance(this_obj, type) and issubclass(this_obj, parent_class):
            authority = getattr(this_obj, '_authority_name', None)
            disabled = getattr(this_obj, '_disabled', False)
            if authority and authority == scraper_name and (include_disabled or not disabled):
                return this_obj
    return None
	
if __name__ == "__main__":
    import sys
    import argparse
    import time
    
    actions = [ 'fetch_application', 'gather_ids', 'show_application', 'get_max_sequence' ]

    log_choices = [ c for c in logging._levelNames.keys() if not isinstance(c, int) ]
    
    parser = argparse.ArgumentParser(description='Run a planning scraper')
    parser.add_argument("scraper", help="name of the scraper")
    parser.add_argument("-l", "--level", help="log level", default='INFO', choices=log_choices)
    parser.add_argument("-g", "--logdir", help="log directory")
    parser.add_argument("action", help="action for the scraper", nargs=argparse.REMAINDER, choices=actions)
    args = parser.parse_args()
    # note the optional parameters all refer to the scrapers which each have their own store / log files at default INFO level

    if args.scraper:
    	# this sets up a default console logger at WARNING level
	    logging.basicConfig(format='%(name)s-%(levelname)s[%(asctime)s]: %(message)s', 
		    datefmt='%Y-%m-%dT%H:%M:%S', level=logging.WARNING)
	    # note need to explicitly set the root stream handler logging level to WARNING
	    handlers = logging.getLogger('').handlers
	    for h in handlers:
	        h.setLevel(logging.WARNING)
	
	    kwargs = { 'log_level': args.level, 'log_directory': args.logdir  }
	    aargs = args.action[1:]
	    print run_scraper(args.scraper, args.action[0], *aargs, **kwargs)
	
