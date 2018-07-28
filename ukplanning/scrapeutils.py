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
import mechanize
import cookielib
import re
import urlparse
import lxml.html
import lxml.html.soupparser
import lxml.etree
import socket
from datetime import timedelta
from datetime import datetime
from datetime import date
from BeautifulSoup import BeautifulSoup
import cookielib
import urllib, urlparse

RFC822_DATE = "%a, %d %b %Y %H:%M:%S %z"
ISO8601_DATE = "%Y-%m-%d"
RFC3339_DATE = "%Y-%m-%dT%H:%M:%SZ"
DATE_FORMAT = "%d/%m/%Y"
SCRIPT_REGEX = re.compile(r'<script\s.*?</script>', re.I | re.S)
HTCOM_REGEX = re.compile(r'<!--.*?-->', re.S)
TAGS_REGEX = re.compile(r'<[^<]+?>')
JSESS_REGEX = re.compile(r';jsessionid=\w*')
WEEKDAYS = { 'Mon': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3, 'Fri': 4, 'Sat': 5, 'Sun': 6 }

mechanize._sockettimeout._GLOBAL_DEFAULT_TIMEOUT = 300.0 # fall back 5 mins inactivity note default is object() meaning no timeout?

# various classes and utilty functions for use in UKPlanning

# subclass the mechanize browser to add an individual per browser timeout setting
class Browser(mechanize.Browser):
    def __init__(self, history=None, request_class=None, timeout=None):
        self._timeout = timeout if timeout else mechanize._sockettimeout._GLOBAL_DEFAULT_TIMEOUT
        # do this last to avoid __getattr__ problems
        mechanize.Browser.__init__(self, history=history, request_class=request_class)

    def open_novisit(self, url, data=None, timeout=None):
        timeout = timeout if timeout else self._timeout
        return self._mech_open(url, data, visit=False, timeout=timeout)

    def open(self, url, data=None, timeout=None):
        timeout = timeout if timeout else self._timeout
        return self._mech_open(url, data, timeout=timeout)
    
# gets a mechanize browser
def get_browser(headers = None, handler_type = '', proxy = '', timeout=None):
    br = Browser(timeout=timeout)
    cj = cookielib.LWPCookieJar()
    br.set_cookiejar(cj)
    if proxy:
        # see http://www.publicproxyservers.com/proxy/list_uptime1.html
        br.set_proxies({"https": proxy, "http": proxy}) 
        # https tunnel via http proxy not working - bug fixed below but same problem?
        # http://sourceforge.net/mailarchive/forum.php?thread_name=alpine.DEB.2.00.0910062211230.8646%40alice&forum_name=wwwsearch-general
    else:
        br.set_proxies(None) 
    br.set_handle_robots(False)
    if headers: 
        br.addheaders = headers.items() # Note addheaders is a data object (list of tuples) not a method
    else:
        br.addheaders = []
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    handlersToKeep = []
    for handler in br.handlers:
        if not isinstance(handler, (SoupHandler, EtreeHandler)):
            handlersToKeep.append(handler)
    br.handlers = handlersToKeep
    if handler_type == 'soup':
        ihandler = SoupHandler()
        br.add_handler(ihandler)
    elif handler_type == 'etree':
        ihandler = EtreeHandler()
        br.add_handler(ihandler)
    return br, cj
    
# put a cookie in the jar
def set_cookie(cookie_jar, cname, cvalue, cdomain=None, cpath='/'):
    ck = cookielib.Cookie(version=0, name=str(cname), value=str(cvalue), domain=cdomain, path=cpath, 
            port=None, port_specified=False, domain_specified=False, expires=None, 
            domain_initial_dot=False, path_specified=True, secure=False, 
            discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
    cookie_jar.set_cookie(ck)
        
# selects a form and sets up its fields, action, method etc
# in the case of HTML select tags, the particular control used is always selected by name
# e.g. <select name="name"> <option value="value"> label </option> </select>
# however the option selected can be via the value attribute or by label (if the key starts with #)
# controls can be disabled by setting them to None
def setup_form(br, form = None, fields = None, action = None, method = None):
    if not form:
        br.select_form(nr=0)
    elif form.isdigit(): # by number
        br.select_form(nr=int(form))
    elif form.startswith('#'): # selects by id
        for f in br.forms():
            if f.attrs.get('id', '') == form[1:]:
                br.form = f
                break # success
        else: # failure
            br.select_form(name=form)
    else: # by name
        br.select_form(name=form)
    if action:
        current_action = br.form.action
        new_action = urlparse.urljoin(current_action, action)
        br.form.action = new_action
    if method and method.upper() == 'GET':
        br.form.method = method
    #print br.form
    if fields:
        add_controls = []
        for k, v in fields.items():
            try:
                if k.startswith('#'):
                    control = br.find_control(id=k[1:], nr=0) # find first control with id k
                elif k.startswith('@'):
                    control = br.find_control(name=k[1:], nr=0) # find first control named k
                else:
                    control = br.find_control(name=k, nr=0) # find first control named k
            except mechanize.ControlNotFoundError as e: # if the control does not exist, we create a dummy hidden control to hold the value
                if k.startswith('#') or k.startswith('@'):
                    add_controls.append(k[1:])
                else:
                    add_controls.append(k)
        if add_controls:
            for k in add_controls:
                br.form.new_control('hidden', k, {'value':''} )
            br.form.fixup()
        br.form.set_all_readonly(False)
        for k, v in fields.items():
            if k.startswith('@'): # used to set a named control using an option label
                control = br.find_control(name=k[1:], nr=0) # find first control named k
                if v is None:
                    control.disabled = True
                elif isinstance(v, list):
                    if control.disabled: control.disabled = False
                    for i in v:
                        control.get(label=i, nr=0).selected = True # set the value by selecting its label (v[i])
                else:
                    if control.disabled: control.disabled = False
                    control.get(label=v, nr=0).selected = True # set the value by selecting its label (v)
                    # NB label matches any white space compressed sub string so there is potential for ambiguity errors
            else:
                #br[k] = v # default is to directly assign the named control a value (v)
                if k.startswith('#'):
                    control = br.find_control(id=k[1:], nr=0) # find first control with id of k
                else:
                    control = br.find_control(name=k, nr=0) # find first control named k
                if v is None:
                    control.disabled = True
                elif (control.type == 'radio' or control.type == 'checkbox' or control.type == 'select') and not isinstance (v, list):
                    if control.disabled: control.disabled = False
                    control.value = [ v ]
                elif (control.type != 'radio' and control.type != 'checkbox' and control.type != 'select') and v and isinstance (v, list):
                    if control.disabled: control.disabled = False
                    control.value = v [0]
                else:
                    if control.disabled: control.disabled = False
                    control.value = v
        # NB throws except mechanize.ItemNotFoundError as e: if field select/check/radio option does not exist

def submit_form(br, submit = None):
    """returns response after submitting a form via a mechanize browser
    submit parameter is a submit control name/number or an id (if it starts with a '#')"""
    if not submit:
        response = br.submit()
    elif submit.isdigit():
        response = br.submit(nr=int(submit))
    elif submit.startswith('#'):
        control = br.find_control(id=submit[1:], nr=0) # find first control with id submit
        if control.disabled: control.disabled = False
        response = br.submit(id=submit[1:], nr=0)
    else:
        control = br.find_control(name=submit, nr=0) # find first control named submit
        if control.disabled: control.disabled = False
        response = br.submit(name=submit, nr=0)
    return response
    
def list_forms(br):
    result = []
    nr = 0
    for f in br.forms():
        out = {}
        out['name'] = f.name
        out['attrs'] = f.attrs
        out['nr'] = nr
        result.append( out )
        nr += 1
    return result
        
class EtreeHandler(mechanize.BaseHandler):
    def http_response(self, request, response):
        if not hasattr(response, "seek"):
            response = mechanize.response_seek_wrapper(response)
        # only use if response is html
        if response.info().dict.has_key('content-type') and ('html' in response.info().dict['content-type']):
            tag_soup = response.get_data()
            try:
                self.element = lxml.html.fromstring(tag_soup)
                ignore = lxml.etree.tostring(self.element, encoding=unicode) # check the unicode entity conversion has worked
            except (UnicodeDecodeError, lxml.etree.XMLSyntaxError):
                self.element = lxml.html.soupparser.fromstring(tag_soup) # fall back to beautiful soup if there is an error    
            response.set_data(lxml.etree.tostring(self.element, pretty_print=True, method="html"))      
        return response
        
class SoupHandler(mechanize.BaseHandler):
    def http_response(self, request, response):
        if not hasattr(response, "seek"):
            response = mechanize.response_seek_wrapper(response)
        # only use if response is html
        if response.info().dict.has_key('content-type') and ('html' in response.info().dict['content-type']):
            tags = response.get_data()
            soup = BeautifulSoup(tags)
            response.set_data(soup.prettify())      
        return response
        
# increment a date by a number OR to the next available weekday if a string
# return the start and end dates of the permissible range
def inc_dt(start_dt, increment=1):
    if not increment:
        increment = 0
    if isinstance(increment, int) or increment.isdigit() or (increment.startswith('-') and increment[1:].isdigit()):
        day_inc = int(increment)
        if day_inc < 0:
            end_dt = start_dt
            start_dt = end_dt + timedelta(days=day_inc)
        else:
            end_dt = start_dt + timedelta(days=day_inc)
    elif increment == 'Year':
        start_dt = date(start_dt.year, 1, 1) # first day of this year
        end_dt = date(start_dt.year, 12, 31) # last day of this year
    elif increment == 'Month': 
        start_dt = date(start_dt.year, start_dt.month, 1) # first day of this month
        if start_dt.month == 12:
            end_dt = date(start_dt.year+1, 1, 1) # first day of next year
        else:
            end_dt = date(start_dt.year, start_dt.month+1, 1) # first day of next month
        end_dt = end_dt - timedelta(days=1)
    elif increment.startswith('-'): 
        wday = WEEKDAYS.get(increment[1:4].capitalize(), 0) # supplied is a week day defining beginning of week for a weekly list
        day_inc = wday - start_dt.weekday()
        if day_inc > 0: 
            day_inc = day_inc - 7
        start_dt = start_dt + timedelta(days=day_inc)
        end_dt = start_dt + timedelta(days=6)
    else:
        wday = WEEKDAYS.get(increment[0:3].capitalize(), 6) # supplied is a week day defining end of week for a weekly list
        day_inc = wday - start_dt.weekday()
        if day_inc < 0:
            day_inc = day_inc + 7
        end_dt = start_dt + timedelta(days=day_inc)
        start_dt = end_dt - timedelta(days=6)
    return start_dt, end_dt



    

