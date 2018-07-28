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
from datetime import date
import re

# works from one long list of all applications - also see Pembroke Coast and Hampshire

class ScillyIslesScraper(base.ListScraper):
    
    current_span = 10 # min number of records to get when gathering current ids
    batch_size = 60
    url_first = False
    
    _authority_name = 'ScillyIsles'
    _applic_url = 'http://www.scilly.gov.uk/planning-application/'
    _search_url = 'http://www.scilly.gov.uk/planning-development/planning-applications'
    _max_ever = 300
    _scrape_ids = """
    <table class="views-table"> <tr /> 
    {* <tr> <td> <a href="{{ [records].url|abs }}"> Planning application: {{ [records].uid }} </a> </td>
    </tr> *}
    </table>
    """
    #_scrape_other_pages = '<h2> Pages </h2> <ul class="pager"> {* <li class="pager-item"> <a href="{{ [other_pages] }}"> *} </ul>'
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <div id="page"> {{ block|html }} </div>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <div class="field field-name-body"> {{ description }} <h4 /> </div>
    <div class="field field-name-field-site-address"> <div class="field-items"> {{ address }} </div> </div>
    <div class="field field-name-field-date-received"> <div class="field-items"> {{ date_received }} </div> </div>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<div class="field field-name-field-list-date"> <div class="field-items"> {{ date_validated }} </div> </div>',
    '<div class="field field-name-field-planning-app-num"> <div class="field-items"> {{ reference }} </div> </div>',
    '<div class="field field-name-field-planning-app-type"> <div class="field-items"> {{ application_type }} </div> </div>',
    '<div class="field field-name-field-decision"> <div class="field-items"> {{ decision }} </div> </div>',
    '<div class="field field-name-field-planning-applicant-name"> <div class="field-items"> {{ applicant_name }} </div> </div>',
    '<div class="field field-name-field-applicant-address"> <div class="field-items"> {{ applicant_address }} </div> </div>',
    '<div class="field field-name-field-agent-name"> <div class="field-items"> {{ agent_name }} </div> </div>',
    '<div class="field field-name-field-agent-address"> <div class="field-items"> {{ agent_address }} </div> </div>',
    '<div class="field field-name-field-decision-date"> <div class="field-items"> {{ decision_date }} </div> </div>',
    '<div class="field field-name-field-target-date"> <div class="field-items"> {{ target_decision_date }} </div> </div>',
    '<div class="field field-name-field-committee-date"> <div class="field-items"> {{ meeting_date }} </div> </div>',
    ]
    detail_tests = [
        { 'uid': 'P/14/018', 'len': 14 } ]
    batch_tests = [ 
        { 'from': '6', 'to': '36', 'len': 31 }, ]

    def get_id_records (self, request_from, request_to, max_recs):
        if not request_from or not request_to or not max_recs:
            return [], None, None # if any parameter invalid - try again next time
        final_result = []
        from_rec = int(request_from)
        to_rec = int(request_to)
        this_max = int(max_recs)
        if from_rec < 1:
            if to_rec < 1: # both too small
                return [], None, None
            from_rec = 1
        if to_rec > this_max:
            if from_rec > this_max: # both too large
                return [], None, None
            to_rec = this_max
            
        response = self.br.open(self._search_url)
        html = response.read()
            
        #try:
        #    result = scrapemark.scrape(self._scrape_other_pages, html)
        #    page_list = [ x for x in result['other_pages'] if x ]
        #except:
        #    page_list = []
        #print page_list
        
        # just get all possible records each time and then sort them by date
        page_count = 0
        max_pages = 50 # guard against infinite loop, note: max_ever must be < max_pages * 10
        while response and page_count < max_pages:
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
            try:
                next_url = self._search_url + '?page=' + str(page_count)
                response = self.br.open(next_url) # one fixed page of records
                #if not page_list:
                #    break
                #response = self.br.open(page_list.pop()) # one fixed page of records
                html = response.read()
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next page after %d pages", page_count)
                break
            
        if final_result:
            fret = sorted(final_result, key=lambda k: k.get('uid'))
            return fret[from_rec-1:to_rec], from_rec, to_rec
        else:
            return [], None, None # list scraper - so empty result is always invalid
        
    @property
    def max_sequence (self):
        all_applics, fr, to = self.get_id_records(1,self._max_ever,self._max_ever)
        num_recs = len(all_applics)
        self.logger.debug('Number of records %d' % num_recs)
        return num_recs
        
    def get_html_from_uid (self, uid):
        uid = uid.replace('/', '')
        url = self._applic_url + 'planning-application-' + uid.lower()
        html, url = self.get_html_from_url(url)
        result = scrapemark.scrape(self._scrape_min_data, html, url)
        if result:
            return html, url
        else:
            return self.get_html_from_url(url + '-0')
            

            

