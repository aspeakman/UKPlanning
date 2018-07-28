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

# note this site returns some duplicate values in the list of ids on a date search

class CheshireEastScraper(base.DateScraper):
    
    min_id_goal = 350 # min target for application ids to fetch in one go

    _authority_name = 'CheshireEast'
    _search_url = 'http://planning.cheshireeast.gov.uk/AdvancedSearch.aspx'
    _detail_page = 'applicationdetails.aspx'
    _date_from_field = 'ctl00$ContentPlaceHolder1$txtDateRegisteredFrom'
    _date_to_field = 'ctl00$ContentPlaceHolder1$txtDateRegisteredTo'
    _next_link = 'Next page'
    _search_form = '0'
    _search_submit = 'ctl00$ContentPlaceHolder1$btnAdvancedSearch'
    _search_fields = {
        'ctl00$ContentPlaceHolder1$optResultsTo': 'map',
        'ctl00$ContentPlaceHolder1$txtJSEnabled': '1',
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        }
    _scrape_ids = """
    <div id="searchResults">
    {* <div>
    <p> <a href="{{ [records].url|abs }}"> Planning ref {{ [records].uid }} </a> </p>
    </div> *}
    </div>
    """
    _scrape_max_recs = '<span id="ContentPlaceHolder1_lblSearchSummary">Found {{ max_recs }} results. </span>'
    _scrape_data_block = """
    <div id="spanMain"> {{ block|html }} </div>
    """
    _scrape_min_data = """
    <h3> Reference Number </h3> <span> {{ reference }} </span>
    <h3> Location </h3> <span> {{ address }} </span>
    <h3> Proposal </h3> <span> {{ description }} </span>
    <h3> Date Registered </h3> <p> {{ date_validated }} </p>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<h3> Type of Application </h3> <span> {{ application_type }} </span>',
    '<h3> Case Officer </h3> <span> {{ case_officer }} </span>',
    '<h3> Status </h3> <span> {{ status }} </span>',
    '<h3> Ward / Parish </h3> <span> {{ ward_name }} / {{ parish }} </span>', 
    '<h3> Decision / Date Decision Made </h3> <span> {{ decision }} / {{ decision_date }} </span>',
    '<h3> Committee Date </h3> <p> {{ meeting_date }} </p>',
    '<h3> Last Date For Submitting Comments </h3> <p> {{ consultation_end_date }} </p>',
    '<h3> Decision Target Date </h3> <p> {{ target_decision_date }} </p>',
    '<h3> Applicant Name </h3> <span> {{ applicant_name }} </span>',
    '<h3> Agent Name </h3> <span> {{ agent_name }} </span>',
    '<h3> Applicant Address </h3> <span> {{ applicant_address }} </span>',
    '<h3> Agent Address </h3> <span> {{ agent_address }} </span>',
    '<iframe id="planningLocn" src="http://maps.cheshire.gov.uk/ce/planning/?easting={{easting}}&northing={{northing}}" />'
    ]
    detail_tests = [
        { 'uid': '11/3076N', 'len': 21 },
        { 'uid': '17/2580D', 'len': 19 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 82 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 24 } ]

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
        id_list = []
        while response and len(final_result) < max_recs and page_count < max_pages:
            url = response.geturl()
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                page_count += 1
                self._clean_ids(result['records'])
                # add IDs one by one and test for duplicates
                for r in result['records']:
                    if r['uid'] not in id_list:
                        final_result.append(r)
                        id_list.append(r['uid'])
            else:
                self.logger.debug("Empty result after %d pages", page_count)
                break
            if len(final_result) >= max_recs: break
            try:
                response = self.br.follow_link(text=self._next_link)
                html = response.read()
                #self.logger.debug("ID next page html: %s", html)
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next link after %d pages", page_count)
                break
        
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
            
        return final_result
        
    def get_html_from_uid (self, uid):
        url = urlparse.urljoin(self._search_url, self._detail_page) + '?pr=' + urllib.quote_plus(uid)    
        return self.get_html_from_url(url) 
        
        

