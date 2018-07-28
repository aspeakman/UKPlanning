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

# also see Dartmoor

class YorkshireDalesScraper(base.DateScraper):

    data_start_target = '2000-02-01'
    min_id_goal = 150 # min target for application ids to fetch in one go
    batch_size = 28 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 28 # start this number of days ago when gathering current ids
    
    _authority_name = 'YorkshireDales'
    _handler = 'etree'
    _search_url = 'http://www.yorkshiredales.org.uk/living-and-working/planning/planning-applications'
    _results_url = 'http://www.yorkshiredales.org.uk/living-and-working/planning/planning-applications/application-search-results'
    _applic_url = 'http://www.yorkshiredales.org.uk/living-and-working/planning/planning-applications/application-details?appNo='
    _date_from_field = { 'day': 'q457814:q7', 'month': 'q457814:q8', 'year': 'q457814:q9', }
    _date_to_field = { 'day': 'q457814:q10', 'month': 'q457814:q11', 'year': 'q457814:q12', }
    _search_form = '2'
    _search_fields = { 'q457814:q6[]': '0', 'q457814:q14': 'ValidDate', 
        'form_email_457814_submit': '   Start your search   ',
        'parish': '', 'q457814:q1': '', 'q457814:q2': '',
        'q457814:q17': 'All', }
    _link_next = 'Next page'
    _scrape_ids = """
    <div class="content"> 
    {* <div class="planningApplication">
    <div class="applicationNo"> <a href="{{ [records].url|abs }}">
    {{ [records].uid }} </a> </div>
    </div> *}
    </div>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = '<div class="content"> {{ block|html }} </div>'
    # the minimum acceptable valid dataset on the details page
    _scrape_min_data = """
    <div> <div> Application Number </div> <div> {{ reference }} </div> </div>
    <div> <div> Address </div> <div> {{ address }} </div> </div>
    <div> <div> Proposal </div> <div> {{ description }} </div> </div>
    <div class="applicationDetailsDateReceived" />
    <div class="applicationDetailsDateReceived"> {{ date_received }} </div>
    <div class="applicationDetailsDateValid"> {{ date_validated }} </div>
    """
    # other optional parameters common to all scrapers can appear on the details page
    _scrape_optional_data = [
    '<div> <div> Application Type </div> <div> {{ application_type }} </div> </div>',
    '<div> <div> District </div> <div> {{ district }} </div> </div>',
    '<div> <div> Parish </div> <div> {{ parish }} </div> </div>',
    '<div> <div> Case Officer </div> <div> {{ case_officer }} </div> </div>',
    '<div> <div> Planning Officer Notes </div> <div> {{ status }} </div> </div>',
    '<div> <div> Grid Reference </div> <div> {{ easting }} , {{ northing }} </div> </div>', 
    '<div> <div> Determined By </div> <div> {{ decided_by }} </div> </div>',
    '<div> <div> Target Date For Decision </div> <div> {{ target_decision_date }} </div> </div>',
    """<div class="applicationDetailsDateConsult" /> <div class="applicationDetailsDateConsult" />
    <div class="applicationDetailsDateConsult"> {{ consultation_start_date }} </div>
    <div class="applicationDetailsDateConsult"> {{ consultation_end_date }} </div>""",
    """<div class="applicationDetailsDateDecision" />
    <div class="applicationDetailsDateDecision"> {{ decision_date }} </div>
    <div class="applicationDetailsDecision"> {{ decision }} </div>""",
    ]
    detail_tests = [
        { 'uid': 'C/33/192J', 'len': 17 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 29 }, 
        { 'from': '23/08/2012', 'to': '23/08/2012', 'len': 1 },
        { 'from': '23/08/2016', 'to': '10/09/2016', 'len': 34 },
    ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        #response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s" % response.read())
        
        # fix buggy option list
        #html = response.get_data()
        #html = html.replace('<option value="7">8</option>', '<option value="7">7</option> <option value="8">8</option>')
        #response.set_data(html)
        #self.br.set_response(response)
        
        fields = {}
        fields.update(self._search_fields)
        dfrom = date_from.strftime('X%d/%B/%Y').replace('X0','X').replace('X','')
        date_parts = dfrom.split('/')
        fields[self._date_from_field['day']] = date_parts[0]
        fields[self._date_from_field['month']] = date_parts[1]
        fields[self._date_from_field['year']] = date_parts[2]
        dto = date_to.strftime('X%d/%B/%Y').replace('X0','X').replace('X','')
        date_parts = dto.split('/')
        fields[self._date_to_field['day']] = date_parts[0]
        fields[self._date_to_field['month']] = date_parts[1]
        fields[self._date_to_field['year']] = date_parts[2]
        #scrapeutils.setup_form(self.br, self._search_form, fields)
        #self.logger.debug("ID batch form: %s", str(self.br.form))
        #response = scrapeutils.submit_form(self.br)
        
        url = self._results_url + '?' + urllib.urlencode(fields)
        #self.logger.debug("Result url: %s" % url)
        response = self.br.open(url)
        
        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
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
            try:
                response = self.br.follow_link(text=self._link_next)
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next link after %d pages", page_count)
                break
        
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
     
        return final_result

    def get_html_from_uid(self, uid): 
        url =  self._applic_url + urllib.quote_plus(uid)
        return self.get_html_from_url(url)
        
    def _get_html(self, response):
        """ Return HTML and URL given the website response """
        html = response.read()
        #self.logger.debug("Original html: %s" % html)
        html = html.replace('>1/1/1970<', '><')
        html = html.replace('>01/01/1970<', '><') # kludge bad date fix
        url = response.geturl()
        return html, url

        

