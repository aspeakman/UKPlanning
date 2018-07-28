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
try:
    from ukplanning import scrapeutils
except ImportError:
    import scrapeutils
from .. import base
import urllib
from datetime import date, timedelta

class WAMScraper(base.DateScraper):

    min_id_goal = 200 # min target for application ids to fetch in one go
    batch_size = 60 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 32 # start this number of days ago when gathering current ids
    
    _scraper_type = 'WAM'
    _date_from_field = 'startDate'
    _date_to_field = 'endDate'
    _search_form = '2'
    _search_fields = {  }
    _scrape_ids = """
    <table id="searchresults"> <tr />
    {* <tr> <td />
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    <td /> <td> {{ [records].status }} </td>
    </tr> *}
    </table>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <body> {{ block|html }} </body>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <table id="casefilesummary">
    <tr> <th> Application No: </th> <td> {{ reference }} </td> </tr>
    <tr> <th> Date </th> <td> {{ date_validated }} </td> </tr>
    <tr> <th> Location: </th> <td> {{ address }} </td> </tr>
    <tr> <th> Development: </th> <td> {{ description }} </td> </tr>
    </table>"""
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [ ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s", response.read())
        
        new_date_to = date_to + timedelta(days=1) # end date is exclusive
        fields = {}
        fields.update(self._search_fields)
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = new_date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        
        if response:
            html = response.read()
            url = response.geturl()
            #self.logger.debug("ID batch page html: %s", html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            
        return final_result
            
    def get_html_from_uid(self, uid):
        url = self._applic_url + '&appNumber=' + urllib.quote_plus(uid)
        return self.get_html_from_url(url)

class HyndburnScraper(WAMScraper): # low numbers
    
    data_start_target = '2010-08-01'
    
    _authority_name = 'Hyndburn'
    _search_url = 'http://planning.hyndburnbc.gov.uk/WAM/searchsubmit/performOption.do?action=search&appType=Planning'
    _applic_url = 'http://planning.hyndburnbc.gov.uk/WAM/showCaseFile.do?action=show&appType=Planning'
    _scrape_data_block = """
    <div id="wam"> {{ block|html }} </div>
    """
    detail_tests = [
        { 'uid': '11/12/0134', 'len': 5 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 19 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]

class MonmouthshireScraper(WAMScraper): # note soon to be Idox

    data_start_target = '2006-11-25'
    
    _authority_name = 'Monmouthshire'
    _search_url = 'http://idox.monmouthshire.gov.uk/WAM/searchsubmit/performOption.do?action=search&appType=Planning'
    _applic_url = 'http://idox.monmouthshire.gov.uk/WAM/showCaseFile.do?action=show&appType=Planning'
    #_search_fields = { 'action2': 'Search', 'appType': 'Planning'  }
    _scrape_data_block = """
    <div id="content"> {{ block|html }} </div>
    """
    detail_tests = [
        { 'uid': 'DC/2012/00340', 'len': 5 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 72 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 4 } ]


