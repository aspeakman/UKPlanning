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

# also see Redcar and Glamorgan

class KirkleesScraper(base.DateScraper):

    min_id_goal = 400 # min target for application ids to fetch in one go

    _authority_name = 'Kirklees'
    _date_from_field = 'ctl00$ctl00$cphPageBody$cphContent$txtDateFrom'
    _date_to_field = 'ctl00$ctl00$cphPageBody$cphContent$txtDateTo'
    _appno_field = 'ctl00$ctl00$cphPageBody$cphContent$txtSearch'
    _search_form = 'aspnetForm'
    _search_submit = 'ctl00$ctl00$cphPageBody$cphContent$btnAdvSearch'
    _next_fields = { '__EVENTTARGET': 'ctl00$ctl00$cphPageBody$cphContent$dpSearchResultsAbove$ctl02$ctl00', 
            '__EVENTARGUMENT': '', 'ctl00$ctl00$cphPageBody$cphContent$searchAgain': None }
    _search_url = 'http://www.kirklees.gov.uk/beta/planning-applications/search-for-planning-applications/default.aspx'
    _detail_page = 'detail.aspx'
    _scrape_ids = """
    <div id="searchResults"> <ul class="filter-list">
    {* <li> <a href="{{ [records].url|abs }}"> <h4> Application {{ [records].uid }} </h4> </a> </li>
     *}
    </ul> </div>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <div class="page-content"> {{ block|html }} </div>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <span id="ctl00_ctl00_cphPageBody_cphContent_lbl_number_formatted"> {{ reference }} </span>
    <span id="ctl00_ctl00_cphPageBody_cphContent_lbl_development_locality"> {{ address }} </span>
    <span id="ctl00_ctl00_cphPageBody_cphContent_lbl_development_description"> {{ description }} </span>
    <span id="ctl00_ctl00_cphPageBody_cphContent_lbl_received_date"> {{ date_received }} </span>
    <span id="ctl00_ctl00_cphPageBody_cphContent_lbl_registration_date"> {{ date_validated }} </span>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<span id="ctl00_ctl00_cphPageBody_cphContent_lbl_applicant_name"> {{ applicant_name }} </span>',
    '<span id="ctl00_ctl00_cphPageBody_cphContent_lbl_ward"> {{ ward_name }} </span>',
    '<span id="ctl00_ctl00_cphPageBody_cphContent_lbl_agent_name"> {{ agent_name }} </span>',
    '<span id="ctl00_ctl00_cphPageBody_cphContent_lbl_agent_address"> {{ agent_address }} </span>',
    '<span id="ctl00_ctl00_cphPageBody_cphContent_lbl_case_officer"> {{ case_officer }} </span>',
    '<span id="ctl00_ctl00_cphPageBody_cphContent_lbl_public_consultation_start_date"> {{ consultation_start_date }} </span>',
    '<span id="ctl00_ctl00_cphPageBody_cphContent_lbl_public_consultation_end_date"> {{ consultation_end_date }} </span>',
    '<span id="ctl00_ctl00_cphPageBody_cphContent_lbl_decision_date"> {{ decision_date }} </span>',
    '<span id="ctl00_ctl00_cphPageBody_cphContent_lbl_decision_text"> {{ decision }} </span>',
    '<span id="ctl00_ctl00_cphPageBody_cphContent_lbl_appeal_lodged_date"> {{ appeal_date }} </span>',
    'http://map.kirklees.gov.uk/planningMap/map.aspx?lon={{longitude}}&amp;lat={{latitude}}&amp;zoom=',
    ]
    detail_tests = [
        { 'uid': '2012/91840', 'len': 15 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 69 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 14 } ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url + '?advanced_search=true')
        scrapeutils.setup_form(self.br, self._search_form)
        #response = scrapeutils.submit_form(self.br, self._advanced_submit)
        #self.logger.debug("Start html: %s" % response.read())
        
        fields = {}
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._search_submit)
        
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
                scrapeutils.setup_form(self.br, self._search_form, self._next_fields)
                #self.logger.debug("Next page form: %s", str(self.br.form))
                response = scrapeutils.submit_form(self.br)
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next form after %d pages", page_count)
                break
        
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
            
        return final_result

    def get_html_from_uid(self, uid): 
        url = urlparse.urljoin(self._search_url, self._detail_page) + '?id=' + urllib.quote_plus(uid)
        return self.get_html_from_url(url) 

        

