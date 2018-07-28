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

class TeignbridgeScraper(base.DateScraper):

    min_id_goal = 300 # min target for application ids to fetch in one go

    _authority_name = 'Teignbridge'
    _search_url = 'http://gis.teignbridge.gov.uk/TeignbridgePlanningOnline/Search.aspx'
    _details_page = 'Results.aspx'
    _results_page = 'SearchResults.aspx'
    _search_form = 'aspnetForm'
    _submit_control = 'ctl00$MainContent$AdvancedButton'
    _date_from_field = 'ctl00$MainContent$AdvancedValidStartFromDateValueTextBox'
    _date_to_field = 'ctl00$MainContent$AdvancedValidStartToDateValueTextBox'
    _scrape_ids = """
    <div id="ctl00_ctl00_MainContent_ChildContentTabsAddress_divSearchResults">
    {* <table>
    <tr> <td /> <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td> </tr>
    </table> *}
    </div>
    """
    
    _scrape_data_block = '<div id="divResultDetails"> {{ block|html }} </div>'
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <tr> <td> Reference: </td> <td> {{ reference }} </td> </tr>
    <tr> <td> Address: </td> <td> {{ address }} </td> </tr>
    <tr> <td> Proposal: </td> <td> {{ description }} </td> </tr>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<tr> <td> Date Application Received: </td> <td> {{ date_received }} </td> </tr>',
    '<tr> <td> Date Application Validated: </td> <td> {{ date_validated }} </td> </tr>',
    '<tr> <td> Date Appeal Started: </td> <td> {{ date_validated }}{{ appeal_date }} </td> </tr>',
    """<tr> <td> Decision: </td> <td> {{ appeal_result }} </td> </tr>
    <tr> <td> Date Appeal Decided: </td> <td> {{ appeal_decision_date }} </td> </tr>""",
    '<tr> <td> Status: </td> <td> {{ status }} </td> </tr>',
    '<tr> <td> Parish: </td> <td> {{ parish }} </td> </tr>',
    '<tr> <td> Ward: </td> <td> {{ ward_name }} </td> </tr>',
    '<tr> <td> Type of Application: </td> <td> {{ application_type }} </td> </tr>',
    '<tr> <td> Type: </td> <td> {{ application_type }} </td> </tr>',
    """<tr> <td> Decision: </td> <td> {{ decision }} </td> </tr>
    <tr> <td> Date Decision Issued: </td> <td> {{ decision_issued_date }} </td> </tr>""",
    '<tr> <td> Case Officer: </td> <td> {{ case_officer }} </td> </tr>',
    '<tr> <td> Decision Level: </td> <td> {{ decided_by }} </td> </tr>',
    '<tr> <td> Applicant Name: </td> <td> {{ applicant_name }} </td> </tr>',
    '<tr> <td> Applicant Address: </td> <td> {{ applicant_address }} </td> </tr>',
    '<tr> <td> Agent Name: </td> <td> {{ agent_name }} </td> </tr>',
    '<tr> <td> Agent Address: </td> <td> {{ agent_address }} </td> </tr>',
    '<tr> <td> Agent Phone: </td> <td> {{ agent_tel }} </td> </tr>',
    '<tr> <td> Publicity Expiry Date: </td> <td> {{ latest_advertisement_expiry_date }} </td> </tr>',
    '<tr> <td> Target Date: </td> <td> {{ target_decision_date }} </td> </tr>',
    ]
    detail_tests = [
        { 'uid': '11/00030/REF', 'len': 12 },
        { 'uid': '11/02646/FUL', 'len': 19 },
    ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 42 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 5 } ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s", response.read())

        fields = {}
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._submit_control)
        
        if response:
            html = response.read()
            url = response.geturl()
            #self.logger.debug("Batch html: %s" % html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            
        return final_result
        
    def get_html_from_uid(self, uid): 
        #url = urlparse.urljoin(self._search_url, self._detail_page) + '?Type=Application&Refval=' + urllib.quote_plus(uid)
        #url = urlparse.urljoin(self._search_url, self._detail_page) + '?Type=Appeal&Refval=' + urllib.quote_plus(uid)
        #return self.get_html_from_url(url)
        url = urlparse.urljoin(self._search_url, self._results_page) + '?SearchReference=' + urllib.quote_plus(uid)
        response = self.br.open(url)
        html = response.read()
        url = response.geturl()
        result = scrapemark.scrape(self._scrape_ids, html)
        if result and result.get('records'):
            self._clean_ids(result['records'])
            for r in result['records']:
                if r.get('uid', '') == uid:
                    return self.get_html_from_url(r['url'])
            return None, None
        else:
            return html, url
        
        

