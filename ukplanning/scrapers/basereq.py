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
import base
import requests
import urlparse

# note basereq adapts the base class to use the requests/urllib3 libraries (not mechanize/urllib2)
# so there is no built in html massaging using _handler and etree/beautifulsoup

class BaseReqScraper(base.BaseScraper):
    
    def __init__(self, *args, **kwargs):
        super(BaseReqScraper, self).__init__(*args, **kwargs)
        self.br = None
        self.rs = requests.Session()
        self.rs.cookies = self.cj
        if self._headers:
            self.rs.headers.update(self._headers)

    def get_html_from_url(self, url):
        """ Get the html and url for one record given a URL """
        if self._uid_only:
            return None, None
        if self._search_url and self._detail_page:
            url_parts = urlparse.urlsplit(url)
            url = urlparse.urljoin(self._search_url, self._detail_page)
            if url_parts.query:
                url = url + '?' + url_parts.query
        response = self.rs.get(url, timeout=self._timeout) 
        return self._get_html(response)

    def _get_html(self, response):
        """ Return HTML and URL given the website response """
        return response.text, response.url

class DateReqScraper(BaseReqScraper, base.DateScraper):
    
    _base_type = 'DateReqScraper'
    
    def __init__(self, *args, **kwargs):
        super(DateReqScraper, self).__init__(*args, **kwargs)

class PeriodReqScraper(BaseReqScraper, base.PeriodScraper):
    
    _base_type = 'PeriodReqScraper'
    
    def __init__(self, *args, **kwargs):
        super(PeriodReqScraper, self).__init__(*args, **kwargs)

class ListReqScraper(BaseReqScraper, base.ListScraper):
    
    _base_type = 'ListReqScraper'
    
    def __init__(self, *args, **kwargs):
        super(ListReqScraper, self).__init__(*args, **kwargs)
        
import ssl
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
class Ssl3HttpAdapter(HTTPAdapter):
    #optional requests Transport adapter that allows a scraper to force use of insecure SSLv3.

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections,
                                       maxsize=maxsize,
                                       block=block,
                                       ssl_version=ssl.PROTOCOL_SSLv3)
    