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
from datetime import date
try:
    from ukplanning import scrapemark
except ImportError:
    import scrapemark
try:
    from ukplanning import scrapeutils
except ImportError:
    import scrapeutils
from .. import base
import re
import urllib

# SouthOxfordshireScraper and Vale of White Horse

class OxonScraper(base.DateScraper):

    min_id_goal = 300 # min target for application ids to fetch in one go
    
    _scraper_type = 'Oxon'
    _date_from_field = { 'day': 'SDAY', 'month': 'SMONTH', 'year': 'SYEAR', }
    _date_to_field = { 'day': 'EDAY', 'month': 'EMONTH', 'year': 'EYEAR', }
    _ref_query = 'MODULE=ApplicationDetails&REF='
    _default_timeout = 30 # server times out sometimes, especially early morning
    _search_fields = {
        'MODULE': 'ApplicationCriteriaList',
        'TYPE': 'Application',
        'PARISH': 'ALL',
        'AREA': 'A',
        'APPTYPE': 'ALL',
        'Submit': 'Search' }
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <h1> Planning Application Details </h1> {{ block|html }} <div id="footer" />
    """
    _scrape_ids = """
    <h1> Planning Application Register </h1> <div class="rowdiv" />
    {* <div class="rowdiv">
       <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a>
    </div> *}
    <div id="footer" />
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <div class="tableheader"> {{ reference }} <img /> </div>
    <div class="leftcelldiv"> Description </div> <div> {{ description }} </div>
    <div class="leftcelldiv"> Location </div> <div> {{ address }} </div>
    <div class="listrowdiv"> Date Received {{ date_received }} </div>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<div class="leftcelldiv"> Grid Reference </div> <div> {{ easting }} / {{ northing }}</div>',
    '<div class="leftcelldiv"> Case Officer </div> <div> {{ case_officer }} <br /> </div>',
    '<div class="leftcelldiv"> Application Type </div> <div> {{ application_type }} </div>',
    '<div class="leftcelldiv"> Decision </div> <div> {{ decision }} </div>',
    '<div class="leftcelldiv"> Appeal </div> <div> {{ appeal_status }} </div>',
    '<div class="leftcelldiv"> Agent </div> <div> <pre> {{ applicant_name }} </pre> </div>',
    '<div class="leftcelldiv"> Applicant </div> <div> <pre> {{ agent_name }} </pre> </div>',  
    '<div class="listrowdiv"> Registration Date {{ date_validated }} </div>',
    '<div class="listrowdiv"> Start Consultation Period {{ consultation_start_date }} </div>',
    '<div class="listrowdiv"> End Consultation Period {{ consultation_end_date }} </div>',
    '<div class="listrowdiv"> Target Decision Date {{ target_decision_date }} </div>',
    ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        
        fields = {}
        fields.update(self._search_fields)
        date_from = date_from.strftime(self._request_date_format)
        date_parts = date_from.split('/')
        fields[self._date_from_field['day']] = date_parts[0]
        fields[self._date_from_field['month']] = date_parts[1]
        fields[self._date_from_field['year']] = date_parts[2]
        date_to = date_to.strftime(self._request_date_format)
        date_parts = date_to.split('/')
        fields[self._date_to_field['day']] = date_parts[0]
        fields[self._date_to_field['month']] = date_parts[1]
        fields[self._date_to_field['year']] = date_parts[2]
        self.logger.debug("Fields: %s", str(fields))
        query = urllib.urlencode(fields)
        url = self._result_url + '?' + query
        response = self.br.open(url)
        
        if response:
            html = response.read() 
            url = response.geturl()
            #self.logger.debug("Batch html: %s" % html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
                    
        return final_result

    def get_html_from_uid (self, uid):
        url = self._result_url + "?" + self._ref_query + urllib.quote_plus(uid)
        return self.get_html_from_url(url)

class SouthOxfordshireScraper(OxonScraper): # note website shuts in early hours

    _authority_name = 'SouthOxfordshire'
    _search_url = 'http://www.southoxon.gov.uk/ccm/support/Main.jsp?MODULE=ApplicationCriteria&TYPE=Application'
    _result_url = 'http://www.southoxon.gov.uk/ccm/support/Main.jsp'
    
    detail_tests = [
        { 'uid': 'P12/S1613/FUL', 'len': 17 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 47 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 12 } ]

class WhiteHorseScraper(OxonScraper):

    _authority_name = 'WhiteHorse'
    _search_url = 'http://www.whitehorsedc.gov.uk/java/support/Main.jsp?MODULE=ApplicationCriteria&TYPE=Application'
    _result_url = 'http://www.whitehorsedc.gov.uk/java/support/Main.jsp'
    timeout = 30

    detail_tests = [
        { 'uid': 'P12/V1640/FUL', 'len': 17 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 39 }, 
        { 'from': '03/08/2012', 'to': '03/08/2012', 'len': 11 } ]


