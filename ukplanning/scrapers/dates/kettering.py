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

class KetteringScraper(base.DateScraper):

    min_id_goal = 200 # min target for application ids to fetch in one go
    
    _authority_name = 'Kettering'
    _search_url = 'http://www.kettering.gov.uk/site/scripts/planning.php'
    _list_page = 'planning_list.php'
    _applic_url = 'http://www.kettering.gov.uk/planningApplication?appNumber='
    _date_from_field = {
        'day': 'fromDay',
        'month': 'fromMonth',
        'year': 'fromYear',
        }
    _date_to_field = {
        'day': 'toDay',
        'month': 'toMonth',
        'year': 'toYear',
        }
    _search_form = '1'
    _search_fields = { 'submitDateWeekly': 'Go' }
    _ref_search = { 'search_ref': 'Search',  }
    _ref_field = 'reference'
    _next_link = 'Next'
    _scrape_max_recs = '<h2> Applications Found: </h2>  <p> of {{ max_recs }} results </p>'
    _scrape_ids = """
    <table summary="Planning Applications"> <tbody>
    {* <tr> <td> <a href="{{ [records].url|abs }}">
    {{ [records].uid }} </a> </td> </tr> *}
    </tbody> </table>
    """
    _scrape_data_block = """
    <div id="content"> {{ block|html }} </td> </tr>
    """
    _scrape_min_data = """
    <h1> {{ reference }} </h1>
    <tr> <td> Location </td> <td> {{ address }} </td> </tr>
    <tr> <td> Proposal </td> <td> {{ description }} </td> </tr>
    <tr> <td> Date received </td> <td> {{ date_received }} </td> </tr>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<tr> <td> Validation/registration Date </td> <td> {{ date_validated }} </td> </tr>',
    """<tr> <td> Decided on </td> <td> {{ decision_date }} </td> </tr>
    <tr> <td> Decision </td> <td> {{ decision }} </td> </tr>""",
    '<tr> <td> Target Decision Date </td> <td> {{ target_decision_date }} </td> </tr>',
    '<tr> <td> Applicant Name </td> <td> {{ applicant_name }} </td> </tr>',
    '<tr> <td> Case Officer </td> <td> {{ case_officer }} </td> </tr>',
    '<tr> <td> Ward </td> <td> {{ ward_name }} </td> </tr>',
    '<tr> <td> Parish </td> <td> {{ parish }} </td> </tr>',
    '<tr> <td> Decision level </td> <td> {{ decided_by }} </td> </tr>',
    '<tr> <td> Application Type </td> <td> {{ application_type }} </td> </tr>',
    '<tr> <td> Neighbours/Consultations Sent on </td> <td> {{ neighbour_consultation_start_date }} </td> </tr>',
    '<tr> <td> Expiry Date for neighbours/consultations </td> <td> {{ neighbour_consultation_end_date }} </td> </tr>',
    '<tr> <td> Site Notice displayed on </td> <td> {{ site_notice_start_date }} </td> </tr>',
    '<tr> <td> Expiry Date for Site Notice </td> <td> {{ site_notice_end_date }} </td> </tr>',
    ]
    detail_tests = [
        { 'uid': 'KET/2011/0680', 'len': 18 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 22 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]

    def get_id_batch (self, date_from, date_to):
        
        final_result = []
        
        fields = {}
        fields.update(self._search_fields)
        date_from = date_from.strftime(self._request_date_format)
        date_parts = date_from.split('/')
        fields[self._date_from_field['day']] = date_parts[0]
        fields[self._date_from_field['month']] = date_parts[1]
        fields[self._date_from_field['year']] = date_parts[2]
        date_to = date_to.strftime(self._request_date_format)
        date_parts = date_to.split('/')
        fields[self._date_to_field['day']] = date_parts[0]
        fields[self._date_to_field['month']] = date_parts[1]
        fields[self._date_to_field['year']] = date_parts[2]
        #scrapeutils.setup_form(self.br, self._search_form, fields)
        #self.logger.debug("ID batch form: %s", str(self.br.form))
        #response = scrapeutils.submit_form(self.br)
        url = urlparse.urljoin(self._search_url, self._list_page) + '?' + urllib.urlencode(fields)
        self.logger.debug("Query url: %s", url)
        response = self.br.open(url)
        
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
                response = self.br.follow_link(text=self._next_link)
                html = response.read()
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next link after %d pages", page_count)
                break
                
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
        
        return final_result

    def get_html_from_uid(self, uid):
        url = self._applic_url + urllib.quote_plus(uid)
        return self.get_html_from_url(url)
            
