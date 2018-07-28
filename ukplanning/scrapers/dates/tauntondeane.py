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
import urllib, urlparse
import re
try:
    from ukplanning import scrapemark
except ImportError:
    import scrapemark
try:
    from ukplanning import scrapeutils
except ImportError:
    import scrapeutils
from .. import base

# Note date search requests seem to fail (no results returned) if they are for less than three days

class TauntonDeaneScraper(base.DateScraper):

    data_start_target = '2000-01-06'
    min_id_goal = 120 # min target for application ids to fetch in one go
    max_update_batch = 100 # max application details to scrape in one go
    
    _search_url = 'http://www1.tauntondeane.gov.uk/tdbcsites/plan/plapplookup.asp'
    _detail_page = 'PlAppDets.asp'
    _authority_name = 'TauntonDeane'
    _date_from_field = 'regdate1'
    _date_to_field = 'regdate2'
    _request_date_format = '%d/%m/%Y'
    _search_form = 'Search'
    _search_fields = { 'ViewAll': 'All', 'PageType': 'Search' }
    _address_regex = re.compile(r'\s+(?:OF|AT|ON LAND AT|ON LAND)\s+(.+?)(?=\s*\Z|\s+(?:OF|AT|ON LAND AT|ON LAND)\s+)', re.I) 
    _noparen_regex = re.compile(r'\([^\)]*\)', re.I) 
    _nonalpha_regex = re.compile(r'\W') # excludes anything non-alphanumeric
    _scrape_ids = """
    <h1> Planning applications </h1>
    {* <table>
    <tr> <td> <a href="{{ [records].url|abs }}">
    Application number : {{ [records].uid }} </a> </td> </tr>
    </table> *}
    """
    _scrape_data_block = """
    <table> {{ block|html }} </table>
    """
    _scrape_min_data = """
    <tr> <th> Application Number </th> <td> {{ reference }} </td> </tr>
    <tr> <th> Received </th> <td> {{ date_received }} </td> </tr>
    <tr> <th> Registered </th> <td> {{ date_validated }} </td> </tr>
    <tr> <th> Proposal </th> <td> {{ description }} </td> </tr>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<tr> <th> Application Status </th> <td> {{ status }} </td> </tr>',
    '<tr> <th> Application Type </th> <td> {{ application_type }} </td> </tr>',
    '<tr> <th> Parish </th> <td> {{ parish }} </td> </tr>',
    '<tr> <th> Status </th> <td> {{ status }} </td> </tr>',
    '<tr> <th> Officer </th> <td> {{ case_officer }} </td> </tr>',
    '<tr> <th> Target Decision Date </th> <td> {{ target_decision_date }} </td> </tr>',
    '<tr> <td> Consultation Period </th> <td> {{ consultation_start_date }} - {{ consultation_end_date }} </td> </tr>',
    '<tr> <th> Applicant </th> <td> {{ applicant_name|html }} </td> </tr>',
    """<tr> <th> Correspondent </th> <td> {{ agent_name|html }} </td> </tr>
    <tr> <th> Correspondent Address </th> <td> {{ agent_address|html }} </td> </tr>""",
    ]
    detail_tests = [
        { 'uid': '17/11/0006', 'len': 14 } ]
    batch_tests = [ # note date ranges should not overlap
    { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 24 },
      { 'from': '15/08/2012', 'to': '15/08/2012', 'len': 5 } ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s", response.read())

        fields = self._search_fields
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
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
        url = urlparse.urljoin(self._search_url, self._detail_page) + '?casefullref=' + urllib.quote_plus(uid)
        return self.get_html_from_url(url)
        
    def _get_details(self, html, this_url):
        """ Scrapes detailed information for one record given html and url 
        - this is an optional hook to allow data from multiple linked pages to be merged """
        result = self._get_detail(html, this_url)
        if 'scrape_error' in result or not result.get('description'):
            return result
        description = self._noparen_regex.sub('', result['description'])
        address_match = self._address_regex.findall(description)
        if address_match: # list
            result['address'] = address_match[-1] # last match
            try:
                address_lower = self._nonalpha_regex.sub('', result['address'].lower())
                agent_address_lower = self._nonalpha_regex.sub('', result['agent_address'].lower())
                if agent_address_lower.find(address_lower) >= 0: # if the address matches the agent address, use that, as it is likely to contain a postcode
                    result['address'] = result['agent_address']
            except:
                pass
        else:
            result['address'] = description
        return result






