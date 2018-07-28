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
import urllib, urlparse

# also see Yorkshire Dales 

class DartmoorScraper(base.DateScraper):

    data_start_target = '2000-01-01'
    min_id_goal = 150 # min target for application ids to fetch in one go
    batch_size = 28 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 28 # start this number of days ago when gathering current ids
    
    _authority_name = 'Dartmoor'
    _comment = 'was custom ListScraper up to Aug 2016'
    _handler = 'etree'
    _search_url = 'http://www.dartmoor.gov.uk/planning/planning-application-search'
    _applic_url = 'http://www.dartmoor.gov.uk/living-and-working/planning/search-for-an-application/db-links/detailed-application-result?AppNo='
    _next_url = 'http://www.dartmoor.gov.uk/living-and-working/planning/search-for-an-application/db-links/planning-searches/search-applications?result_776602_result_page='
    _date_from_field = { 'day': 'q868954:q4', 'month': 'q868954:q5', 'year': 'q868954:q6', }
    _date_to_field = { 'day': 'q868954:q7', 'month': 'q868954:q8', 'year': 'q868954:q9', }
    _search_form = '1'
    _search_fields = { 'q868954:q10[]': '0', 'q868954:q3': 'ValidDate', 
        'parish': '', 'q868954:q1': '', 'q868954:q2': '',
        }
    _search_submit = 'form_email_868954_submit'
    _scrape_max_recs = '<p> <strong> {{ max_recs }} </strong> results found </p>'
    _scrape_ids = """
    <article class="main-content"> <table> <tr/>
    {* <tr> <td/>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    </tr> *}
    </table> </article>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = '<article class="main-content"> {{ block|html }} </article>'
    # the minimum acceptable valid dataset on the details page
    _scrape_min_data = """
    <table> <th> Application no: {{ reference }} </th>
    <td> <strong> Site Address </strong> </td> <td> {{ address }} </td> 
    <td> <strong> Proposal </strong> </td> <td> {{ description }} </td></table>
    <table> <tr> <td> Date valid </td> </tr> <tr> <td> {{ date_validated }} </td> </tr> </table>
    """
    # other optional parameters common to all scrapers can appear on the details page
    _scrape_optional_data = [
    '<td> <strong> Parish </strong> </td> <td> {{ parish }} </td>',
    '<td> <strong> Applicant </strong> </td> <td> {{ applicant_name }} </td>',
    '<td> <strong> Case Officer </strong> </td> <td> {{ case_officer }} </td>',
    '<td> <strong> Target Date For Decision </strong> </td> <td> {{ target_decision_date }} </td>',
    '<tr> <td> Consultation end </td> </tr> <tr> <td/> <td> {{ consultation_end_date }} </td> </tr>',
    '<tr> <td> Decision date </td> </tr> <tr> <td/> <td/> <td> {{ decision_date }} </td> </tr>',
    '<tr> <td> Decision/Status </td> </tr> <tr> <td/> <td/> <td/> <td> {{ status }} </td> </tr>',
    '<tr> <td> Decision/Status </td> </tr> <tr> <td/> <td/> <td/> <td> {{ decision }} </td> </tr>',
    ]
    detail_tests = [
        { 'uid': '0045/13', 'len': 13 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '09/09/2012', 'to': '29/09/2012', 'len': 29 }, 
        { 'from': '24/08/2012', 'to': '24/08/2012', 'len': 2 },
    ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        #self.logger.debug("ID batch start html: %s", response.read())
        
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
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._search_submit)
        
        html = response.read()
        #self.logger.debug("ID batch page html: %s", html)
        try:
            result = scrapemark.scrape(self._scrape_max_recs, html)
            max_recs = int(result['max_recs'])
        except:
            max_recs = 0
        
        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        while response and page_count < max_pages:
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
            if len(final_result) >= max_recs: break
            try:
                action_url =  self._next_url + str(page_count + 1)
                response = self.br.open(self._search_url)
                scrapeutils.setup_form(self.br, self._search_form, fields, action_url)
                response = scrapeutils.submit_form(self.br, self._search_submit)
                html = response.read()
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next link after %d pages", page_count)
                break
        
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
     
        return final_result

    def get_html_from_uid(self, uid): 
        url =  self._applic_url + urllib.quote_plus(uid)
        return self.get_html_from_url(url)
        


        

