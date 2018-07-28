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
import urllib

class WiganScraper(base.DateScraper):

    min_id_goal = 350 # min target for application ids to fetch in one go
    
    _authority_name = 'Wigan'
    _start_url = 'http://kinnear.wigan.gov.uk/planapps/'
    _search_url = 'http://kinnear.wigan.gov.uk/planapps/PlanAppsAppSearch.asp'
    _applic_url = 'http://kinnear.wigan.gov.uk/planapps/PlanAppsDetails.asp?passAppNo='
    _date_from_field = 'txtAppRecFromDate'
    _date_to_field = 'txtAppRecToDate'
    _start_fields = { 'txtDisclaimer': 'disclaimeryes' }
    _search_form = '0'
    _scrape_max_recs = '<p> Returned {{ max_recs }} results </p>'
    _response_date_format = '%d/%m/%y'
    _scrape_ids = """
    <table> <tr />
    {* <tr> <td> <a href="{{ [records].url|abs }}">
    {{ [records].uid }} </a> </td> </tr> *}
    </table>
    """
    _scrape_data_block = """
    <div id="L1_container"> {{ block|html }} </div>
    """
    _scrape_min_data = """
    <tr> <td> Application Reference </td> <td> {{ reference }} </td> </tr>
    <tr> <td> Address of Proposal </td> <td> {{ address }} </td> </tr>
    <tr> <td> Proposal </td> <td> {{ description }} </td> </tr>
    <tr> <td> Date Application Valid </td> <td> {{ date_validated }} </td> <td /> <td /> </tr>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<tr> <td> Date Application Received </td> <td> {{ date_received }} </td> </tr>',
    '<tr> <td> Decision Target Date </td> <td> {{ target_decision_date }} </td> </tr>',
    '<tr> <td> Date Decision Made </td> <td> {{ decision_date }} </td> </tr>',
    '<tr> <td> Neighbour Consultations Sent </td> <td> {{ neighbour_consultation_start_date }} </td> <td /> <td /> </tr>',
    '<tr> <td> Neighbour Consultation Expires </td> <td> {{ neighbour_consultation_end_date }} </td> </tr>',
    '<tr> <td> Standard Consultations Sent </td> <td> {{ consultation_start_date }} </td> <td /> <td /> </tr>',
    '<tr> <td> Standard Consultations Expires </td> <td> {{ consultation_end_date }} </td> </tr>',
    '<tr> <td> Committee Date </td> <td> {{ meeting_date }} </td> <td /> <td /> </tr>',
    '<tr> <td> Permission Expires </td> <td> {{ permission_expires_date }} </td> <td /> <td /> </tr>',
    '<tr> <td> Date Decision Issued </td> <td> {{ decision_issued_date }} </td> <td /> <td /> </tr>',
    '<tr> <td> Type of Application </td> <td> {{ application_type }} </td> <td /> <td /> </tr>',
    '<tr> <td> Status </td> <td> {{ status }} </td> </tr>',
    """<tr> <td> Decision </td> <td> {{ decision }} </td> 
    <td> Decision Level </td> <td> {{ decided_by }} </td> </tr>""",
    '<tr> <td> Case Officer </td> <td> {{ case_officer }} </td> <td /> <td /> </tr>',
    '<tr> <td> Ward </td> <td> {{ ward_name }} </td> </tr>',
    "<tr> <td> Applicant's Name </td> <td> {{ applicant_name }} </td> </tr>",
    "<tr> <td> Agent's Name </td> <td> {{ agent_name }} </td> </tr>",
    "<tr> <td> Applicant's Address </td> <td> {{ applicant_address }} </td> </tr>",
    "<tr> <td> Agent's Address </td> <td> {{ agent_address }} </td> </tr>",
    '<tr> <td> Date Appeal Lodged </td> <td> {{ appeal_date }} </td> <td /> <td /> </tr>',
    '<tr> <td> Date Appeal Determined </td> <td> {{ appeal_decision_date }} </td> </tr>',
    ]
    detail_tests = [
        { 'uid': 'A/12/77341', 'len': 21 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 57 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 10 } ]

    def get_id_batch (self, date_from, date_to):
        
        final_result = []
        
        response = self.br.open(self._start_url)
        
        scrapeutils.setup_form(self.br, self._search_form, self._start_fields)
        self.logger.debug("ID start form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        
        #response = self.br.open(self._search_url)
        
        fields = {}
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        
        #response = self.br.open(self._direct_url, urllib.urlencode(fields))
        
        if response:
            
            html = response.read()
            self.logger.debug("ID batch page html: %s", html)
            try:
                result = scrapemark.scrape(self._scrape_max_recs, html)
                max_recs = int(result['max_recs'])
            except:
                max_recs = 0
            
            url = response.geturl()
            #self.logger.debug("Batch html: %s" % html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                self._clean_ids(result['records'])
                final_result.extend(result['records'])          
                
        return final_result

    def get_html_from_uid(self, uid):
        url = self._applic_url + urllib.quote_plus(uid)
        return self.get_html_from_url(url)
            
