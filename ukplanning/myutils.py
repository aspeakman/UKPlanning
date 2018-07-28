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
import re
from datetime import datetime, date
import urllib, urllib2, urlparse
import logging, logging.handlers
import dateutil.parser
import os
import json

logger = logging.getLogger(__name__)

GAPS_REGEX = re.compile(r'\s+', re.U) # unicode spaces include html &nbsp;
EXTRACT_FULL_REGEX = re.compile(r'\b([A-Z][A-Z]?\d(?:\d|[A-Z])?)\s*(\d[ABDEFGHJLNPQRSTUWXYZ]{2})\b', re.I) # ignore case
NONALPHA_REGEX = re.compile(r'\W+', re.U) # non-alphanumeric characters

def get_dt(supplied_date, date_format=None):
    ' get a date using the format, if supplied - returns None if the string cannot be parsed '
    if not supplied_date:
        return None
    if isinstance(supplied_date, date):
        return supplied_date
    elif isinstance(supplied_date, datetime):
        return supplied_date.date()
    if date_format:
        try:
            return datetime.strptime(supplied_date, date_format).date()
        except (ValueError, TypeError):
            pass
    try:
        norm_dt = GAPS_REGEX.sub(' ', supplied_date) # normalise any internal space (allows date conversion to handle non-breakable spaces)
        if not norm_dt or norm_dt == ' ' or norm_dt == "''": # test for empty date strings
            return None # deals with bug where the date parser turns an all spaces string into today's date
        return dateutil.parser.parse(norm_dt, dayfirst=True, yearfirst=True).date()
        # if yearfirst = True means precedence is YY-MM-DD > DD-MM-YY > MM-DD-YY see dateutil docs
        # if yearfirst = False means precedence is DD-MM-YY > MM-DD-YY > YY-MM-DD see dateutil docs
    except (ValueError, TypeError):
        return None
        
def get_dttm(supplied_datetime, datetime_format=None):
    ' get a datetime using the format, if supplied - returns None if the string cannot be parsed '
    if not supplied_datetime:
        return None
    if isinstance(supplied_datetime, datetime):
        return supplied_datetime
    elif isinstance(supplied_datetime, date):
        return datetime(supplied_datetime.year, supplied_datetime.month, supplied_datetime.day)
    if datetime_format:
        try:
            return datetime.strptime(supplied_datetime, datetime_format)
        except (ValueError, TypeError):
            pass
    try:
        norm_dttm = GAPS_REGEX.sub(' ', supplied_datetime) # normalise any internal space (allows date conversion to handle non-breakable spaces)
        if not norm_dttm or norm_dttm == ' ' or norm_dttm == "''": # test for empty date strings
            return None # deals with bug where the date parser turns an all spaces string into today's date
        return dateutil.parser.parse(norm_dttm, dayfirst=True, yearfirst=True)
    except (ValueError, TypeError):
        return None
    
# add new data elements to the existing query of a URL
def add_to_query(url, data = {}):
    u = urlparse.urlsplit(url)
    qdict = dict(urlparse.parse_qsl(u.query))
    qdict.update(data)
    query = urllib.urlencode(qdict)
    new_url = urlparse.urlunsplit((u.scheme, u.netloc, u.path, query, u.fragment))
    return new_url

def get_filepath(name, directory = None):
    ' check if a file exists here or in a directory off the current or parent directory '
    parent = os.path.abspath(os.pardir)
    if directory:
        dir_file = None
        if os.path.isdir(directory): # directory exists
            dir_file = os.path.join(directory, name)
            if os.path.isfile(dir_file): # found existing file in directory
                return os.path.abspath(dir_file)
        parent_dir = os.path.join(parent, directory)
        pardir_file = None
        if os.path.isdir(parent_dir): # directory exists in parent
            pardir_file = os.path.join(parent_dir, name)
            if os.path.isfile(pardir_file): # found existing file in parent directory
                return pardir_file
        # file not found so return name of file to create
        if dir_file: # first pref is in local directory if it exists
            return os.path.abspath(dir_file)
        elif pardir_file: # second pref is in parent directory if it exists
            return pardir_file
    else:
        if os.path.isfile(name): # found existing file
            return os.path.abspath(name)
        par_file = os.path.join(parent, name)
        if os.path.isfile(par_file): # found existing file in parent
            return par_file
        return os.path.abspath(name) # fallback option, use the name anyway

def setup_logger(log_name, fh, level = None):
    ' set up a file handler log '
    if log_name.endswith('.log'):
        log_name = log_name[:-4]
    logger = logging.getLogger(log_name)
    if not level:
        level = logging.INFO
    logger.setLevel(level) # determines the level sent to all handlers
    fh.setLevel(level) # determines the level output by this handler
    formatter = logging.Formatter('%(name)s-%(levelname)s[%(asctime)s]: %(message)s',
            '%Y-%m-%dT%H:%M:%S')
    fh.setFormatter(formatter)
    if logger.handlers: # loggers are global, so this one might have been set up before
        for h in logger.handlers: # remove existing handlers
            logger.removeHandler(h)
    logger.addHandler(fh)
    return logger
    
def log_path(log_name, directory = None):
    if not '.' in log_name:
        log_name = log_name + '.log'
    return get_filepath(log_name, directory)
    
def frotate_handler(log_path, maxBytes=1000000, backupCount=2):
    return logging.handlers.RotatingFileHandler(log_path, mode='a', maxBytes=maxBytes, backupCount=backupCount)
    
def file_handler(log_path):
    return logging.FileHandler(log_path, mode='w')
    
def extract_postcode(text):
    if not text: return None
    postcode_match = EXTRACT_FULL_REGEX.search(text)
    if postcode_match and postcode_match.lastindex >= 2:
        return postcode_match.group(1).upper() + ' ' + postcode_match.group(2).upper()
    return None
    
def dict_lookup(dic, key, *keys):
    # lookup a value in a dict
    # the key/keys parameter is either a single key which means a direct lookup at current level
    # or an array of keys, in which case the lookup takes place down within the dict sub-tree
    # integer keys are taken as list array element indexes (if a list exists)
    # if no value exists at indicated position, always returns None
    # eg *[ 'a', 'c' ] would return 'val2' from { 'a': { 'b': 'val1', 'c': 'val2' } }
    # eg *[ 'a', 2 ]  would return 'val2' from { 'a': [ 'val0', 'val1', 'val2' ] }
    if keys:
        sub_dict = dic.get(key, {})
        if sub_dict:
            return dict_lookup(sub_dict, *keys)
        sub_list = dic.get(key, [])
        if sub_list:
            return dict_lookup(sub_list, *keys)
        return None
    if isinstance(dic, list):
        try:
            return dic[key]
        except IndexError:
            return None
    else:
        return dic.get(key)

def read_defaults(json_file='plan_defaults.json', existing=None):
    # if there is a JSON config file - use default settings there
    if not existing:
        existing = {}
    if os.path.isfile(json_file):
        with open(json_file) as defaults_file:    
            ddata = json.load(defaults_file)
            if ddata and ddata.get('defaults'):
                for k, v in ddata['defaults'].items():
                    if not k.startswith('_') and (isinstance(v, bool) or v == 0 or v):
                        existing[k] = v
    return existing


