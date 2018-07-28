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
from .. import base
try:
    from ukplanning import scrapeutils
except ImportError:
    import scrapeutils
import urllib, urlparse
from datetime import timedelta

class WestLindseyScraper(base.DateScraper):

    min_id_goal = 150 # min target for application ids to fetch in one go
    batch_size = 28 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 28 # start this number of days ago when gathering current ids
    
    _authority_name = 'WestLindsey'
    _search_url = 'https://www.west-lindsey.gov.uk/my-services/planning-and-building/view-applications-decisions-and-appeals/search-our-planning-application-database/'
    _iframe_url = 'https://planning.west-lindsey.gov.uk/planning/index-iframe.asp'
    _detail_page = 'details-iframe.asp'
    _results_page = 'results-iframe.asp'
    _handler = 'etree'
    """_date_from_field = {
        'day': 'StartDay',
        'month': 'StartMonth',
        'year': 'StartYear',
        }
    _date_to_field = {
        'day': 'EndDay',
        'month': 'EndMonth',
        'year': 'EndYear',
        }"""
    _date_from_field = 'fromdate'
    _date_to_field = 'todate'
    _search_fields = { 'wardid': 'ALL', 'areaid': 'ALL' }
    _request_date_format = '%Y-%m-%d'
    #_search_form = '1'
    _scrape_ids = """
    <ul id='results-list'>
    {* <a href='{{ [records].url|abs }}'> <div class='col1'> {{ [records].uid }} </div> </a>  *}
    </ul>
    """
    _scrape_data_block = """
    <div id="content"> {{ block|html }} </div>
    """
    _scrape_min_data = """
    <div class="detailFull> <strong> Application Number: </strong> {{ reference }} </div>
    <div class="detailCol> <strong> Application date: </strong> {{ date_validated }} </div>
    <div class="detailCol> <strong> Description of proposal: </strong> {{ description }} </div>
    <div class="detailCol> <strong> Location of proposal: </strong> {{ address }} </div>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<div class="detailCol> <strong> Planning officer: </strong> {{ case_officer }} </div>',
    '<div class="detailCol> <strong> Applicant Name: </strong> {{ applicant_name }} <br> </div>',
    '<div class="detailCol> <strong> Ward: </strong> {{ ward_name }} <br> </div>',
    '<div class="detailCol> <strong> Parish: </strong> {{ parish }} <br> </div>',
    '<div class="detailCol> <strong> Status: </strong> {{ status }} </div>',
    '<div class="detailCol> <strong> Agent Name: </strong> {{ agent_name }} <br>',
    '<div class="detailCol> <strong> Agent Address: </strong> {{ agent_address }} </div>',
    """<div class="detailCol> <strong> Date of Decision: </strong> {{ decision_date }} </div>
    <div class="detailCol> <strong> Decision: </strong> {{ decision }} </div>""",
    '<div class="detailCol> <strong> Appeal Date: </strong> {{ appeal_date }} </div>',
    '<div class="detailCol> <strong> Appeal Result: </strong> {{ appeal_result }} </div>',
    ]
    detail_tests = [
        { 'uid': '127688', 'len': 13 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '24/09/2012', 'len': 31 }, 
        { 'from': '22/08/2012', 'to': '22/08/2012', 'len': 2 } ]

    
    def get_id_batch (self, date_from, date_to):
        
        final_result = []
        new_date_to = date_to + timedelta(days=1) # end date is exclusive, increment end date by one day

        fields = {}
        fields.update(self._search_fields)
        fields [self._date_from_field] = date_from.strftime(self._request_date_format)
        fields [self._date_to_field] = new_date_to.strftime(self._request_date_format)
        
        self.logger.debug("Fields: %s", str(fields))
        query = urllib.urlencode(fields)
        url = urlparse.urljoin(self._iframe_url, self._results_page)
        response = self.br.open(url, query)
        
        if response:
            html = response.read() 
            url = response.geturl()
            #self.logger.debug("Batch html: %s" % html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                self._clean_ids(result['records'])
                for res in result['records']:
                    if res.get('uid'): # sometimes there are blank uids eg 18/3/15
                        final_result.append(res)
        return final_result
        
    # post process a set of uid/url records: sets URL
    def _clean_record(self, record):
        super(WestLindseyScraper, self)._clean_record(record)
        if record.get('uid') and not record.get('url'):
            record['url'] = urlparse.urljoin(self._iframe_url, self._detail_page) + '?id=' + urllib.quote_plus(record['uid'])

    def get_html_from_uid(self, uid):
        url = urlparse.urljoin(self._iframe_url, self._detail_page) + '?id=' + urllib.quote_plus(uid)
        return self.get_html_from_url(url)
        
    def get_html_from_url(self, url):
        """ Get the html and url for one record given a URL """
        if self._uid_only:
            return None, None
        if self._iframe_url and self._detail_page:
            url_parts = urlparse.urlsplit(url)
            url = urlparse.urljoin(self._iframe_url, self._detail_page)
            if url_parts.query:
                url = url + '?' + url_parts.query
        response = self.br.open(url) # use mechanize, to get same handler interface as elsewhere
        return self._get_html(response)
        
