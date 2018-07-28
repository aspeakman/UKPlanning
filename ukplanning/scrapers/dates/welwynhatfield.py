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
import urllib

# also see Wychavon, Lancashire, Nottinghamshire, Northumberland Park, Devon and CCED = Christchurch and East Dorset

class WelwynHatfieldScraper(base.DateScraper):

    batch_size = 28 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 28 # start this number of days ago when gathering current ids
    min_id_goal = 200 # min target for application ids to fetch in one go
    
    _authority_name = 'WelwynHatfield'
    _comment = 'was Fastweb'
    _date_from_field3 = 'ctl00_ContentPlaceHolder1_txtDateReceivedFrom_dateInput_ClientState'
    _date_to_field3 = 'ctl00_ContentPlaceHolder1_txtDateReceivedTo_dateInput_ClientState'
    _request_date_format3 = '{"enabled":true,"emptyMessage":"","validationText":"%Y-%m-%d-00-00-00","valueAsString":"%Y-%m-%d-00-00-00","minDateStr":"1980-01-01-00-00-00","maxDateStr":"2099-12-31-00-00-00","lastSetTextBoxValue":"%d/%m/%Y"}'          
    _date_from_field2 = 'ctl00$ContentPlaceHolder1$txtDateReceivedFrom'
    _date_to_field2 = 'ctl00$ContentPlaceHolder1$txtDateReceivedTo'
    _request_date_format2 = '%Y-%m-%d'
    _date_from_field = 'ctl00$ContentPlaceHolder1$txtDateReceivedFrom$dateInput'
    _date_to_field = 'ctl00$ContentPlaceHolder1$txtDateReceivedTo$dateInput'
    _search_fields = { '__EVENTTARGET': '', '__EVENTARGUMENT': '' } 
    _search_form = 'aspnetForm'
    #_start_fields = { 'ctl00$MainContent$radSearchType': 'ADV' }
    #_submit_continue = "ctl00$MainContent$btnContinue"
    _submit_control = 'ctl00$ContentPlaceHolder1$Button3'
    _ref_submit = 'ctl00$ContentPlaceHolder1$btnSearch2'
    _ref_field = 'ctl00$ContentPlaceHolder1$txtAppNumber'
    _submit_next = 'ctl00$ContentPlaceHolder1$lvResults$RadDataPager1$ctl02$NextButton'
    
    _search_url = 'http://planning.welhat.gov.uk/planhome.aspx'
    _applic_url = 'http://planning.welhat.gov.uk/plandisp.aspx'
    
    _scrape_max_pages = '<div class="rdpWrap"> of {{ max_pages }} </div>'
    _scrape_ids = """
    <div id="news_results_list">
        {* <div class="emphasise-area">
        <h2> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </h2> 
        </div>  *}
    </div>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <div id="ctl00_ContentPlaceHolder1_RadMultiPage1"> {{ block|html }} </div>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <span> Application No </span> <p> {{ reference }} </p>
    <span> Address </span> <p> {{ address }} </p>
    <span> Proposal </span> <p> {{ description }} </p>
    <span> Received Date </span> <p> {{ date_received }} </p>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<span> Valid Date </span> <p> {{ date_validated }} </p>',
    '<span> Status </span> <p> {{ status }} </p>',
    '<span> Case Officer </span> <p> {{ case_officer }} </p>',
    '<span> Type </span> <p> {{ application_type }} </p>',
    '<span> Committee Date </span> <p> {{ meeting_date }} </p>',
    '<span> Committee/ Delegated </span> <p> {{ decided_by }} </p>',
    '<span> UPRN </span> <p> {{ uprn }} </p>', 
    """<span> Decision </span> <p> {{ decision }} </p>
    <span> Decision Date </span> <p> {{ decision_date }} </p>""",
    '<span> Issue Date </span> <p> {{ decision_issued_date }} </p>',
    '<span> Neighbour Expiry </span> <p> {{ neighbour_consultation_end_date }} </p>', 
    '<span> Advert Expiry </span> <p> {{ latest_advertisement_expiry_date }} </p>', 
    '<span> Site Notice Expiry </span> <p> {{ site_notice_end_date }} </p>', 
    '<span> Easting </span> <p> {{ easting }} </p>',
    '<span> Northing </span> <p> {{ northing }} </p>',
    '<span> Ward </span> <p> {{ ward_name }} </p>',
    '<span> Parish </span> <p> {{ parish }} </p>',
    '<span> Appeal Status </span> <p> {{ appeal_status }} </p>',
    '<span> Appeal Decision Date </span> <p> {{ appeal_decision_date }} </p>',
    """<span> Applicant </span> <p> {{ applicant_name }} </p>
    <span> Applicant's Address </span> <p> {{ applicant_address }} </p>""",
    """<span> Agent </span> <p> {{ agent_name }} </p>
    <span> Agent's Address </span> <p> {{ agent_address }} </p>""",
    ]
    detail_tests = [
        { 'uid': 'S6/2012/1356/FP', 'len': 18 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 57 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 11 } ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        
        response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s", response.read())
        
        fields = {}
        fields.update(self._search_fields)
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        fields[self._date_from_field2] = date_from.strftime(self._request_date_format2)
        fields[self._date_to_field2] = date_to.strftime(self._request_date_format2)
        fields[self._date_from_field3] = date_from.strftime(self._request_date_format3)
        fields[self._date_to_field3] = date_to.strftime(self._request_date_format3)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._submit_control)
        
        html = response.read()
        #self.logger.debug("ID batch page html: %s", html)
        
        runaway_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        try:
            result = scrapemark.scrape(self._scrape_max_pages, html)
            max_pages = int(result['max_pages'])
        except:
            max_pages = runaway_pages
            
        page_count = 0
        while html and page_count < max_pages:
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
            if page_count >= max_pages: break
            try:
                scrapeutils.setup_form(self.br, self._search_form)
                self.logger.debug("ID next form: %s", str(self.br.form))
                response = scrapeutils.submit_form(self.br, self._submit_next)
                html = response.read()
            except: # failure to find next page link at end of page sequence here
                self.logger.debug("No next form after %d pages", page_count)
                break
                
        if page_count >= runaway_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
               
        return final_result
        
    def get_html_from_uid (self, uid):
        response = self.br.open(self._search_url)
        #self.logger.debug("ID detail start html: %s", response.read())
        fields = {}
        fields.update(self._search_fields)
        fields[self._ref_field] = uid
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("Get UID form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._ref_submit)
        html, url = self._get_html(response)
        result = scrapemark.scrape(self._scrape_ids, html, url)
        if result and result.get('records'):
            self._clean_ids(result['records'])
            for r in result['records']:
                if r.get('uid', '') == uid and r.get('url'):
                    self.logger.debug("Scraped url: %s", r['url'])
                    return self.get_html_from_url(r['url'])
        return None, None
        

