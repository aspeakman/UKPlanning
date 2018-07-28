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
import re
import urllib

class TamesideScraper(base.DateScraper):

    #data_start_target = '2007-01-01'
    min_id_goal = 350 # min target for application ids to fetch in one go
    
    _authority_name = 'Tameside'
    _search_url = 'http://public.tameside.gov.uk/plan/f422planapp.asp'
    _uid_only = True # these can only access applications via uid not url
    _date_from_field = {
        'day': 'F08_Fdd',
        'month': 'F09_Fmm',
        'year': 'F10_Fyyyy',
        }
    _date_to_field = {
        'day': 'F11_Tdd',
        'month': 'F12_Tmm',
        'year': 'F13_Tyyyy',
        }
    _ref_field = 'F01_AppNo'
    #_search_fields = { 'F02_District': [ '99' ], }
    _search_fields = { 'F02_District': '99', 'action': 'Home', 'submit': 'Find', }
    _next_fields = { 'submit': 'More' }
    _next_form = 'form3'
    _search_form = '1'
    _search_submit = 'submit'
    _response_date_format = '%d/%m/%y'
    _scrape_ids = """
    <div class="content1">
    {* <table> <tr> <td> Application Number </td> <td> {{ [records].uid }} </td> </tr>
    </table> *}
    </div>
    """
    _scrape_data_block = """
    <form action="f422planapp.asp"> {{ block|html }} </table>
    """
    _scrape_min_data = """
    <tr> <td> Application Number </td> <td> {{ reference }} </td> <td> Date of Application </td> <td> {{ date_validated }} </td> </tr>
    <tr> <td> Proposal </td> <td> {{ description }} </td> </tr>
    <tr> <td> Site </td> <td> {{ address }} </td> </tr>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<tr> <td> Case Officer </td> <td> {{ case_officer }} </td> </tr>',
    '<tr> <td> Status </td> <td> {{ status }} </td> </tr>',
    '<tr> <td> Applicant </td> <td> {{ applicant_name }} </td> <td> {{ applicant_address|html }} </td> </tr>',
    '<input name="AgentName0" value ="{{ agent_name }}">',
    '<input name="AgentAddress0" value ="{{ agent_address }}">',
    '<input name="Decision0" value"{{ decision }}">',
    '<input name="DecisionDate0" value=" On {{ decision_date }}">',
    '<input name="AppRec0" value="{{ date_received }}">',
    '<input name="AppVal0" value="{{ date_validated }}">',
    '<input name="StartCons0" value="{{ consultation_start_date }}">',
    '<input name="TargetDec0" value="{{ target_decision_date }}">',
    '<input name="ExpiryDate0" value="{{ application_expires_date }}">',
    ]
    detail_tests = [
        { 'uid': '11/00616/FUL', 'len': 12 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2009', 'to': '19/09/2009', 'len': 17 }, 
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 25 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]

    def get_id_batch (self, date_from, date_to):
        
        final_result = []
        
        response = self.br.open(self._search_url)
        
        fields = {}
        fields.update(self._search_fields)
        date_from = date_from.strftime(self._request_date_format)
        date_parts = date_from.split('/')
        #fields[self._date_from_field['day']] = [ date_parts[0] ]
        #fields[self._date_from_field['month']] = [ date_parts[1] ]
        #fields[self._date_from_field['year']] = [ date_parts[2] ]
        fields[self._date_from_field['day']] = date_parts[0]
        fields[self._date_from_field['month']] = date_parts[1]
        fields[self._date_from_field['year']] = date_parts[2]
        date_to = date_to.strftime(self._request_date_format)
        date_parts = date_to.split('/')
        #fields[self._date_to_field['day']] = [ date_parts[0] ]
        #fields[self._date_to_field['month']] = [ date_parts[1] ]
        #fields[self._date_to_field['year']] = [ date_parts[2] ]
        fields[self._date_to_field['day']] = date_parts[0]
        fields[self._date_to_field['month']] = date_parts[1]
        fields[self._date_to_field['year']] = date_parts[2]
        #scrapeutils.setup_form(self.br, self._search_form, fields)
        #self.logger.debug("ID batch form: %s", str(self.br.form))
        #response = scrapeutils.submit_form(self.br, self._search_submit)
        
        response = self.br.open(self._search_url, urllib.urlencode(fields))
        
        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        while response and page_count < max_pages:
            url = response.geturl()
            html = response.read()
            self.logger.debug("Batch html: %s" % html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                page_count += 1
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            else:
                self.logger.debug("Empty result after %d pages", page_count)
                break
            try:
                scrapeutils.setup_form(self.br, self._next_form, self._next_fields)
                self.logger.debug("ID next form: %s", str(self.br.form))
                response = scrapeutils.submit_form(self.br)
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next form after %d pages", page_count)
                break
                
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
        
        return final_result

    def get_html_from_uid (self, uid):
        response = self.br.open(self._search_url)
        #self.logger.debug("ID detail start html: %s", response.read())
        fields = {  self._ref_field: uid }
        scrapeutils.setup_form(self.br, self._search_form, fields)
        #self.logger.debug("Get UID form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._search_submit)
        return self._get_html(response)

            
