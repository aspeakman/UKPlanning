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
#from .. import base
import urllib, urlparse
from datetime import date
from annuallist import AnnualListScraper

# also see WeeklyWAMScraper PeriodScraper version
# no good = covers last 4-8 weeks only

# works from the sequence of application numbers (in YY/P/NNNN format)

class NorthSomersetScraper(AnnualListScraper):

    min_id_goal = 90 # min target for application ids to fetch in one go
    batch_size = 30 # batch size for each scrape - number of applications requested to produce at least one result each time
    current_span = 30 # min number of records to get when gathering current ids
    data_start_target = 20000001
    
    _disabled = False
    _authority_name = 'NorthSomerset'
    _max_index = 3100 # maximum records per year
    _search_url = 'http://wam.n-somerset.gov.uk/MULTIWAM/searchsubmit/performOption.do?action=search&appType=planning'
    _handler = 'etree'
    _applic_url = 'http://wam.n-somerset.gov.uk/MULTIWAM/findCaseFile.do'
    _scrape_invalid_format = '<h2> Summary </h2> ERROR: Unable to find {{ invalid_format }} file <h2 />'
    _scrape_invalid_format2 = '<span class="errortext"> No matching case {{ invalid_format }} were found'
    
    _scrape_ids = """
    <table id="searchresults"> <tr />
    {* <tr> <td />
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    </tr> *}
    </table>
    """
    
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <h2> Summary </h2> {{ block|html }} <h2> Documents </h2>
    """
    _scrape_min_data = """
    <tr> <td> Development </td> <td> {{ description }} </td> </tr>
    <tr> <td> Location </td> <td> {{ address }} </td> </tr>
    <tr> <td> Application </td> <td> {{ reference }} </td> </tr>
    """
    _scrape_optional_data = [
    '<tr> <td> Application Type </td> <td> {{ application_type }} </td> </tr>',
    '<tr> <td> Date Received </td> <td> {{ date_received }} </td> </tr>',
    '<tr> <td> Valid Date </td> <td> {{ date_validated }} </td> </tr>',
    '<tr> <td> Parish </td> <td> {{ parish }} </td> </tr>',
    '<tr> <td> Decision Date </td> <td> {{ decision_date }} </td> </tr> Case Officer',
    '<tr> <td> Decision Date </td> <td> {{ decision_date }} </td> </tr> Parish',
    '<tr> <td> Case Officer </td> <td> {{ case_officer }} </td> </tr>',
    '<tr> <td> Decision </td> <td> {{ decision }} </td> Appeal Reference </tr>',
    '<tr> <td> Applicant: </td> <td> {{ applicant_name }} <br> {{ applicant_address|html }} </td> </tr>',
    '<tr> <td> Agent: </td> <td> {{ agent_name }} <br> {{ agent_address|html }} </td> </tr>',
    '<tr> <td> Application Status </td> <td> {{ status }} </td> </tr>',
    '<tr> <td> Consultation Expiry Date </td> <td> {{ consultation_end_date }} </td> </tr>',
    """<tr> <td> Target Date </td> <td> {{ target_decision_date }} </td>
    <td> Target Date for Public Consultations </td> <td> {{ consultation_end_date }} </td> </tr>""",
    '<tr> <td> Appeal Decision Date </td> <td> {{ appeal_decision_date }} </td> </tr>',
    '<p id="comment"> <a href="{{ comment_url|abs }}" /> </p>',
    ]
    detail_tests = [
        { 'uid': '12/P/0645/F', 'len': 12 },
        { 'uid': '20120645', 'len': 12 } ]
    batch_tests = [    
        { 'from': '20163099', 'to': '20163188', 'len': 81 },
        { 'from': '20120506', 'to': '20120516', 'len': 11 },
        { 'from': '20119998', 'to': '20120008', 'len': 8 }, ]
        #{ 'from': '20123090', 'to': '20123110', 'len': 10 }, ]
        
    def get_uid(self, index, year):
        # create a uid from year and index integer values
        uid = str(year)[2:4] + '/P/' + str(index).zfill(self._index_digits)
        return uid  
        
    def get_html_from_uid(self, uid):
        if uid.isdigit() and int(uid) > self.data_start_target: 
            uid = str(uid)[2:4] + '/P/' + str(uid)[4:8]
        url = self._applic_url + '?action=Search&appType=planning&appNumber=' + urllib.quote_plus(uid)
        html, url = self.get_html_from_url(url)
        result = scrapemark.scrape(self._scrape_ids, html, url)
        if len(uid) >= 9 and result and result.get('records'):
            self._clean_ids(result['records'])
            for r in result['records']:
                if r.get('uid', '').startswith(uid) and r.get('url'):
                    self.logger.debug("Scraped url: %s" % r['url'])
                    return self.get_html_from_url(r['url'])
            return None, None
        else:
            return html, url

