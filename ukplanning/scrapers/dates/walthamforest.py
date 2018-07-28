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
try:
    from ukplanning import scrapemark
except ImportError:
    import scrapemark
#from .. import base
try:
    from ukplanning import scrapeutils
except ImportError:
    import scrapeutils
from datetime import timedelta
import urllib, urlparse

# bug fix for SSL errno 8 on Waltham Forest
# http://stackoverflow.com/questions/11772847/error-urlopen-error-errno-8-ssl-c504-eof-occurred-in-violation-of-protoco
# forces the SSL connection to use TLSv1
import ssl
from functools import wraps
def sslwrap(func):
    @wraps(func)
    def bar(*args, **kw):
        kw['ssl_version'] = ssl.PROTOCOL_TLSv1
        return func(*args, **kw)
    return bar

ssl.wrap_socket = sslwrap(ssl.wrap_socket)

from civica import CivicaScraper
        
class WalthamForestScraper(CivicaScraper): 
    # note bad dates = 13th dec 2012 = returns too many pages (duplicates) - times out
    # also after 6th Dec 2015 -> A fatal error occurred
    
    min_id_goal = 100

    _authority_name = 'WalthamForest'
    _comment = 'was PlanningExplorer'
    _uid_num_sequence = True # uid is numeric sequence number not the local authority reference
    _start_url = 'https://planning.walthamforest.gov.uk/Planning/lg/GFPlanningWelcome.page?org.apache.shale.dialog.DIALOG_ID=7'
    _search_url = 'https://planning.walthamforest.gov.uk/Planning/lg/plansearch.page?org.apache.shale.dialog.DIALOG_NAME=gfplanningsearch&Param=APP.Planning'
    _search_page = 'GFPlanningSearch.page'
    _search_form = '1'
    _ref_search_form = '0'
    _next_form = '0'
    _date_from_field = '_id93:ReceivedDateFrom'
    _date_to_field = '_id93:ReceivedDateTo'
    _search_submit = '_id93:_id139'
    _ref_search_submit = '_id65:_id124'
    _ref_field = '_id65:KeyNo'
    _alt_ref_field = '_id65:LARef'
    _next_field = '_id70:scroll_1'
    _result_submit = '_id70:results:0:_id86'
    _scrape_state = """
        <input name="javax.faces.ViewState" value="{{ viewstate }}" />
        <input name="Civica.CSRFToken" value="{{ csrftoken }}" />
    """
    _query_fields = {
        '_id93_SUBMIT': '1',
        '_id93:_id139': 'Search'
    }

    _scrape_min_data = """
    <table title="Address Details"> UPRN {* <tr> <td /> <td> {{ [address] }} </td> </tr> *} Address Status </table>
    <table> <td> Application Id </td> <td> {{ reference }} </td>
    <td> Description </td> <td> {{ description }} </td>
    <td> Received Date </td> <td> {{ date_received }} </td> </table>
    """
    _scrape_invalid_format = "<span> No records found, {{ invalid_format }} re-enter search details </span>"
    detail_tests = [
        { 'uid': '111268', 'len': 10 },  # same as 2011/1234
        { 'uid': '2011/1234', 'len': 10 }, # same as 111268
        { 'uid': '142743', 'len': 8 }, # no LA Ref
        { 'uid': '2004/0991', 'len': 8 },  # multiples IDs, same as 040596
        { 'uid': '040596', 'len': 8 } ] 
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 69 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 8 } ]
        
    def get_id_batch (self, date_from, date_to):
        
        min_window = False
        if date_from == date_to: # note min 2 days, scraper rejects same day requests
            min_window = True
            date_to = date_to + timedelta(days=1)

        if self._start_url:
            response = self.br.open(self._start_url)
            #self.logger.debug("Start html: %s", response.read())
            
        response = self.br.open(self._search_url)
        html = response.read()
        url = response.geturl()
        st_result = scrapemark.scrape(self._scrape_state, html)
        #self.logger.debug("Search html: %s", html)

        fields = {}
        fields.update(self._query_fields)
        fields['javax.faces.ViewState'] = st_result.get('viewstate', '')
        fields['Civica.CSRFToken'] = st_result.get('csrftoken', '')
        fields [self._date_from_field] = date_from.strftime(self._request_date_format)
        fields [self._date_to_field] = date_to.strftime(self._request_date_format)
        #scrapeutils.setup_form(self.br, self._search_form, fields)
        #self.logger.debug("ID batch form: %s" % str(self.br.form))
        #response = scrapeutils.submit_form(self.br, self._search_submit)
        self.logger.debug("Form fields: %s", str(fields))
        url = urlparse.urljoin(url, self._search_page)
        response = self.br.open(url, urllib.urlencode(fields))
        html = response.read()

        #self.logger.debug("Batch html: %s" % html)
        try:
            result = scrapemark.scrape(self._scrape_max_pages, html)
            if isinstance(result['max_pages'], list):
                page_list = [ x for x in result['max_pages'] if x ]
            else:
                page_list = result['max_pages'].split()
            max_pages = int(page_list[-1]) # take the last value
        except:
            max_pages = 1
        self.logger.debug("max pages: %d" % max_pages)

        if self._page_limit and max_pages >= self._page_limit: # limit of 10 pages is the max, so if we hit it then split things up
            if not min_window:
                half_days = int((date_to - date_from).days / 2)
                mid_date = date_from + timedelta(days=half_days)
                result1 = self.get_id_batch(date_from, mid_date)
                result2 = self.get_id_batch(mid_date + timedelta(days=1), date_to)
                result1.extend(result2)
                return result1
            else:
                self.logger.warning("Max %d pages returned on %s - probable missed data" % (self._page_limit, date_from.isoformat()))

        #self.logger.debug(scrapeutils.list_forms(self.br))
        
        page_count = 1
        final_result = []
        while page_count <= max_pages:
            url = response.geturl()
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            else:
                self.logger.debug("Empty result after %d pages", page_count)
                break
            page_count += 1
            if page_count > max_pages:
                break
            try:
                fields = { self._next_field: 'next' }
                scrapeutils.setup_form(self.br, self._next_form, fields)
                self.logger.debug("Next page form: %s" % str(self.br.form))
                response = scrapeutils.submit_form(self.br)
                html = response.read()
            except:
                self.logger.debug("No next form after %d pages", page_count)
                break
            
        return final_result
        
    def get_html_from_uid (self, uid):
        if self._start_url:
            response = self.br.open(self._start_url)
        response = self.br.open(self._search_url)
        #self.logger.debug("search html: %s", response.read())
        #self.logger.debug(scrapeutils.list_forms(self.br))
        fields = {}
        fields.update(self._search_fields)
        if uid.isdigit():
            fields[self._ref_field] = uid
        else:
            fields[self._alt_ref_field] = uid
        scrapeutils.setup_form(self.br, self._ref_search_form, fields)
        #self.logger.debug("Uid form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._ref_search_submit)
        html, url = self._get_html(response)
        # note return here can be a single uid match page OR list of multiple matches
        result = scrapemark.scrape(self._scrape_ids, html, url)
        if result and result.get('records'):
            self._clean_ids(result['records'])
            if len(result['records']) >= 1:
                fields = {}
                fields.update(self._search_fields)
                scrapeutils.setup_form(self.br, self._ref_search_form, fields)
                #self.logger.debug("Uid form: %s", str(self.br.form))
                response = scrapeutils.submit_form(self.br, self._result_submit)
                return self._get_html(response)
            return None, None
        else:
            return html, url
    
    """def _get_details(self, html, this_url):
        "" Scrapes detailed information for one record given html and url 
        - this is an optional hook to allow data from multiple linked pages to be merged ""
        result = self._get_detail(html, this_url)
        if 'scrape_error' in result or not result.get('uid'):
            return result
        if result.get('reference'):
            if result['uid'] <> result['reference'] and result['uid'].isdigit(): 
                temp = result['uid'] # swap identifiers
                result['uid'] = result['reference']
                result['reference'] = temp
        else:
            result['reference'] = result['uid']
        return result"""



    




