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
from datetime import timedelta
from datetime import date
import re

# North Warks, Coventry, Staff Moorlands have dual reference numbers

class AppSearchServScraper(base.DateScraper):

    min_id_goal = 300 # min target for application ids to fetch in one go
    
    _scraper_type = 'AppSearchServ'
    _headers = {
    'Accept-Charset': 'UTF-8,*',
    'Accept': 'text/html',
    'User-Agent': 'Mozilla/5.0 (Windows NT 5.1; rv:7.0.1) Gecko/20100101 Firefox/7.0.1',
    }
    # received dates = Ealing, Haringey
    # also could be Coventry, Preston
    _date_from_field = 'ValidDateFrom'
    _date_to_field = 'ValidDateTo'
    _ref_field = 'ExistingRefNo'
    _search_form = 'AppSearchForm'
    _request_date_format = '%d-%m-%Y'
    _html_subs = {}
    _scrape_ids = """
    <h1 /> <table> <tr />
    {* <tr>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    </tr> *}
    </table>
    """
    _scrape_no_recs = '<div id="pageCenter"> {{ no_recs }} any results </div>'
    _next_page_form = 'navigationForm2' 

    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <body> {{ block|html }} </body>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <tr> Reference <td> {{ reference }} </td> </tr>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [ ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        self._adjust_response(response)
        #self.logger.debug("Start html: %s", response.read())

        fields = {}
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        self._adjust_response(response)
        
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
                break
            try:
                scrapeutils.setup_form(self.br, self._next_page_form)
                self.logger.debug("ID next form: %s", str(self.br.form))
                response = scrapeutils.submit_form(self.br)
                self._adjust_response(response)
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next form after %d pages", page_count)
                break
                
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
            
        return final_result

    def get_html_from_uid (self, uid):
        response = self.br.open(self._search_url)
        self._adjust_response(response)
        #self.logger.debug("ID detail start html: %s", response.read())
        fields = {  self._ref_field: uid }
        scrapeutils.setup_form(self.br, self._search_form, fields)
        response = scrapeutils.submit_form(self.br)
        html, url = self._get_html(response)
        result = scrapemark.scrape(self._scrape_ids, html, url)
        if result and result.get('records'):
            self._clean_ids(result['records'])
            for r in result['records']:
                if r.get('uid', '') == uid and r.get('url'):
                    self.logger.debug("Scraped url: %s", r['url'])
                    return self.get_html_from_url(r['url'])
        return None, None
        
    def _clean_record(self, record):
        super(AppSearchServScraper, self)._clean_record(record)
        if record.get('alt_reference'):
            if not record.get('planning_portal_id') and record['alt_reference'].startswith('PP-'):
                record['planning_portal_id'] = record['alt_reference']
            elif record['alt_reference'].lower() <> 'not available':
                record['reference'] = record['alt_reference']
            del record['alt_reference']
            
    def _adjust_response(self, response): 
        """ fixes bad html that breaks form processing """
        if self._html_subs:
            html = response.get_data()
            for k, v in self._html_subs.items():
                html = re.sub(k, v, html, 0, re.U|re.S|re.I) # unicode|dot matches new line|ignore case
            response.set_data(html)
            self.br.set_response(response)

class AllerdaleScraper(AppSearchServScraper):

    _search_url = 'http://planning.allerdale.gov.uk/portal/servlets/ApplicationSearchServlet'
    _authority_name = 'Allerdale'

    _scrape_no_recs = '<div id="content"> {{ no_recs }} not return any results </div>'

    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <div id="content"> {{ block|html }} </div>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <tr> <th> Reference </th> <td> {{ reference }} </td> </tr>
    <tr> <th> Address </th> <td> {{ address|html }} </td> 
         <th> Development </th> <td> {{ description }} </td> </tr>
    <tr> <th> Valid </th> <td> {{ date_validated }} </td> </tr>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [ 
    "<tr> <th> Application Type </th> <td> {{ application_type }} </td> </tr>",
    "<tr> <th> Committee Date </th> <td> {{ meeting_date }} </td> </tr>",
    "<tr> <th> Officer </th> <td> {{ case_officer }} </td> </tr>",
    "<tr> <th> Decision </th> <td> {{ decision }} </td> <th> Decision Date </th> <td> {{ decision_date }} </td> </tr>",
    "<tr> <th> Consultation Start Date </th> <td> {{ consultation_start_date }} </td> </tr>",
    "<tr> <th> Consultation End Date </th> <td> {{ consultation_end_date }} </td> </tr>",
    "<tr> <th> Applicant Name </th> <td> {{ applicant_name|html }} </td> </tr>",
    "<tr> <th> Agent Name </th> <td> {{ agent_name|html }} </td> </tr>",
    "<tr> <th> Applicant Address </th> <td> {{ applicant_address|html }} </td> </tr>",
    "<tr> <th> Agent Address </th> <td> {{ agent_address|html }} </td> </tr>",
    ]
    detail_tests = [
        { 'uid': '2/2011/0608', 'len': 15 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 21 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 12 } ]

class CoventryScraper(AppSearchServScraper):

    _search_url = 'http://planning.coventry.gov.uk/portal/servlets/ApplicationSearchServlet'
    _authority_name = 'Coventry'

    _date_from_field = 'ReceivedDateFrom'
    _date_to_field = 'ReceivedDateTo'
    _scrape_no_recs = '<h1 class="mainTitle">Sorry, but your query did not return any results {{ no_recs }} </h1>'

    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <div id="mainPad"> <table> <table> {{ block|html }} </table> </table> </div>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <tr> <td> Reference Number </td> <td> {{ reference }} </td> </tr>
    <tr> <td> Address </td> <td> {{ address|html }} </td>
         <td> Proposal </td> <td> {{ description }} </td> </tr>
    <tr> <td> Received </td> <td> {{ date_received }} </td> 
         <td> Valid </td> <td> {{ date_validated }} </td> </tr>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    "<tr> <td> Coventry Reference </td> <td> {{ alt_reference }} </td> </tr>",
    "<tr> <td> Application Description </td> <td> {{ application_type }} </td> </tr>",
    "<tr> <td> Application Status </td> <td> {{ status }} </td> </tr>",
    "<tr> <td> Determination Required </td> <td> {{ target_decision_date }} </td> </tr>",
    "<tr> <td> Committee Date </td> <td> {{ meeting_date }} </td> </tr>",
    "<tr> <td> Officer </td> <td> {{ case_officer }} </td> </tr>",
    """<tr> <td> Decision By </td> <td> {{ decided_by }} </td> <td> Committee Date </td> </tr>
    <tr> <td> Decision </td> <td> {{ decision }} </td> <td> Decision Date </td> <td> {{ decision_date }} </td> </tr>""",
    "<tr> <td> Start of Public Consultation </td> <td> {{ consultation_start_date }} </td> </tr>",
    "<tr> <td> End of Public Consultation </td> <td> {{ consultation_end_date }} </td> </tr>",
    "<tr> <td> Applicant Name </td> <td> {{ applicant_name|html }} </td> </tr>",
    "<tr> <td> Agent Name </td> <td> {{ agent_name|html }} </td> </tr>",
    "<tr> <td> Applicant Address </td> <td> {{ applicant_address|html }} </td> </tr>",
    "<tr> <td> Agent Address </td> <td> {{ agent_address|html }} </td> </tr>",
    ]
    detail_tests = [
        { 'uid': 'FUL/2012/0660', 'len': 19 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 23 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 4 } ]

"""class CrookScraper(AppSearchServScraper):

    _search_url = 'http://planning.wearvalley.gov.uk/portal/servlets/ApplicationSearchServlet'
    _authority_name = 'Crook'
    _disabled = True
    _comment = 'Wear Valley. Inactive from Mar 2014 see County Durham Idox'

    _scrape_no_recs = ""<div id="bodycontent"> <strong>Sorry, but your query did not 
    return any results, {{ no_recs }} </strong> </div>""

    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = ""
    <div id="bodycontent"> {{ block|html }} </div>
    ""
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = ""
    <tr> <td> Reference </td> <td> {{ reference }} </td> </tr>
    <tr> <td> Address </td> <td> {{ address|html }} </td>
         <td> Development </td> <td> {{ description }} </td> </tr>
    <tr> <td> Valid </td> <td> {{ date_validated }} </td>
        <td> Received </td> <td> {{ date_received }} </td> </tr>
    ""
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    "<tr> <td> Application Type </td> <td> {{ application_type }} </td> </tr>",
    "<tr> <td> Status </td> <td> {{ status }} </td> </tr>",
    "<tr> <td> Status </td> <td> {{ decision }} </td> </tr>",
    "<tr> <td> Committee Date </td> <td> {{ meeting_date }} </td> </tr>",
    "<tr> Agent Name <td> Officer </td> <td> {{ case_officer }} </td> </tr>",
    "<tr> <td> Decision Level </td> <td> {{ decided_by }} </td> </tr>",
    "<tr> <td> Decision Date </td> <td> {{ decision_date }} </td> </tr>",
    "<tr> <td> Consultation Start Date </td> <td> {{ consultation_start_date }} </td> </tr>",
    "<tr> <td> Consultation End Date </td> <td> {{ consultation_end_date }} </td> </tr>",
    "<tr> <td> Applicant Name </td> <td> {{ applicant_name|html }} </td> </tr>",
    "<tr> <td> Agent Name </td> <td> {{ agent_name|html }} </td> </tr>",
    "<tr> <td> Applicant Address </td> <td> {{ applicant_address|html }} </td> </tr>",
    "<tr> <td> Agent Address </td> <td> {{ agent_address|html }} </td> </tr>",
    ]
    detail_tests = [
        { 'uid': '3/2012/0259', 'len': 18 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 8 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 1 } ]"""

"""class EalingScraper(AppSearchServScraper): now Idox

    batch_size = 18
    
    _search_url = 'http://www.pam.ealing.gov.uk/portal/servlets/ApplicationSearchServlet'
    _authority_name = 'Ealing'
    _date_from_field = 'ReceivedDateFrom'
    _date_to_field = 'ReceivedDateTo'
    _scrape_no_recs = '<div class="innerContent"> {{ no_recs }} any results </div>'

    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = ""
    <div id="content"> {{ block|html }} </div>
    ""
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = ""
    <tr> <td> Reference </td> <td> {{ reference }} </td> </tr>
    <tr> <td> Address </td> <td> {{ address|html }} </td> </tr>
    <tr> <td> Description </td> <td> {{ description }} </td> </tr>
    <tr> <td> Received </td> <td> {{ date_received }} </td> </tr>
    <tr> <td> Valid </td> <td> {{ date_validated }} </td> </tr>
    ""
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    "<tr> <td> Application Type </td> <td> {{ application_type }} </td> </tr>",
    "<tr> <td> Ward </td> <td> {{ ward_name }} </td> </tr>",
    "<tr> <td> Determination Required </td> <td> {{ target_decision_date }} </td> </tr>",
    "<tr> <td> Committee/Delegated Date </td> <td> {{ meeting_date }} </td> </tr>",
    "<tr> <td> Officer </td> <td> {{ case_officer }} </td> </tr>",
    "<tr> <td> Committee or Delegated </td> <td> {{ decided_by }} </td> </tr>",
    "<tr> <td> Decision </td> <td> {{ decision }} </td> </tr> <tr> <td> Decision Date </td> <td> {{ decision_date }} </td> </tr>",
    "<tr> <td> Consultation Start Date </td> <td> {{ consultation_start_date }} </td> </tr>",
    "<tr> <td> Consultation End Date </td> <td> {{ consultation_end_date }} </td> </tr>",
    "<tr> <td> Applicant Name </td> <td> {{ applicant_name|html }} </td> </tr>",
    "<tr> <td> Agent Name </td> <td> {{ agent_name|html }} </td> </tr>",
    "<tr> <td> Applicant Address </td> <td> {{ applicant_address|html }} </td> </tr>",
    "<tr> <td> Agent Address </td> <td> {{ agent_address|html }} </td> </tr>",
    '<tr> <a href="{{comment_url|abs }}"> comment on this </a> </tr>',
    ]
    detail_tests = [
        { 'uid': 'P/2012/4146', 'len': 14 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 82 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 23 } ]
        
    # Ealing has some bad dates (26/7/2013, 24/7/2012) which if included causes a server exception
    bad_dates = [ date(2014,4,16), date(2013,7,26), date(2012,7,24) ]
    def get_id_batch (self, date_from, date_to):
        results = None
        for bd in self.bad_dates:
            results = self.do_bad_batch(date_from, date_to, bd)
            if results is not None:
                break
        if results is None:
            results = super(EalingScraper, self).get_id_batch(date_from, date_to)
        final_results = []
        for res in results:
            if res.get('uid'): # Ealing has problem where some records don't get a uid - so skip them
                final_results.append(res)
        return final_results
            
    def do_bad_batch (self, date_from, date_to, bad_date):
        if date_from > bad_date or date_to < bad_date:
            return None
        elif date_from == bad_date: 
            date_from = bad_date + timedelta(days=1)
            return super(EalingScraper, self).get_id_batch(date_from, date_to)
        elif date_to == bad_date: 
            date_to = bad_date - timedelta(days=1)
            return super(EalingScraper, self).get_id_batch(date_from, date_to)
        else:
            new_date_from = bad_date + timedelta(days=1)
            new_date_to = bad_date - timedelta(days=1)
            result = super(EalingScraper, self).get_id_batch(date_from, new_date_to)
            result2 = super(EalingScraper, self).get_id_batch(new_date_from, date_to)
            result.extend(result2)
            return result"""
            
"""class EasingtonScraper(AppSearchServScraper): 
    
    _search_url = 'http://planning.easington.gov.uk/portal/servlets/ApplicationSearchServlet'
    _authority_name = 'Easington'
    _disabled = True
    _comment = 'Inactive from Sep 2013 see County Durham Idox'

    _date_from_field = 'ReceivedDateFrom'
    _date_to_field = 'ReceivedDateTo'
    _scrape_no_recs = ""<div id="contenthome"> <strong> Sorry, but your query did 
    not return any results, {{ no_recs }} </strong> </div>""

    _scrape_ids = ""
    <h1 /> <table /> <table> <tr />
    {* <tr>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    </tr> *}
    </table>
    ""

    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = ""
    <form name="formPLNDetails"> {{ block|html }} </form>
    ""
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = ""
    <input value="{{ reference }}" name="REF_NO">
    <tr> <td> Address </td> <td> {{ address }} </td>
        <td> Description </td> <td> {{ description }} </td> </tr>
    <input value="{{ date_validated }}" name="DateValid">
    ""
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<input value="{{ application_type }}" name="ApplicationType">',
    '<input value="{{ ward_name }}" name="Ward">',
    '<input value="{{ parish }}" name="ParishDescription">',
    '<input value="{{ status }}" name="CurrentStatus">',
    '<input value="{{ decision }}" name="CurrentStatus">',
    '<input value="{{ decision_date }}" name="CurrentStatusDate">',
    '<input value="{{ decided_by }}" name="CommitteeType">',
    '<input value="{{ agent_name }}" name="AgentName">',
    '<input value="{{ applicant_name }}" name="ApplicantName">',
    "<tr> Handling Officer <td> {{ case_officer }} </td> </tr>",
    '<textarea name="AGE_ADDRESS"> {{ agent_address }} </textarea>',
    '<textarea name="APP_ADDRESS"> {{ applicant_address }} </textarea>',
    ]
    detail_tests = [
        { 'uid': 'PL/5/2011/0260', 'len': 13 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 2 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 1 } ]"""

class GuernseyScraper(AppSearchServScraper):

    _search_url = 'http://planningexplorer.gov.gg/portal/servlets/ApplicationSearchServlet'
    _authority_name = 'Guernsey'
    data_start_target = '2009-04-01'

    _scrape_no_recs = '<div class="itemContent"> {{ no_recs }} not return any results </div>'

    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <div class="itemContent"> {{ block|html }} </div>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <tr> <td> Number </td> <td> {{ reference }} </td> </tr>
    <tr> <td> Address </td> <td> {{ address|html }} </td> </tr>
    <tr> <td> Description </td> <td> {{ description }} </td> </tr>
    <tr> <td> Received </td> <td> {{ date_received }} </td> </tr>
    <tr> <td> Valid </td> <td> {{ date_validated }} </td> </tr>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    "<tr> <td> Application Type </td> <td> {{ application_type }} </td> </tr>",
    "<tr> <td> Current Status </td> <td> {{ status }} </td> </tr>",
    "<tr> <td> Current Status </td> <td> {{ decision }} </td> </tr>",
    "<tr> <td> Officer </td> <td> {{ case_officer }} </td> </tr>",
    "<tr> <td> Committee or Delegated </td> <td> {{ decided_by }} </td> </tr>",
    "<tr> <td> Decision Notification Date </td> <td> {{ decision_date }} </td> </tr>",
    "<tr> <td> Start of Consultation Date </td> <td> {{ consultation_start_date }} </td> </tr>",
    "<tr> <td> End of Consultation Date </td> <td> {{ consultation_end_date }} </td> </tr>",
    "<tr> <td> Applicant Name </td> <td> {{ applicant_name|html }} </td> </tr>",
    "<tr> <td> Agent </td> <td> {{ agent_name|html }} </td> </tr>",
    "<tr> <td> Applicant Address </td> <td> {{ applicant_address|html }} </td> </tr>",
    "<tr> <td> Agent Address </td> <td> {{ agent_address|html }} </td> </tr>",
    '<tr> <a href="{{comment_url|abs }}"> comment on this </a> </tr>',
    ]
    detail_tests = [
        { 'uid': 'FULL/2011/2233', 'len': 13 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 34 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 10 } ]

class HaringeyScraper(AppSearchServScraper):

    _search_url = 'http://www.planningservices.haringey.gov.uk/portal/servlets/ApplicationSearchServlet'
    _authority_name = 'Haringey'

    batch_size = 18
    _date_from_field = 'ReceivedDateFrom'
    _date_to_field = 'ReceivedDateTo'
    _scrape_no_recs = '<h2> {{ no_recs }} not return any results </h2>'

    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <form name="formPLNDetails"> {{ block|html }} </form>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <input value="{{ reference }}" name="REF_NO" />
    <tr> <td> Location </td> <td> <textarea> {{ address }} </textarea> </td>
        <td> Development </td> <td> {{ description }} </td> </tr>
    <input value="{{ date_received }}" name="DateReceived" />
    
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<input value="{{ application_type }}" name="ApplicationType">',
    '<input value="{{ planning_portal_id }}" name="PORTAL_REF">',
    '<input value="{{ ward_name }}" name="Ward">',
    '<input value="{{ easting }}" name="Eastings" /> <input value="{{ northing }}" name="Northings" />',
    '<input value="{{ status }}" name="CurrentStatus">',
    '<input value="{{ decision }}" name="CurrentStatus">',
    '<input value="{{ decision_date }}" name="CurrentStatusDate">',
    '<input value="{{ decided_by }}" name="CommitteeType">',
    '<input value="{{ agent_name }}" name="AgentName">',
    '<input value="{{ agent_tel }}" name="AG_Telephone">',
    '<input value="{{ meeting_date }}" name="CommitteeDate">',
    '<input value="{{ applicant_name }}" name="ApplicantName">',
    "<tr> <td> Officer </td> <td> {{ case_officer }} </td> </tr>",
    "<tr> <td> Agent Address </td> <td> {{ agent_address }} </td> </tr>",
    "<tr> <td> Applicant Address </td> <td> {{ applicant_address }} </td> </tr>",
    ]
    detail_tests = [
        { 'uid': 'HGY/2012/1554', 'len': 15 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 54 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 19 } ]

class HartlepoolScraper(AppSearchServScraper):

    _search_url = 'http://eforms.hartlepool.gov.uk:7777/portal/servlets/ApplicationSearchServlet'
    _authority_name = 'Hartlepool'

    _scrape_no_recs = """<h1>Search Results List</h1>
    <strong>Sorry, but your query did not return any results {{ no_recs }} </strong>"""

    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <div class="box3"> {{ block|html }} </div>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <tr> <td> Reference </td> <td> {{ reference }} </td> </tr>
    <tr> <td> Development </td> </tr> <tr> <td> {{ description }} </td> </tr>
    <tr> <td> Address </td> <td> {{ address|html }} </td> 
         <td> Valid </td> <td> {{ date_validated }} </td> </tr>
    <tr> <td> Received </td> <td> {{ date_received }} </td> </tr>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    "<tr> <td> Application Type </td> <td> {{ application_type }} </td> </tr>",
    "<tr> <td> Target Date </td> <td> {{ target_decision_date }} </td> </tr>",
    "<tr> <td> Officer </td> <td> {{ case_officer }} </td> </tr>",
    "<tr> <td> Decision </td> <td> {{ decision }} </td> <td> Decision Date </td> <td> {{ decision_date }} </td> </tr>",
    "<tr> <td> Applicant Name </td> <td> {{ applicant_name|html }} </td> </tr>",
    "<tr> <td> Agent Details </td> <td> {{ agent_name|html }} <br> {{ agent_address|html }} </td> </tr>",
    "<tr> <td> Applicant Address </td> <td> {{ applicant_address|html }} </td> </tr>",
    ]
    detail_tests = [
        { 'uid': 'H/2011/0408', 'len': 14 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 9 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 } ]

class HighPeakScraper(AppSearchServScraper):

    _search_url = 'http://planning.highpeak.gov.uk/portal/servlets/ApplicationSearchServlet'
    _authority_name = 'HighPeak'

    _date_from_field = 'ReceivedDateFrom'
    _date_to_field = 'ReceivedDateTo'
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <form name="formPLNDetails"> {{ block|html }} </form>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <tr> <td> Application Number </td> <td> {{ reference }} </td> </tr>
    <tr> <td> Site Address </td> <td> {{ address|html }} </td> 
    <td> Proposal </td> <td> {{ description }} </td> </tr>
    <tr> <td> Received Date </td> <td> {{ date_received }} </td> 
    <td> Valid Date </td> <td> {{ date_validated }} </td> </tr>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    "<tr> <td> Application Type </td> <td> {{ application_type }} </td> </tr>",
    "<tr> <td> Application Status </td> <td> {{ status }} </td> </tr>",
    "<tr> <td> Parish </td> <td> {{ parish }} </td> </tr>",
    "<tr> <td> Ward </td> <td> {{ ward_name }} </td> </tr>",
    """<tr> <td> Decision </td> <td> {{ decision }} </td> 
    <td> Decision Date </td> <td> {{ decision_date }} </td> </tr>""",
    #"<tr> <td> Eastings </td> <td> {{ easting }} <br /> {{ northing }} </td> </tr>",
    "<tr> <td> Committee Date </td> <td> {{ meeting_date }} </td> </tr>",
    "<tr> <td> Case Officer </td> <td> {{ case_officer }} </td> </tr>",
    "<tr> <td> Determination Required Date </td> <td> {{ target_decision_date }} </td> </tr>",
    "<tr> <td> Permission Expiry Date </td> <td> {{ permission_expires_date }} </td> </tr>",
    "<tr> <td> Decision By </td> <td> {{ decided_by }} </td> </tr>",
    "<tr> <td> Start of Public Consultation Period </td> <td> {{ consultation_start_date }} </td> </tr>",
    "<tr> <td> End of Public Consultation Period </td> <td> {{ consultation_end_date }} </td> </tr>",
    "<tr> <td> Applicant Name </td> <td> {{ applicant_name|html }} </td> </tr>",
    "<tr> <td> Agent Name </td> <td> {{ agent_name|html }} </td> </tr>",
    "<tr> <td> Applicant Address </td> <td> {{ applicant_address|html }} </td> </tr>",
    "<tr> <td> Agent Address </td> <td> {{ agent_address|html }} </td> </tr>",
    "<tr> <td> Agent Telephone </td> <td> {{ agent_tel|html }} </td> </tr>",
    ]
    detail_tests = [
        { 'uid': 'HPK/2011/0381', 'len': 17 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 13 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]

class NorthWarwickshireScraper(AppSearchServScraper):

    _search_url = 'http://planning.northwarks.gov.uk/portal/servlets/ApplicationSearchServlet'
    _authority_name = 'NorthWarwickshire'

    _date_from_field = 'ReceivedDateFrom'
    _date_to_field = 'ReceivedDateTo'
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <div id="central"> {{ block|html }} </div>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <tr> <td> Reference </td> <td> {{ reference }} </td> </tr>
    <tr> <td> Old Reference </td> <td> {{ alt_reference }} </td> </tr>
    <tr> <td> Location </td> <td> {{ address|html }} </td> </tr>
    <tr> <td> Proposal </td> <td> {{ description }} </td> </tr>
    <tr> <td> Received </td> <td> {{ date_received }} </td> </tr>
    <tr> <td> Valid </td> <td> {{ date_validated }} </td> </tr>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    "<tr> <td> Eastings </td> <td> {{ easting }} </td> </tr> <tr> <td> Northings </td> <td> {{ northing }} </td> </tr>",
    "<tr> <td> Ward </td> <td> {{ ward_name }} </td> </tr>",
    "<tr> <td> Parish </td> <td> {{ parish }} </td> </tr>",
    "<tr> <td> Case Officer </td> <td> {{ case_officer }} </td> </tr>",
    "<tr> <td> Decision Level </td> <td> {{ decided_by }} </td> </tr>",
    "<tr> <td> Decision </td> <td> {{ decision }} </td> </tr> <tr> <td> Decision Date </td> <td> {{ decision_date }} </td> </tr>",
    "<tr> <td> Consultation Start Date </td> <td> {{ consultation_start_date }} </td> </tr>",
    "<tr> <td> Consultation End Date </td> <td> {{ consultation_end_date }} </td> </tr>",
    "<tr> <td> Applicant Name </td> <td> {{ applicant_name|html }} </td> </tr>",
    "<tr> <td> Agent Name </td> <td> {{ agent_name|html }} </td> </tr>",
    "<tr> <td> Applicant Address </td> <td> {{ applicant_address|html }} </td> </tr>",
    "<tr> <td> Agent Address </td> <td> {{ agent_address|html }} </td> </tr>",
    "<tr> <td> Portal Ref </td> <td> {{ planning_portal_id }} </td> </tr>",
    ]
    detail_tests = [
        { 'uid': 'PAP/2011/0396', 'len': 17 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 12 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]

class PowysScraper(AppSearchServScraper):

    _search_url = 'http://planning.powys.gov.uk/portal/servlets/ApplicationSearchServlet'
    _authority_name = 'Powys'

    batch_size = 18
    _scrape_no_recs = '<p> {{ no_recs }} not return any results </p>'

    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <table class="contenttable"> {{ block|html }} </table>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <tr> <td> Reference </td> <td> {{ reference }} </td>
         <td> Received </td> <td> {{ date_received }} </td> </tr>
    <tr> <td> Address </td> <td> {{ address|html }} </td>
         <td> Development </td> <td> {{ description }} </td> </tr>
    <tr> <td> Valid </td> <td> {{ date_validated }} </td> </tr>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    "<tr> <td> Eastings </td> <td> {{ easting }} </td> <td> Northings </td> <td> {{ northing }} </td> </tr>",
    "<tr> <td> Community Council </td> <td> {{ district }} </td> </tr>",
    "<tr> <td> Officer </td> <td> {{ case_officer }} </td> </tr>",
    "<tr> <td> Committee Type </td> <td> {{ decided_by }} </td> </tr>",
    "<tr> <td> Committee Date </td> <td> {{ meeting_date }} </td> </tr>",
    "<tr> <td> Decision </td> <td> {{ decision }} </td> <td> Decision Date </td> <td> {{ decision_date }} </td> </tr>",
    "<tr> <td> Consultation Start Date </td> <td> {{ consultation_start_date }} </td> </tr>",
    "<tr> <td> Consultation End Date </td> <td> {{ consultation_end_date }} </td> </tr>",
    "<tr> <td> Applicant Name </td> <td> {{ applicant_name|html }} </td> </tr>",
    "<tr> <td> Agent Name </td> <td> {{ agent_name|html }} </td> </tr>",
    "<tr> <td> Applicant Company </td> <td> {{ applicant_company|html }} </td> </tr>",
    "<tr> <td> Agent Telephone </td> <td> {{ agent_tel }} </td> </tr>",
    "<tr> <td> Agent Company </td> <td> {{ agent_company|html }} </td> </tr>",
    "<tr> <td> Applicant Address </td> <td> {{ applicant_address|html }} </td> </tr>",
    "<tr> <td> Agent Address </td> <td> {{ agent_address|html }} </td> </tr>",
    ]
    detail_tests = [
        { 'uid': 'P/2011/0800', 'len': 17 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 25 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 6 } ]

"""class PrestonScraper(AppSearchServScraper): # now SwiftLG

    _search_url = 'http://publicaccess.preston.gov.uk/portal/servlets/ApplicationSearchServlet'
    _authority_name = 'Preston'

    _date_from_field = 'ReceivedDateFrom'
    _date_to_field = 'ReceivedDateTo'
    _scrape_no_recs = '<h1> </h1> <p>Sorry, but your query did not return any results, {{ no_recs }} </p>'

    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = ""
    <div class="table"> {{ block|html }} </div>
    ""
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = ""
    <tr> <td> Reference </td> <td> {{ reference }} </td> </tr>
    <tr> <td> Address </td> <td> {{ address|html }} </td> </tr>
    <tr> <td> Description </td> <td> {{ description }} </td> </tr>
    <tr> <td> Received </td> <td> {{ date_received }} </td> </tr>
    <tr> <td> Valid </td> <td> {{ date_validated }} </td> </tr>
    ""
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    "<tr> <td> Application Type </td> <td> {{ application_type }} </td> </tr>",
    "<tr> <td> Ward </td> <td> {{ ward_name }} </td> </tr>",
    "<tr> <td> Parish </td> <td> {{ parish }} </td> </tr>",
    "<tr> <td> Committee Date </td> <td> {{ meeting_date }} </td> </tr>",
    "<tr> <td> Case Officer </td> <td> {{ case_officer }} </td> </tr>",
    "<tr> <td> Committee Type </td> <td> {{ decided_by }} </td> </tr>",
    "<tr> <td> Decision </td> <td> {{ decision }} </td> </tr> <tr> <td> Decision Date </td> <td> {{ decision_date }} </td> </tr>",
    "<tr> <td> Consultation Start Date </td> <td> {{ consultation_start_date }} </td> </tr>",
    "<tr> <td> Consultation End Date </td> <td> {{ consultation_end_date }} </td> </tr>",
    "<tr> <td> Applicant Name </td> <td> {{ applicant_name|html }} </td> </tr>",
    "<tr> <td> Agent Name </td> <td> {{ agent_name|html }} </td> </tr>",
    "<tr> <td> Applicant Address </td> <td> {{ applicant_address|html }} </td> </tr>",
    "<tr> <td> Agent Address </td> <td> {{ agent_address|html }} </td> </tr>",
    ]
    detail_tests = [
        { 'uid': '06/2012/0630', 'len': 17 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 14 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 1 } ]

class RutlandScraper(AppSearchServScraper): # now SwiftLG

    search_url = 'http://planningonline.rutland.gov.uk:7777/portal/servlets/ApplicationSearchServlet'
    TABLE_NAME = 'Rutland'

    scrape_no_recs = '<div id="mainContent"> {{ no_recs }} not return any results, </div>'

    # captures HTML block encompassing all fields to be gathered
    scrape_data_block = "
    <div id="mainContent"> {{ block|html }} </div>
    "
    # the minimum acceptable valid dataset on an application page
    scrape_min_data = "
    <tr> <th> Reference </th> <td> {{ reference }} </td> </tr>
    <tr> <th> Address </th> <td> {{ address|html }} </td>
         <th> Proposal </th> <td> {{ description }} </td> </tr>
    <tr> <th> Received </th> <td> {{ date_received }} </td>
         <th> Valid </th> <td> {{ date_validated }} </td> </tr>
    "
    # other optional parameters that can appear on an application page
    scrape_optional_data = [
    "<tr> <th> Application Type </th> <td> {{ application_type }} </td> </tr>",
    "<tr> <th> Eastings </th> <td> {{ easting }} </td> <th> Northings </th> <td> {{ northing }} </td> </tr>",
    "<tr> <th> Parish </th> <td> {{ parish }} </td> </tr>",
    "<tr> <th> Officer </th> <td> {{ case_officer }} </td> </tr>",
    "<tr> <th> Committee Type </th> <td> {{ decided_by }} </td> </tr>",
    "<tr> <th> Committee Date </th> <td> {{ meeting_date }} </td> </tr>",
    "<tr> <th> Status </th> <td> {{ status }} </td> </tr>",
    "<tr> <th> Status </th> <td> {{ decision }} </td> </tr>",
    "<tr> <th> Decision Date </th> <td> {{ decision_date }} </td> </tr>",
    "<tr> <th> Consultation Start Date </th> <td> {{ consultation_start_date }} </td> </tr>",
    "<tr> <th> Consultation End Date </th> <td> {{ consultation_end_date }} </td> </tr>",
    "<tr> <th> Applicant Name </th> <td> {{ applicant_name|html }} </td> </tr>",
    "<tr> <th> Agent Name </th> <td> {{ agent_name|html }} </td> </tr>",
    "<tr> <th> Applicant Address </th> <td> {{ applicant_address|html }} </td> </tr>",
    "<tr> <th> Agent Address </th> <td> {{ agent_address|html }} </td> </tr>",
    ]
    detail_tests = [
        { 'uid': 'APP/2011/0540', 'len': 26 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 55 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 13 } ]"""

class StaffordshireMoorlandsScraper(AppSearchServScraper): 

    _search_url = 'http://publicaccess.staffsmoorlands.gov.uk/portal/servlets/ApplicationSearchServlet'
    _authority_name = 'StaffordshireMoorlands'
    _comment = 'Was PublicAccess'
    _date_from_field = 'ReceivedDateFrom'
    _date_to_field = 'ReceivedDateTo'
    _scrape_no_recs = '<strong> Sorry, {{ no_recs }} not return any results </strong>'
    _html_subs = { 
        r'<!</script>': r'</script>',
    }
   
     # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <form name="formPLNDetails"> {{ block|html }} </form>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <tr> <td> Application Number </td> <td> {{ reference }} </td> </tr>
    <tr> <td> Site Address </td> <td> {{ address|html }} </td> 
    <td> Proposal </td> <td> {{ description }} </td> </tr>
    <tr> <td> Received Date </td> <td> {{ date_received }} </td> 
    <td> Valid Date </td> <td> {{ date_validated }} </td> </tr>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    "<tr> <td> Application Type </td> <td> {{ application_type }} </td> </tr>",
    "<tr> <td> Application Status </td> <td> {{ status }} </td> </tr>",
    "<tr> <td> Parish </td> <td> {{ parish }} </td> </tr>",
    "<tr> <td> Ward </td> <td> {{ ward_name }} </td> </tr>",
    """<tr> <td> Decision </td> <td> {{ decision }} </td> 
    <td> Decision Date </td> <td> {{ decision_date }} </td> </tr>""",
    #"<tr> <td> Eastings </td> <td> {{ easting }} <br /> {{ northing }} </td> </tr>",
    "<tr> <td> Committee Date </td> <td> {{ meeting_date }} </td> </tr>",
    "<tr> <td> Case Officer </td> <td> {{ case_officer }} </td> </tr>",
    "<tr> <td> Determination Required Date </td> <td> {{ target_decision_date }} </td> </tr>",
    "<tr> <td> Permission Expiry Date </td> <td> {{ permission_expires_date }} </td> </tr>",
    "<tr> <td> Decision By </td> <td> {{ decided_by }} </td> </tr>",
    "<tr> <td> Start of Public Consultation Period </td> <td> {{ consultation_start_date }} </td> </tr>",
    "<tr> <td> End of Public Consultation Period </td> <td> {{ consultation_end_date }} </td> </tr>",
    "<tr> <td> Applicant Name </td> <td> {{ applicant_name|html }} </td> </tr>",
    "<tr> <td> Agent Name </td> <td> {{ agent_name|html }} </td> </tr>",
    "<tr> <td> Applicant Address </td> <td> {{ applicant_address|html }} </td> </tr>",
    "<tr> <td> Agent Address </td> <td> {{ agent_address|html }} </td> </tr>",
    "<tr> <td> Agent Telephone </td> <td> {{ agent_tel|html }} </td> </tr>",
    ]
    detail_tests = [
        { 'uid': 'SMD/2011/0343', 'len': 18 },
    ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 48 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 6 } ]
    
"""class StHelensScraper(AppSearchServScraper): # now Idox

    _search_url = 'http://llpgport.oltps.sthelens.gov.uk/portal/servlets/ApplicationSearchServlet'
    _authority_name = 'StHelens'
    _date_from_field = 'ReceivedDateFrom'
    _date_to_field = 'ReceivedDateTo'
    _scrape_no_recs = '<p> Sorry, {{ no_recs }} not return any results </p>'

     # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = ""
    <div class="article"> {{ block|html }} </div>
    ""
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = ""
    <tr> <td> Reference </td> <td> {{ reference }} </td> </tr>
    <tr> <td> Address </td> <td> {{ address|html }} </td> </tr>
    <tr> <td> Received </td> <td> {{ date_received }} </td> 
         <td> Valid </td> <td> {{ date_validated }} </td> </tr>
    <tr> <td> Development </td> </tr> <tr> <td> {{ description }} </td> </tr>
    ""
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    "<tr> <td> Application Type </td> <td> {{ application_type }} </td> </tr>",
    "<tr> <td> Eastings </td> <td> {{ easting }} <br /> {{ northing }} </td> </tr>",
    "<tr> <td> Committee Date </td> <td> {{ meeting_date }} </td> </tr>",
    "<tr> <td> Officer </td> <td> {{ case_officer }} </td> </tr>",
    "<tr> <td> Decision Level </td> <td> {{ decided_by }} </td> </tr>",
    "<tr> <td> Decision </td> <td> {{ decision }} </td> <td> Decision Date </td> <td> {{ decision_date }} </td> </tr>",
    "<tr> <td> Consultation Start Date </td> <td> {{ consultation_start_date }} </td> </tr>",
    "<tr> <td> Consultation End Date </td> <td> {{ consultation_end_date }} </td> </tr>",
    "<tr> <td> Applicant Name </td> <td> {{ applicant_name|html }} </td> </tr>",
    "<tr> <td> Agent Name </td> <td> {{ agent_name|html }} </td> </tr>",
    "<tr> <td> Applicant Address </td> <td> {{ applicant_address|html }} </td> </tr>",
    "<tr> <td> Agent Address </td> <td> {{ agent_address|html }} </td> </tr>",
    ]
    detail_tests = [
        { 'uid': 'P/2011/0664', 'len': 19 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 16 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 1 } ]

class WellingboroughScraper(AppSearchServScraper): # now Idox

    _search_url = 'http://planning.wellingborough.gov.uk/portal/servlets/ApplicationSearchServlet'
    _authority_name = 'Wellingborough'

    _date_from_field = 'ReceivedDateFrom'
    _date_to_field = 'ReceivedDateTo'
    _scrape_no_recs = '<h1>Search Results List</h1> Sorry, but your query did not return any results, {{ no_recs }}'

    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = ""
    <tr> <td> Reference </td> <td> {{ reference }} </td> </tr>
    <tr> <td> Address </td> <td> {{ address|html }} </td> </tr>
    <tr> <td> Description </td> <td> {{ description }} </td> </tr>
    <tr> <td> Received </td> <td> {{ date_received }} </td> </tr>
    <tr> <td> Valid </td> <td> {{ date_validated }} </td> </tr>
    ""
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    "<tr> <td> Application Type </td> <td> {{ application_type }} </td> </tr>",
    "<tr> <td> Ward </td> <td> {{ ward_name }} </td> </tr>",
    "<tr> <td> Parish </td> <td> {{ parish }} </td> </tr>",
    "<tr> <td> Committee Date </td> <td> {{ meeting_date }} </td> </tr>",
    "<tr> <td> Officer </td> <td> {{ case_officer }} </td> </tr>",
    "<tr> <td> Committee Type </td> <td> {{ decided_by }} </td> </tr>",
    "<tr> <td> Decision </td> <td> {{ decision }} </td> </tr> <tr> <td> Decision Date </td> <td> {{ decision_date }} </td> </tr>",
    "<tr> <td> Consultation Start Date </td> <td> {{ consultation_start_date }} </td> </tr>",
    "<tr> <td> Consultation End Date </td> <td> {{ consultation_end_date }} </td> </tr>",
    "<tr> <td> Applicant Name </td> <td> {{ applicant_name|html }} </td> </tr>",
    "<tr> <td> Agent Name </td> <td> {{ agent_name|html }} </td> </tr>",
    "<tr> <td> Applicant Address </td> <td> {{ applicant_address|html }} </td> </tr>",
    "<tr> <td> Agent Address </td> <td> {{ agent_address|html }} </td> </tr>",
    '<a href="{{comment_url|abs }}"> comment on this </a>',
    ]
    detail_tests = [
        { 'uid': 'WP/2011/0373', 'len': 17 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 17 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 } ]"""

  






