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
try:
    from ukplanning import scrapemark
except ImportError:
    import scrapemark
#from .. import base
try:
    from ukplanning import scrapeutils
except ImportError:
    import scrapeutils
from datetime import date, timedelta
import urllib, urlparse 

from civica import CivicaScraper

class ErewashScraper(CivicaScraper):
    # different date selection mechanism from other Civicas

    data_start_target = '2003-08-01'
    batch_size = 21
    current_span = 21 # start this number of days ago when gathering current ids
    
    _authority_name = 'Erewash'
    _uid_num_sequence = True # uid is numeric sequence number not the local authority reference
    #_start_url = 'http://planportal.erewash.gov.uk/PlanningLive/_javascriptDetector_?goto=/PlanningLive/lg/GFPlanningSearch.page'
    #_search_url = 'https://myservice.erewash.gov.uk/PlanningLive/lg/plansearch.page?org.apache.shale.dialog.DIALOG_NAME=gfplanningsearch&Param=lg.Planning'
    _search_url = 'https://myservice.erewash.gov.uk/Planning/lg/GFPlanningWelcome.page'
    _search_page = 'plansearch.page'
    _handler = 'etree'
    
    #_date_from_field = 'ResponseDateFrom'
    #_date_to_field = 'ResponseDateTo'
    _date_from_field = 'ApplicationValidDateFrom'
    _date_to_field = 'ApplicationValidDateTo'
    _search_submit = '_id95:_id106'
    _ref_field = '_id95:KeyNo'
    _alt_ref_field = '_id95:LARef'
    _next_field = '_id98:scroll_1'
    _search_fields = {
        'org.apache.shale.dialog.DIALOG_NAME': 'gfplanningsearch',
        'Param': 'APP.Planning'
    }

    _scrape_data_block = """
    <div id="content"> {{ block|html }} </div>"
    """
    _scrape_min_data = """
    <table> Address Details <tr> UPRN </tr> {* <tr> <td /> <td> {{ [address] }} </td> </tr> *} <tr> Address Status </tr> </table>
    <table> <td> Web Search Reference </td> <td> {{ reference }} </td>
    <td> Application Description </td> <td> {{ description }} </td>
    <td> Received Date </td> <td> {{ date_received }} </td>
    </table>
    """
    detail_tests = [
        { 'uid': '0313/0070', 'len': 13 }, 
        { 'uid': '026273', 'len': 13 }, ] # same
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 12 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]

    def get_id_batch (self, date_from, date_to):
        
        if date_from == date_to: # note min 2 days, rejects same day requests
            date_to = date_to + timedelta(days=1) # increment end date by one day

        if self._start_url:
            response = self.br.open(self._start_url)
            #self.logger.debug("Start html: %s", response.read())

        current_day = date.today().weekday() 
        ref_date = date.today() - timedelta(days=current_day) # reference date is Monday (day 0) of the current week
        fields = {}
        fields.update(self._search_fields)
        fields [self._date_from_field] = "fw%+d" % (date_from - ref_date).days
        fields [self._date_to_field] = "fw%+d" % (date_to - ref_date).days
        self.logger.debug("Form fields: %s", str(fields))
        url = urlparse.urljoin(self._search_url, self._search_page)
        query_url = url + '?' + urllib.urlencode(fields)
        self.logger.debug("Query url: %s" % query_url)

        response = self.br.open(query_url)
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
        self.logger.debug("Max pages: %d" % max_pages)

        if max_pages >= 10: # 10 pages is the max, so if we hit it then split things up
            half_days = int((date_to - date_from).days / 2)
            mid_date = date_from + timedelta(days=half_days)
            result1 = self.get_id_batch(date_from, mid_date)
            result2 = self.get_id_batch(mid_date + timedelta(days=1), date_to)
            result1.extend(result2)
            return result1

        page_count = 1
        final_result = []
        while page_count <= max_pages:
            url = response.geturl()
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            else:
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
                break
            
        return final_result
        
    def _get_exact_html_from_uid (self, uid):
        if self._start_url:
            response = self.br.open(self._start_url)
        url = urlparse.urljoin(self._search_url, self._search_page)
        query_url = url + '?' + urllib.urlencode(self._search_fields)
        response = self.br.open(query_url) 
        #self.logger.debug("ID detail start html: %s", response.read())
        #self.logger.debug(scrapeutils.list_forms(self.br))
        fields = {}
        if uid.isdigit():
            fields[self._ref_field] = uid
        else:
            fields[self._alt_ref_field] = uid
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("Uid form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._search_submit)
        return self._get_html(response)

