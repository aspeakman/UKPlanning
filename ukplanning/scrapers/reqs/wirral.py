#!/usr/bin/env python
"""Copyright (C) 2013-2017  Andrew Speakman

This file is part of UKPlanning, a library of scrapers for UK planning applications

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>."""
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
import ssl
import requests

# bug fix for SSL EOF error on Wirral site
# see https://lukasa.co.uk/2013/01/Choosing_SSL_Version_In_Requests/
# with mechanize -> urlopen error EOF occurred in violation of protocol (_ssl.c:590)
# with requests -> "bad handshake: SysCallError(-1, 'Unexpected EOF')"
# this fix forces the SSL connection to use TLSv1 which is the only SSL protocol the site accepts
# https://www.ssllabs.com/ssltest/analyze.html?d=planning.wirral.gov.uk

class TLSv1Adapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections,
                                       maxsize=maxsize,
                                       block=block,
                                       ssl_version=ssl.PROTOCOL_TLSv1)

from idoxreq import IdoxReqEndExcScraper

class WirralScraper(IdoxReqEndExcScraper): 

    _search_url = 'https://planning.wirral.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Wirral'
    _disabled = False
    _comment = 'was AcolNet'
    detail_tests = [
        { 'uid': 'APP/11/00960', 'len': 27 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 34 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 4 } ]
        
    def __init__(self, *args, **kwargs):
        super(WirralScraper, self).__init__(*args, **kwargs)
        self.rs.mount('https://', TLSv1Adapter())

""" note this method of forcing TLSv1 does not seem to work
import ssl
from functools import wraps
def sslwrap(func):
    @wraps(func)
    def bar(*args, **kw):
        kw['ssl_version'] = ssl.PROTOCOL_TLSv1
        return func(*args, **kw)
    return bar

ssl.wrap_socket = sslwrap(ssl.wrap_socket)

from idox import IdoxEndExcScraper
        
class WirralScraper(IdoxEndExcScraper): # not working EOF error

"""
