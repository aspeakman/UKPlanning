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
from datetime import date, timedelta
import urllib, urlparse
import re

class HerefordScraper(base.DateScraper):

    min_id_goal = 200 # min target for application ids to fetch in one go
    
    _authority_name = 'Hereford'
    _search_url= 'https://www.herefordshire.gov.uk/planning-and-building-control/development-control/planning-applications'
    _applic_url = 'https://www.herefordshire.gov.uk/planning-and-building-control/development-control/planning-applications/details'
    _page_params = 'search-term=e&search-service=search&search-source=the%%20keyword&search-item=%%27e%%27&date-from=%s&date-to=%s&status=all&offset=%d'
    _uid_regex = re.compile(r'^[^\d]*(\d+)')
    _scrape_max_recs1 = '<div class="hc-notification hc-notification--info"> Showing planning applications 1 to 10 of {{ max_recs }} for the keyword </div>'
    _scrape_max_recs2 = '<div class="hc-notification hc-notification--info"> {{ max_recs }} planning applications found for the keyword </div>'
    _scrape_ids = """
    <table id="results-table"> <tr />
        {* <tr> <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td> </tr> *}
    </table>"""
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <div id="content"> {{ block|html }} </div>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <tr> <th> Number </th> <td> {{ reference }} </td> </tr>
    <tr> <th> Location </th> <td> {{ address }} </td> </tr>
    <tr> <th> Proposal </th> <td> {{ description }} </td> </tr>
    <tr> <th> Date validated </th> <td> {{ date_validated }} </td> </tr>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<tr> <th> Date received </th> <td> {{ date_received }} </td> </tr>',
    '<tr> <th> Consultation start date </th> <td> {{ consultation_start_date }} </td> </tr>',
    '<tr> <th> Consultation end date </th> <td> {{ consultation_end_date }} </td> </tr>',
    '<tr> <th> Case Officer </th> <td> {{ case_officer }} </td> </tr>',
    '<tr> <th> Decision date </th> <td> {{ decision_date }} </td> </tr>',
    '<tr> <th> Appeal date </th> <td> {{ appeal_date }} </td> </tr>',
    '<tr> <th> Ward </th> <td> {{ ward_name }} </td> </tr>',
    '<tr> <th> Parish </th> <td> {{ parish }} </td> </tr>',
    '<tr> <th> Current status </th> <td> {{ status }} </td> </tr>',
    '<tr> <th> Agent name </th> <td> {{ agent_name }} </td> </tr>',
    '<tr> <th> Agent address </th> <td> {{ agent_address }} </td> </tr>',
    '<tr> <th> Applicant name </th> <td> {{ applicant_name }} </td> </tr>',
    '<tr> <th> Applicant address </th> <td> {{ applicant_address }} </td> </tr>',
    """<tr> <th> Decision </th> <td> {{ decision }} </td> </tr>
    <tr> <th> Type </th> <td> {{ application_type }} </td> </tr>""",
    '<tr> <th> Target determination date </th> <td> {{ target_decision_date }} </td> </tr>',
    '<tr> <th> Appeal date </th> <td> {{ appeal_date }} </td> </tr>',
    '<tr> <th> Appeal decision date </th> <td> {{ appeal_decision_date }} </td> </tr>',
    '<tr> <th> Committee date </th> <td> {{ meeting_date }} </td> </tr>',
    '<tr> <th> Publicity date </th> <td> {{ last_advertised_date }} </td> </tr>',
    '<tr> <th> Comments by </th> <td> {{ comment_date }} </td> </tr>',
    '<tr> <th> Easting/Northing </th> <td> {{ easting }} - {{ northing }} </td> </tr>',
    ]
    detail_tests = [
        { 'uid': 'P142871/FH', 'len': 24 },
        { 'uid': '142871', 'len': 24 }, ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 56 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 7 } ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        page_count = 0
        
        new_date_from = date_from - timedelta(days=1) # NB from date is exclusive
        dfrom = new_date_from.strftime(self._request_date_format) 
        dto = date_to.strftime(self._request_date_format)
        url = self._search_url + '?' + self._page_params % (dfrom, dto, page_count*10)
        self.logger.debug("Start URL: %s", url)
        response = self.br.open(url)
        
        html = response.read()
        #self.logger.debug("ID batch page html: %s", html)
        try:
            result = scrapemark.scrape(self._scrape_max_recs1, html)
            max_recs = int(result['max_recs'])
        except:
            try:
                result = scrapemark.scrape(self._scrape_max_recs2, html)
                max_recs = int(result['max_recs'])
            except:
                max_recs = 0
        
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        while response and len(final_result) < max_recs and page_count < max_pages:
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
            if len(final_result) >= max_recs: break
            try:
                url = self._search_url + '?' + self._page_params % (dfrom, dto, page_count*10)
                self.logger.debug("Next URL: %s", url)
                response = self.br.open(url)
                html = response.read()
            except: # failure to find next page link at end of page sequence here
                self.logger.debug("No next link after %d pages", page_count)
                break
           
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
        
        return final_result

    def get_html_from_uid(self, uid):
        uid_match = self._uid_regex.search(uid)
        if uid_match and uid_match.group(1):
            url = self._applic_url + '?id=' + urllib.quote_plus(uid_match.group(1))
            return self.get_html_from_url(url)
        return None, None
        
