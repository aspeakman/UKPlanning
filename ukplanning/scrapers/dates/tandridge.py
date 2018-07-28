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
from datetime import timedelta
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
import urllib

class TandridgeScraper(base.DateScraper):

    data_start_target = '2005-04-06'
    min_id_goal = 200 # min target for application ids to fetch in one go
    batch_size = 35 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 35 # start this number of days ago when gathering current ids

    _authority_name = 'Tandridge'
    _search_url = 'http://tdcws01.tandridge.gov.uk/ArcusPlanning'
    _applic_url = 'http://tdcws01.tandridge.gov.uk/ArcusPlanning/Planning/Planning/Planning'
    _request_date_format = '%Y-%m-%d'
    _date_from_field = 'startDate'
    _date_to_field = 'endDate'
    _search_fields = { 'searchType': 'AcknowledgedDate', 'parish': None }
    _search_form = 'search'

    _scrape_ids = """
    <table id="resultsTable"> <tr />
    {* <tr>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    </tr> *}
    </table>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = '<div class="grid_9"> {{ block|html }} </div>'
    # the minimum acceptable valid dataset on the details page
    _scrape_min_data = """
    <h2> Application {{ reference }} </h2>
    <li> Application received <b> {{ date_received }} </b> </li>
    <li> Application validated <b> {{ date_validated }} </b> </li>
    <h3> Summary </h3> <p> {{ description }} </p>
    <tr> <td> Address </td> <td> {{ address }} </td> </tr>
    """
    # other optional parameters that can appear on the details page
    _scrape_optional_data = [
    "<tr> <td> Type of application </td> <td> {{ application_type }} </td> </tr>",
    "<tr> <td> Application Type </td> <td> {{ application_type }} </td> </tr>",
    "<tr> <td> Appeal decision </td> <td> {{ appeal_result }} </td> </tr>",
    "<tr> <td> Appeal date </td> <td> {{ appeal_date }} </td> </tr>",
    "<tr> <td> Parish </td> <td> {{ parish }} </td> </tr>",
    "<tr> <td> Planning Portal Ref </td> <td> {{ planning_portal_id }} </td> </tr>",
    "<tr> <td> Ward </td> <td> {{ ward_name }} </td> </tr>",
    "<tr> <td> Officer </td> <td> {{ case_officer }} </td> </tr>",
    "<tr> <td> Type of development </td> <td> {{ development_type }} </td> </tr>",
    "<tr> <td> Decision </td> <td> {{ decision }} </td> </tr>",
    '<li> Consultation ended <b> {{ consultation_end_date }} </b> </li>',
    '<li> Decision made <b> {{ decision_date }} </b> </li>',
    ]
    detail_tests = [
        { 'uid': '2011/1062', 'len': 12 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 32 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 1 } ]
    
    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s", response.read())
        
        fields = {}
        fields.update(self._search_fields)
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
        uid = uid.replace('/', '-')
        url = self._applic_url + '?reference=' + urllib.quote_plus(uid)
        return self.get_html_from_url(url)

        



