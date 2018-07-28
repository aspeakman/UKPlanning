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
from datetime import datetime

class WestDunbartonshireScraper(base.DateScraper):

    data_start_target = '2002-10-01'
    min_id_goal = 200 # min target for application ids to fetch in one go
    batch_size = 28 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 28 # start this number of days ago when gathering current ids
    
    _authority_name = 'WestDunbartonshire'
    _handler = 'etree'
    _search_url = 'http://www.west-dunbarton.gov.uk/uniform/dcsearch_app.asp'
    _applic_url = 'http://www.west-dunbarton.gov.uk/uniform/dcdisplayfull.asp?vPassword=&View1=View&vUPRN='
    _date_from_field = 'vDateRcvFr'
    _date_to_field = 'vDateRcvTo'
    _search_form = 'publicdisplay'
    _scrape_ids = """
    <h3> Property Search Results </h3>
    {* <table> <tr>
    <td /> <td> {{ [records].uid }} </td>
    </tr> </table> *}
    </div>
    """
    _scrape_data_block = """
    <div class="document"> {{ block|html }} </div>
    """
    _scrape_min_data = """
    <tr> <td> Reference Number </td> <td> {{ reference }} </td> </tr>
    <tr> <td> Address </td> <td> {{ address }} </td> </tr>
    <tr> <td> Proposal </td> <td> {{ description }} </td> </tr>
    <tr> <td> Date Received </td> <td> {{ date_received }} </td> </tr>
    <tr> <td> Date Valid </td> <td> {{ date_validated }} </td> </tr>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<tr> <td> Status </td> <td> {{ status }} </td> </tr>',
    '<tr> <td> Type of Application </td> <td> {{ application_type }} </td> </tr>',
    '<tr> <td> Development Type </td> <td> {{ development_type }} </td> </tr>',
    '<tr> <td> Officer </td> <td> {{ case_officer }} </td> </tr>',
    '<tr> <td> Decision Date </td> <td> {{ decision_date }} </td> </tr>',
    '<tr> <td> Committee Date </td> <td> {{ meeting_date }} </td> </tr>',
    '<tr> <td> Appeal Status </td> <td> {{ appeal_status }} </td> </tr>',
    '<tr> <td> Applicant Name </td> <td> {{ applicant_name }} </td> </tr>',
    '<tr> <td> Applicant Address </td> <td> {{ applicant_address }} </td> </tr>',
    '<tr> <td> Agent Name </td> <td> {{ agent_name }} </td> </tr>',
    '<tr> <td> Agent Address </td> <td> {{ agent_address }} </td> </tr>',
    '<tr> <td> Ward </td> <td> {{ ward_name }} </td> </tr>',
    '<tr> <td> Parish </td> <td> {{ parish }} </td> </tr>',
    ]
    detail_tests = [
        { 'uid': 'DC11/199', 'len': 17 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 10 }, 
        { 'from': '23/08/2012', 'to': '23/08/2012', 'len': 1 } ]
        
    # unavailable 3 am to 5 am
    @classmethod
    def can_run(cls):
        now = datetime.now()
        if now.hour >= 2 and now.hour <= 6:
            return False
        else:
            return True

    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s" % response.read())
        
        fields = {}
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        
        if response:
            html = response.read()
            url = response.geturl()
            #self.logger.debug("Batch html: %s" % html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                for rec in result['records']:
                    rec['url'] = self._applic_url + urllib.quote_plus(rec['uid'])
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            
        return final_result

    def get_html_from_uid(self, uid): 
        url =  self._applic_url + urllib.quote_plus(uid)
        return self.get_html_from_url(url) 

        

