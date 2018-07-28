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
from .. import base
try:
    from ukplanning import scrapeutils
except ImportError:
    import scrapeutils
import urllib

class BrightonScraper(base.DateScraper):

    _authority_name = 'Brighton'
    _date_from_field = 'date_from'
    _date_to_field = 'date_to'
    _search_form = '1'
    _start_fields = { 'accept': '1', }
    _search_fields = { 'dateFilterCol': 'Received', }
    _search_url = 'http://ww3.brighton-hove.gov.uk/index.cfm?request=c1199915&action=showform'
    _applic_url = 'http://ww3.brighton-hove.gov.uk/index.cfm?request=c1199915&action=showDetail&APPLICATION_NUMBER='
    _next_form = '1'
    _next_submit = 'next'
    _scrape_ids = """
    <div class="navContainer" />
    {* <table> <td> {{ [records].uid }} </td>
    <form action="{{ [records].url|abs }}" /> </table>
     *}
    <div class="dspCurrent" />
    """
    _scrape_max_recs = '<p class="records"> {{ max_recs }} records found. </p>'

    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <h1> Planning register </h1> <div class="content"> {{ block|html }} </div> 
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <h2> Application number: {{ reference }} </h2>
    <tr> <td> Address </td> <td> {{ address }} </td> </tr>
    <tr> <td> Received date </td> <td> {{ date_received }} </td> </tr>
    """ 
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<tr> <td> Description </td> <td> {{ description }} </td> </tr>',
    '<tr> <td> Valid date </td> <td>{{ date_validated }} </td> </tr>',
    '<tr> <td> Application type </td> <td> {{ application_type }} </td> </tr>', 
    '<tr> <td> Ward </td> <td> {{ ward_name }} </td> </tr>', 
    '<tr> <td> Status </td> <td> {{ status }} </td> </tr>', 
    '<tr> <td> Target decision date </td> <td> {{ target_decision_date }} </td> </tr>', 
    """<tr> <td> Decision date </td> <td> {{ decision_date }} </td> </tr>
    <tr> <td> Decision </td> <td> {{ decision }} </td> </tr>""", 
    '<tr> <td> Officer </td> <td> {{ case_officer }} </td> </tr>', 
    '<tr> <td> Agent </td> <td> {{ agent_name }} <br> {{ agent_address }} </td> </tr>', 
    '<tr> <td> Applicant </td> <td> {{ applicant_name }} <br> {{ applicant_address }} </td> </tr>',
    '<tr> <td> Development type </td> <td> {{ development_type }} </td> </tr>', 
    '<tr> <td> Development types </td> <td> {{ development_type }} </td> </tr>', 
    '<tr> <td> Conservation area </td> <td> {{ district }} </td> </tr>',
    '<tr> <td> Delegated </td> <td> {{ decided_by }} </td> </tr>',
    ]
    detail_tests = [
        { 'uid': 'BH2011/02336', 'len': 17 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 69 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 14 } ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url, urllib.urlencode(self._start_fields))
        #self.logger.debug("Start html: %s", response.read())

        fields = {}
        fields.update(self._search_fields)
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        
        html = response.read()
        #self.logger.debug("ID batch page html: %s", html)
        try:
            result = scrapemark.scrape(self._scrape_max_recs, html)
            max_recs = int(result['max_recs'])
        except:
            max_recs = 0
            
        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        while response and len(final_result) < max_recs and page_count < max_pages:
            url = response.geturl()
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
                scrapeutils.setup_form(self.br, self._next_form)
                self.logger.debug("ID next form: %s", str(self.br.form))
                response = scrapeutils.submit_form(self.br, self._next_submit)
                html = response.read()
                #self.logger.debug("ID next page html: %s", html)
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next form after %d pages", page_count)
                break
        
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
            
        return final_result
        
    def get_html_from_uid(self, uid):
        url = self._applic_url + urllib.quote_plus(uid)
        return self.get_html_from_url(url) 
        
    def _get_details(self, html, this_url):
        """ Scrapes detailed information for one record given html and url 
        - this is an optional hook to allow data from multiple linked pages to be merged """
        result = self._get_detail(html, this_url)
        if 'scrape_error' in result or result.get('description') or not result.get('application_type'):
            return result
        result['description'] = result['application_type']
        return result

        

