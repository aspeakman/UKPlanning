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
import re
from datetime import timedelta


class SouthSomersetScraper(base.DateScraper):

    min_id_goal = 350
    
    _authority_name = 'SouthSomerset'
    _search_url = 'http://www.southsomerset.gov.uk/planning-and-building-control/view-a-planning-application-online/'
    _applic_url = 'http://www.southsomerset.gov.uk/planningdetails/?id='
    _handler = 'etree'
    _cookies = [
        { 'name': 'PlanningStatementOfPurpose', 'value': 'Accepted', 'domain': 'www.southsomerset.gov.uk', 'path': '/' },
    ]
    _search_query = 'startDate=%s&endDate=%s'
    _scrape_ids = """
    <div id="divSearchCriteria" /> <table> <tr />
         {* <tr> <td> {{ [records].uid }} </td>
         <td> {{ [records].date_received }} </td>
         <td> <a href="{{ [records].url|abs }}" /> </td> </tr>
           *}
    </table>"""
    
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <ul class="nav nav-tabs" /> {{ block|html }} <div id="divDocumentsTab" />
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <tr> <td> Proposal </td> <td> {{ description }} </td> </tr>
    <tr> <td> Application No. </td> <td> {{ reference }} </td> </tr>
    <tr> <td> Address </td> <td> {{ address|html }} </td> </tr>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    "<tr> <td> Type of application </td> <td> {{ application_type }} </td> </tr>",
    "<tr> <td> Status </td> <td> {{ status }} </td> </tr>",
    "<tr> <td> Date validated </td> <td> {{ date_validated }} </td> </tr>",
    "<tr> <td> Date received </td> <td> {{ date_received }} </td> </tr>",
    "<tr> <td> Case Officer </td> <td> {{ case_officer }} </td> </tr>",
    "<tr> <td> Ward </td> <td> {{ ward_name }} </td> </tr>",
    "<tr> <td> Parish </td> <td> {{ parish }} </td> </tr>",
    "<tr> <td> Area </td> <td> {{ district }} </td> </tr>",
    "<tr> <td> Target date </td> <td> {{ target_decision_date }} </td> </tr> Target committee",
    "<tr> <td> Committee date </td> <td> {{ meeting_date }} </td> </tr>",
    "<tr> <td> Decision date </td> <td> {{ decision_date }} </td> </tr> Appeal decision",
    "<tr> <td> Decision </td> <td> {{ decision }} </td> </tr> Appeal Status",
    "<tr> <td> Applicant Name </td> <td> {{ applicant_name }} </td> </tr>",
    "<tr> <td> Agent Name </td> <td> {{ agent_name }} </td> </tr>",
    "<tr> <td> Agent Address </td> <td> {{ agent_address }} </td> </tr>",
    "<tr> <td> Proposal </td> <td> (GR:{{ easting }}/{{ northing }}) </td> </tr>",
    "<tr> <td> Appeal status </td> <td> {{ appeal_status }} </td> </tr>",
    "<tr> <td> Appeal logged date </td> <td> {{ appeal_date }} </td> </tr>",
    "<tr> <td> Appeal result </td> <td> {{ appeal_result }} </td> </tr>",
    "<tr> <td> Appeal decision date </td> <td> {{ appeal_decision_date }} </td> </tr>",
    ]
    detail_tests = [
        { 'uid': '12/03648/FUL', 'len': 18 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 1 },
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 14 },
        ]
    
    def get_id_batch (self, date_from, date_to):

        final_result = []
        
        dfrom = date_from.strftime(self._request_date_format)
        dto = date_to.strftime(self._request_date_format)
        query = self._search_query % (dfrom, dto)
        this_url = self._search_url + '?' + query
        response = self.br.open(this_url)
        #print response.geturl()
        
        finished = False
        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        while response and page_count < max_pages and not finished:
            html = response.read()
            url = response.geturl()
            #self.logger.debug("Batch html: %s" % html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                page_count += 1
                self._clean_ids(result['records'])
                for res in result['records']: # query returns excess results (ordered by most recent) 
                    if res['date_received'] < date_from.isoformat():
                        finished = True
                        break # finish early when we find the first date outside the required range
                    else:
                        final_result.append(res)
            else:
                self.logger.debug("Empty result after %d pages", page_count)
                break
            if finished: break
            try:
                next_url = this_url + '&page=' + str(page_count+1)
                response = self.br.open(next_url)
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("Next link failed after %d pages", page_count)
                break
        
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
            
        return final_result
        
    def get_html_from_uid(self, uid):
        uid = uid.replace('/', '')
        url = self._applic_url + urllib.quote_plus(uid)
        return self.get_html_from_url(url)
        


