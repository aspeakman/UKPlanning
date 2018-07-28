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
import urllib, urlparse
from datetime import datetime

class ColchesterScraper(base.PeriodScraper): # was WeeklyWAM scraper type, now only one in effect

    min_id_goal = 300 # min target for application ids to fetch in one go

    _authority_name = 'Colchester'
    _search_url = 'http://www.planning.colchester.gov.uk/WAM/weeklyApplications.do'

    _handler = 'etree'
    _detail_page = 'showCaseFile.do'
    _period_type = 'Sunday'
    _date_field = 'endDate'
    _request_date_format = '%s'
    _query_fields = {  "areaCode": "%", "sortOrder": "3", "applicationType": "%", "Button": "Search", 'action': 'showWeeklyList', 'category': 'planning'  }
    _scrape_ids = """
    <table id="searchresults"> <tr />
    {* <tr> <td />
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    <td /> <td> {{ [records].status }} </td>
    </tr> *}
    </table>
    """
    _next_page_link = '[Next >>]'
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <td id="content"> {{ block|html }} </td>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <table id="casefilesummary">
    <tr> <td id="applicationumbervalue"> {{ reference }} </td> </tr>
    <tr> <th> Development: </th> <td> {{ description }} </td> </tr>
    <tr> <th> Site Address: </th> <td> {{ address }} </td> </tr>
    <tr>
         <th> Date Received: </th> <td> {{ date_received }} </td>
         <th> Registration Date: </th> <td> {{ date_validated }} </td>
    </tr>
    </table>"""
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<tr> <th> Applicant: </th> <td> {{ applicant_name }} </td> </tr>',
    '<tr> <th> Agent: </th> <td> {{ agent_name }} </td> </tr>',
    '<tr> <th> Consultation Expiry Date: </th> <td> {{ consultation_end_date }} </td> </tr>',
    '<tr> <th> CBC Decision Date: </th> <td> {{ decision_date }} </td> </tr>',
    '<tr> <th> Target Date: </th> <td> {{ target_decision_date }} </td> </tr>',
    '<tr> <th> Application Type: </th> <td> {{ application_type }} </td> </tr>',
    '<p id="comment"> <a href="{{ comment_url|abs }}" /> </p>',
    '<tr> <th> Application Status: </th> <td> {{ status }} </td> </tr>',
    '<tr> <th> UPRN: </th> <td> {{ uprn }} </td> </tr>',
    '<tr> <th> Parish: </th> <td> {{ parish }} </td> </tr>',
    '<tr> <th> Ward: </th> <td> {{ ward_name }} </td> </tr>',
    '<tr> <th> Decision Type: </th> <td> {{ decision }} </td> </tr>',
    '<tr> <th> Case Officer: </th> <td> {{ case_officer }} </td> </tr>',
    '<tr> <th> Appeal Start Date: </th> <td> {{ appeal_date }} </td> </tr>',
    '<tr> <th> Appeal Determination Date: </th> <td> {{ appeal_decision_date }} </td> </tr>',
    '<tr> <th> Appeal Decision: </th> <td> {{ appeal_result }} </td> </tr>',
    ]
    detail_tests = [
        { 'uid': '120697', 'len': 17 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'date': '18/10/2014', 'len': 37 }, 
        { 'date': '13/08/2012', 'len': 25 } ]

    def get_id_period (self, this_date):

        final_result = []
        from_dt, to_dt = scrapeutils.inc_dt(this_date, self._period_type)
        timestamp = (datetime(to_dt.year, to_dt.month, to_dt.day) - datetime(1970,1,1)).total_seconds()
        self.logger.debug("Timestamp: %f" % timestamp)
        fields = {}
        fields.update(self._query_fields)
        fields [self._date_field] = str(int(timestamp*1000))
        response = self.br.open(self._search_url, urllib.urlencode(fields))
            
        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        while response and page_count < max_pages:
            html = response.read()
            url = response.geturl()
            #self.logger.debug("ID batch page html: %s", html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                page_count += 1
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            else:
                self.logger.debug("Empty result after %d pages", page_count)
                break # note weekly result allowed to be legitimately empty (for example in the current week)
            try:
                response = self.br.follow_link(text=self._next_page_link)
            except:
                self.logger.debug("No next link after %d pages", page_count)
                break
                
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
        
        return final_result, from_dt, to_dt # weekly scraper - so empty result can be valid

    def get_html_from_uid (self, uid):
        url = urlparse.urljoin(self._search_url, self._detail_page) + '?action=show&appType=Planning&appNumber=' + urllib.quote_plus(uid)
        return self.get_html_from_url(url)
      
"""    _scrape_data_block = ""
    <body> {{ block|html }} </body>
    ""
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = ""
    <table id="casefilesummary">
    <tr> <th id="development" /> <td> {{ description }} </td> </tr>
    <tr> <th id="location" /> <td> {{ address }} </td> </tr>
    <tr> <th id="appno" /> <td> {{ reference }} </td>
         <th id="regdate" /> <td> {{ date_validated }} </td>
    </tr>
    </table>""
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<tr> <th id="applicant" /> <td> {{ applicant_name }} <br> {{ applicant_address }} </td> </tr>',
    '<tr> <th id="agent" /> <td> {{ agent_name }} <br> {{ agent_address }} </td> </tr>',
    '<tr> <th id="dateconsultend" /> <td> {{ consultation_end_date }} </td> </tr>',
    '<tr> <th id="dateconsultstart" /> <td> {{ consultation_start_date }} </td> </tr>',
    '<tr> <th id="caseofficer" /> <td> {{ case_officer }} </td> </tr>',
    '<tr> <th id="decdate" /> <td> {{ decision_date }} </td> </tr>',
    '<tr> <th id="apptype" /> <td> {{ application_type }} </td> </tr>',
    '<p id="comment"> <a href="{{ comment_url|abs }}" /> </p>',
    '<tr> <th id="parish" /> <td> {{ ward_name }} </td> </tr>',
    '<tr> <th id="dectype" /> <td> {{ decision }} </td> </tr>',
    ]
"""

"""class DartmoorScraper(WeeklyWAMScraper): 

    _authority_name = 'Dartmoor'
    _disabled = False
    _search_url = 'http://www2.dartmoor-npa.gov.uk/WAM/weeklyApplications.do'
    _scrape_ids = ""
    <body>
    {* <p id="viewApplication"> <a href="{{ [records].url|abs }}"> </a> </p>
    <table class="searchresult">
    <tr> Application Number: {{ [records].uid }} </tr>
    <tr> District: {{ [records].district }} </tr>
    <tr> Parish: {{ [records].parish }} </tr>
    <tr> Grid Reference: {{ [records].os_grid_ref }} </tr> 
    <tr> Application Type: {{ [records].application_type }} </tr> 
    </table> *}
    </body>
    ""
    _scrape_min_data = ""
    <table id="casefilesummary">
    <tr> <th id="apptype" /> <td> {{ reference }} </td> </tr>
    <tr> <th id="development" /> <td> {{ description }} </td> </tr>
    <tr> <th id="location" /> <td> {{ address }} </td> </tr>
    </table>""
    _scrape_optional_data = [
    '<tr> <th id="applname" /> <td> {{ applicant_name }} </td> </tr>',
    '<tr> <th id="status" /> <td> {{ status }} </td> </tr>',
    ""<tr> <th id="datereceived" /> </tr> <tr> <td> {{ date_received }} </td> <td> {{ date_validated }} </td> 
    <td> {{ consultation_start_date }} </td> <td> {{ consultation_end_date }} </td> </tr>"",
    '<tr> <th id="caseofficer" /> <td> <a> {{ case_officer }} </a> </td> </tr>',
    '<tr> <th id="targetdecision" /> </tr> <tr> <td> {{ target_decision_date }} </td> <td> {{ decision_date }} </td> <td> {{ decision }} </td> </tr>',
    '<p id="comment"> <a href="{{ comment_url|abs }}" /> </p>',
    ]
    detail_tests = [
        { 'uid': '0045/13', 'len': 14 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'date': '05/02/2015', 'len': 2 }, 
        { 'date': '12/02/2012', 'len': 43 }
    ]

    def get_id_period (self, this_date):

        final_result = []
        from_dt, to_dt = scrapeutils.inc_dt(this_date, self._period_type)
        timestamp = (datetime(to_dt.year, to_dt.month, to_dt.day) - datetime(1970,1,1)).total_seconds()
        self.logger.debug("Timestamp: %f" % timestamp)
        fields = {}
        fields.update(self._query_fields)
        fields [self._date_field] = str(int(timestamp*1000))
        response = self.br.open(self._search_url, urllib.urlencode(fields))
        if not response:
            return [], None, None
            
        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        while response and page_count < max_pages:
            html = response.read()
            url = response.geturl()
            #self.logger.debug("ID batch page html: %s", html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                page_count += 1
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            #else:
            #    return [], None, None # note weekly result allowed to be empty as numbers are low
            try:
                response = self.br.follow_link(text=self._next_page_link)
            except:
                self.logger.debug("No next link after %d pages", page_count)
                break
                
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
        
        return final_result, from_dt, to_dt"""

"""class NorthSomersetScraper(WeeklyWAMScraper): 

    _authority_name = 'NorthSomerset'
    _disabled = False
    _search_url = 'http://wam.n-somerset.gov.uk/MULTIWAM/weeklyApplications.do'
    _scrape_data_block = ""
    <h2> Summary </h2> {{ block|html }} <h2> Documents </h2>
    ""
    _scrape_min_data = ""
    <tr> <td> Development </td> <td> {{ description }} </td> </tr>
    <tr> <td> Location </td> <td> {{ address }} </td> </tr>
    <tr> <td> Application </td> <td> {{ reference }} </td> </tr>
    ""
    _scrape_optional_data = [
    '<tr> <td> Application Type </td> <td> {{ application_type }} </td> </tr>',
    '<tr> <td> Date Received </td> <td> {{ date_received }} </td> </tr>',
    '<tr> <td> Valid Date </td> <td> {{ date_validated }} </td> </tr>',
    '<tr> <td> Parish </td> <td> {{ parish }} </td> </tr>',
    '<tr> <td> Decision Date </td> <td> {{ decision_date }} </td> </tr> Case Officer',
    '<tr> <td> Case Officer </td> <td> {{ case_officer }} </td> </tr>',
    '<tr> <td> Decision </td> <td> {{ decision }} </td> Appeal Reference </tr>',
    '<tr> <td> Applicant: </td> <td> {{ applicant_name }} <br> {{ applicant_address|html }} </td> </tr>',
    '<tr> <td> Agent: </td> <td> {{ agent_name }} <br> {{ agent_address|html }} </td> </tr>',
    '<tr> <td> Application Status </td> <td> {{ status }} </td> </tr>',
    '<tr> <td> Consultation Expiry Date </td> <td> {{ consultation_end_date }} </td> </tr>',
    ""<tr> <td> Target Date </td> <td> {{ target_decision_date }} </td>
    <td> Target Date for Public Consultations </td> <td> {{ consultation_end_date }} </td> </tr>"",
    '<tr> <td> Appeal Decision Date </td> <td> {{ appeal_decision_date }} </td> </tr>',
    '<p id="comment"> <a href="{{ comment_url|abs }}" /> </p>',
    ]
    detail_tests = [
        { 'uid': '12/P/0645/F', 'len': 14 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'date': '05/03/2015', 'len': 58 }, 
        { 'date': '13/08/2012', 'len': 25 }
    ]"""

"""class NottinghamScraper(WeeklyWAMScraper): now Idox

    _authority_name = 'Nottingham'
    _search_url = 'http://plan4.nottinghamcity.gov.uk/WAM/pas/searchApplications.do'
    _scrape_ids = ""
    <div id="page"> <table> <tr />
    {* <tr> <td />
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    <td /> <td> {{ [records].status }} </td>
    </tr> *}
    </table> </div>
    ""
    _scrape_data_block = ""
    <div id="page"> {{ block|html }} </div>
    ""
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = ""
    <div id="casefile"> <table>
    <tr> <td> Application No: </td> <td> {{ reference }} </td>
         <td> Registration Date: </td> <td> {{ date_validated }} </td> </tr>
    <tr> <td> Location: </td> <td> {{ address }} </td> </tr>
    <tr> <td> Development: </td> <td> {{ description }} </td> </tr>
    </table> </div>""
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<tr> <td> Applicant: </td> <td> {{ applicant_name }} <br> {{ applicant_address|html }} </td> </tr>',
    '<tr> <td> Agent: </td> <td> {{ agent_name }} <br> {{ agent_address|html }} </td> </tr>',
    '<tr> <td> Decision Date: </td> <td> {{ decision_date }} </td> </tr>',
    '<tr> <td> Application Type: </td> <td> {{ application_type }} </td> </tr>',
    '<tr> <td> Ward: </td> <td> {{ ward_name }} </td> </tr>',
    '<tr> <td> Decision Type: </td> <td> {{ decision }} </td> </tr>',
    ]
    
    def get_html_from_uid (self, uid):
        url = urlparse.urljoin(self._search_url, self._detail_page) + '?councilName=Nottingham+City+Council&appNumber=' + urllib.quote_plus(uid)
        return self.get_html_from_url(url)"""
    
"""class SwanseaScraper(WeeklyWAMScraper): 

    _authority_name = 'Swansea'
    _search_url = 'http://wam.swansea.gov.uk/WAM/weeklyApplications.do'
    _comment = 'was PlanningExplorer'
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = ""
    <table id="casefilesummary">
    <tr> <th> Application No </th> <td> {{ reference }} </td> </tr>
    <tr> <th> Location </th> <td> {{ address }} </td> </tr>
    <tr> <th> Description </th> <td> {{ description }} </td> </tr>
    <tr> <th> Date Application Valid </th> <td> {{ date_validated }} </td>
    </table>""
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<tr> <th> Applicant </th> <td> {{ applicant_name }} </td> </tr>',
    '<tr> <th> Agent </th> <td> {{ agent_name }} </td> </tr>',
    '<tr> <th> Submit Comments By </th> <td> {{ consultation_end_date }} </td> </tr>',
    '<tr> <th> Decision Date </th> <td> {{ decision_date }} </td> </tr>',
    '<tr> <th> Target Date </th> <td> {{ target_decision_date }} </td> </tr>',
    '<tr> <th> Committee Date </th> <td> {{ meeting_date }} </td> </tr>',
    '<tr> <th> Application Type </th> <td> {{ application_type }} </td> </tr>',
    '<p id="comment"> <a href="{{ comment_url|abs }}" /> </p>',
    '<tr> <th> Application Status </th> <td> {{ status }} </td> </tr>',
    '<tr> <th> UPRN </th> <td> {{ uprn }} </td> </tr>',
    '<tr> <th> Community Council </th> <td> {{ parish }} </td> </tr>',
    '<tr> <th> Ward </th> <td> {{ ward_name }} </td> </tr>',
    ""<tr> <th> Determination Level </th> <td> {{ decided_by }} </td> </tr>
    <tr> <th> Decision </th> <td> {{ decision }} </td> </tr>"",
    '<tr> <th> Case Officer </th> <td> {{ case_officer }} </td> </tr>',
    '<tr> <th> Appeal Lodged </th> <td> {{ appeal_date }} </td> </tr>',
    '<tr> <th> Appeal Decision Date </th> <td> {{ appeal_decision_date }} </td> </tr>',
    '<tr> <th> Appeal Decision Status </th> <td> {{ appeal_result }} </td> </tr>',
    ]
    detail_tests = [
        { 'uid': '2012/1066', 'len': 14 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'date': '25/10/2014', 'len': 45 }, 
        { 'date': '13/08/2012', 'len': 36 } ]"""

"""class TowerHamletsScraper(WeeklyWAMScraper): # now Idox

    _authority_name = 'TowerHamlets'
    _search_url = 'http://planreg.towerhamlets.gov.uk/WAM/weeklyApplications.do'
    detail_tests = [
        { 'uid': 'PA/11/02670', 'len': 16 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'date': '18/10/2014', 'len': 57 }, 
        { 'date': '13/08/2012', 'len': 43 } ]"""

"""class WestLothianScraper(WeeklyWAMScraper): now Idox

    _authority_name = 'WestLothian'
    _search_url = 'http://planning.westlothian.gov.uk/WAM133/weeklyApplications.do'
    _scrape_data_block = ""
    <div id="white-bg"> {{ block|html }} </div>
    ""
    """


    