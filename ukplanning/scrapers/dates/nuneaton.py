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

class NuneatonScraper(base.DateScraper):

    min_id_goal = 400 # min target for application ids to fetch in one go

    _authority_name = 'Nuneaton'
    _date_from_field = { 'day': 'intFromDay', 'month': 'strFromMonth', 'year': 'intFromYear', }
    _date_to_field = { 'day': 'intToDay', 'month': 'strToMonth', 'year': 'intToYear', }
    _search_form = 'frmSearchByLocationDate'
    _search_fields = { 'strRecordType': 'P' }
    #_request_date_format = '%-d/%B/%Y' only works on linux
    _search_url = 'http://apps.nuneatonandbedworth.gov.uk/bt_nbbc_planning/bt_nbbc_planning_disp.asp'
    _detail_page = 'bt_nbbc_planning_application.asp'
    _scrape_ids = """
    <div class="subheader"> Online Application Register: Applications </div>
         {* <tr> <a href="{{ [records].url|abs }}">
             Ref: {{ [records].uid }} (Planning)
            </a> </tr>
           *}
    <div> This information was last uploaded </div>
    """ # note first table is paging control - but does not appear if only one page
    _link_next = 'Next >'

    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <table class="nbbcTable"> {{ block|html }} </table>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <tr> Application reference: {{ reference }} </tr>
    <tr> Date accepted: {{ date_validated }} </tr>
    <tr> Location: {{ address }} </tr>
    <tr> Description: {{ description }} </tr>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    "<tr> Application type: {{ application_type }} </tr>", # OK
    "<tr> Application status: {{ status }} </tr>", # OK
    "<tr> Date received: {{ date_received }} </tr>", # OK
    "<tr> Officer: {{ case_officer }} </tr>", # OK
    "<tr> Applicant: {{ applicant_name }} </tr>", #OK
    "<tr> Applicant's address: {{ applicant_address }} </tr>", # OK
    "<tr> Agent: {{ agent_name }} </tr>", # OK
    "<tr> Agent's address: {{ agent_address }} </tr>", # OK
    "<tr> Recommendation: {{ decision }} </tr>", # OK
    "<tr> Decision: {{ decision }} </tr>", # OK
    "<tr> Target decision date: {{ target_decision_date }} </tr>", # OK
    "<tr> Decided on: {{ decision_date }} </tr>", # OK
    "<tr> Decided by: {{ decided_by }} </tr>", # OK
    "<tr> Appeal made on: {{ appeal_date }} </tr>", # OK
    "<tr> Appeal result: {{ appeal_result }} </tr>", # OK
    "<tr> Appeal decided on: {{ appeal_decision_date }} </tr>", # OK
    ]
    detail_tests = [
        { 'uid': '030654', 'len': 20 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 26 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 1 } ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        
        fields = {}
        fields.update(self._search_fields)
        dfrom = date_from.strftime('X%d/%B/%Y').replace('X0','X').replace('X','')
        date_parts = dfrom.split('/')
        fields[self._date_from_field['day']] = [ date_parts[0] ]
        fields[self._date_from_field['month']] = [ date_parts[1] ]
        fields[self._date_from_field['year']] = [ date_parts[2] ]
        dto = date_to.strftime('X%d/%B/%Y').replace('X0','X').replace('X','')
        date_parts = dto.split('/')
        fields[self._date_to_field['day']] = [ date_parts[0] ]
        fields[self._date_to_field['month']] = [ date_parts[1] ]
        fields[self._date_to_field['year']] = [ date_parts[2] ]
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        
        #html = response.read()
        #self.logger.debug("ID batch page html: %s", html)
        #try:
        #    result = scrapemark.scrape(self._scrape_max_recs, html)
        #    max_recs = int(result['max_recs'])
        #except:
        #    max_recs = 0
        
        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        #while response and len(final_result) < max_recs and page_count < max_pages:
        while response and page_count < max_pages:
            html = response.read()
            url = response.geturl()
            #self.logger.debug("Batch html: %s" % html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                page_count += 1
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            else:
                self.logger.debug("Empty result after %d pages", page_count)
                break
            #if len(final_result) >= max_recs: break
            try:
                response = self.br.follow_link(text=self._link_next)
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next link after %d pages", page_count)
                break
        
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
            
        return final_result

    def get_html_from_uid(self, uid): 
        url = urlparse.urljoin(self._search_url, self._detail_page) + '?strRecordType=P&strApplicationReference=' + uid
        return self.get_html_from_url(url) 

        

