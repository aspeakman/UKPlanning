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

class LeicesterScraper(base.DateScraper):

    min_id_goal = 400 # min target for application ids to fetch in one go

    _authority_name = 'Leicester'
    _handler = 'etree'
    _date_from_field = 'ctl00$ContentPlaceHolder1$txtDateRecfrom' # note lower case f
    _date_to_field = 'ctl00$ContentPlaceHolder1$txtDateRecTo'
    _search_form = 'aspnetForm'
    _search_url = 'http://rcweb.leicester.gov.uk/planning/onlinequery/mainsearch.aspx'
    _detail_page = 'Details.aspx'
    _next_target = 'ctl00$ContentPlaceHolder1$GridView1'
    _scrape_ids = """
    <table id="ctl00_ContentPlaceHolder1_GridView1"> 
    {* <tr valign="top">
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td> <td />
    </tr> *}
    </table>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <form id="aspnetForm"> {{ block|html }} </form>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <span id="ctl00_ContentPlaceHolder1_FormView1_Label1"> {{ reference }} </span>
    <span id="ctl00_ContentPlaceHolder1_FormView1_locationLabel"> {{ address }} </span>
    <span id="ctl00_ContentPlaceHolder1_FormView1_proposalLabel"> {{ description }} </span>
    <span id="ctl00_ContentPlaceHolder1_FormView1_received_dateLabel"> {{ date_received }} </span>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<span id="ctl00_ContentPlaceHolder1_FormView1_uprnLabel"> {{ uprn }} </span>',
    '<span id="ctl00_ContentPlaceHolder1_FormView1_received_complete_dateLabel"> {{ date_validated }} </span>',
    '<span id="ctl00_ContentPlaceHolder1_FormView1_Label17"> {{ application_type }} </span>',
    '<span id="ctl00_ContentPlaceHolder1_FormView1_ward_descriptionLabel"> {{ ward_name }} </span>',   
    '<span id="ctl00_ContentPlaceHolder1_FormView1_Label2"> {{ applicant_name }} </span>',
    '<span id="ctl00_ContentPlaceHolder1_FormView1_agentLabel"> {{ agent_name }} </span>',
    '<span id="ctl00_ContentPlaceHolder1_FormView1_applicants_addressLabel"> {{ applicant_address }} </span>',
    '<span id="ctl00_ContentPlaceHolder1_FormView1_agents_addressLabel"> {{ agent_address }} </span>',
    '<span id="ctl00_ContentPlaceHolder1_FormView1_case_officerLabel"> {{ case_officer }} </span>', 
    '<span id="ctl00_ContentPlaceHolder1_FormView1_neighbour_letter_dateLabel"> {{ neighbour_consultation_start_date }} </span>',
    '<span id="ctl00_ContentPlaceHolder1_FormView1_neighbour_expiry_dateLabel"> {{ neighbour_consultation_end_date }} </span>',
    '<span id="ctl00_ContentPlaceHolder1_FormView1_decision_descriptionLabel"> {{ decision }} </span>',
    '<span id="ctl00_ContentPlaceHolder1_FormView1_committee_dateLabel"> {{ metting_date }} </span>',    
    '<span id="ctl00_ContentPlaceHolder1_FormView1_decision_dateLabel"> {{ decision_date }} </span>',
    '<span id="ctl00_ContentPlaceHolder1_FormView1_appeal_lodged_dateLabel"> {{ appeal_date }} </span>',
    '<span id="ctl00_ContentPlaceHolder1_FormView1_appeal_decisionLabel"> {{ appeal_result }} </span>',
    '<span id="ctl00_ContentPlaceHolder1_FormView1_appeal_decision_dateLabel"> {{ appeal_decision_date }} </span>',
    ]
    detail_tests = [
        { 'uid': '20121265', 'len': 19 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '03/09/2012', 'to': '29/09/2012', 'len': 142 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 7 } ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s" % response.read())
        
        fields = {}
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
            
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
                fields = { '__EVENTTARGET': self._next_target }
                fields['__EVENTARGUMENT'] = 'Page$' + str(page_count+1)
                scrapeutils.setup_form(self.br, self._search_form, fields)
                self.logger.debug("Next page form: %s", str(self.br.form))
                response = scrapeutils.submit_form(self.br)
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next form after %d pages", page_count)
                break
        
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
            
        return final_result

    def get_html_from_uid(self, uid): 
        url = urlparse.urljoin(self._search_url, self._detail_page) + '?AppNo=' + urllib.quote_plus(uid)
        return self.get_html_from_url(url) 

        

