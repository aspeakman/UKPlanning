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

# also see Wychavon, WelwynHatfield, Nottinghamshire, Lancashire, NorthumberlandPark and CCED = Christchurch and East Dorset

class DevonScraper(base.DateScraper):

    batch_size = 50 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 50 # start this number of days ago when gathering current ids
    min_id_goal = 200 # min target for application ids to fetch in one go
    
    _authority_name = 'Devon'
    _date_from_field3 = 'ctl00_ContentPlaceHolder1_txtDateReceivedFrom_dateInput_ClientState'
    _date_to_field3 = 'ctl00_ContentPlaceHolder1_txtDateReceivedTo_dateInput_ClientState'
    _request_date_format3 = '{"enabled":true,"emptyMessage":"","validationText":"%Y-%m-%d-00-00-00","valueAsString":"%Y-%m-%d-00-00-00","minDateStr":"1980-01-01-00-00-00","maxDateStr":"2099-12-31-00-00-00","lastSetTextBoxValue":"%d/%m/%Y"}'
    _date_from_field2 = 'ctl00$ContentPlaceHolder1$txtDateReceivedFrom'
    _date_to_field2 = 'ctl00$ContentPlaceHolder1$txtDateReceivedTo'
    _request_date_format2 = '%Y-%m-%d'
    _date_from_field = 'ctl00$ContentPlaceHolder1$txtDateReceivedFrom$dateInput'
    _date_to_field = 'ctl00$ContentPlaceHolder1$txtDateReceivedTo$dateInput'
    #_request_date_format = '%Y-%m-%d'
    _search_fields = { '__EVENTTARGET': '', '__EVENTARGUMENT': '', 'ctl00$ContentPlaceHolder1$chklstSearchType$0': '1' } 
    _search_form = '#form2'
    #_start_fields = { 'ctl00$MainContent$radSearchType': 'ADV' }
    _submit_continue = "ctl00$MainContent$btnContinue"
    _submit_control = 'ctl00$ContentPlaceHolder1$btnSearch'
    _submit_next = 'ctl00$ContentPlaceHolder1$lvResults$RadDataPager1$ctl02$NextButton'
    
    _search_url = 'https://planning.devon.gov.uk/AdvSearch.aspx'
    _disclaimer_url = 'https://planning.devon.gov.uk/Disclaimer.aspx'
    _detail_page = 'PlanDisp.aspx'
    
    _scrape_max_recs = '<div class="rdpWrap"> Page 1 of {{dummy}} Total Records: {{ max_recs }} </div>'
    _scrape_ids = """
    <div id="news_results_list">
        {* <div>
        <h4> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </h4> 
        </div> *}
    </div>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <form id="form2"> {{ block|html }} </form>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <input name="ctl00$ContentPlaceHolder1$txtAppNo" value="{{ reference }}" />
    <input name="ctl00$ContentPlaceHolder1$txtValidDate" value="{{ date_validated }}" />
    <textarea name="ctl00$ContentPlaceHolder1$txtProposal"> {{ description }} </textarea>
    <textarea name="ctl00$ContentPlaceHolder1$txtAddress"> {{ address }} </textarea>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<input name="ctl00$ContentPlaceHolder1$txtReceivedDate" value="{{ date_received }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtType" value="{{ application_type }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtStatus" value="{{ status }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtCaseOfficer" value="{{ case_officer }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtConsultExpiry" value="{{ consultation_end_date }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtCommitteeDelegated" value="{{ decided_by }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtDecisionDate" value="{{ decision_date }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtCommitteeDelegatedDate" value="{{ meeting_date }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtDecision" value="{{ decision }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtIssueDate" value="{{ decision_issued_date }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtAppName" value="{{ applicant_name }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtAgtName" value="{{ agent_name }}" />',
    '<textarea name="ctl00$ContentPlaceHolder1$txtApplicantsAddress"> {{ applicant_address }} </textarea>',
    '<textarea name="ctl00$ContentPlaceHolder1$txtAgentsAddress"> {{ agent_address }} </textarea>',
    '<textarea name="ctl00$ContentPlaceHolder1$txtDistricts"> {{ district }} </textarea>',
    '<textarea name="ctl00$ContentPlaceHolder1$listElectoralDivisions"> {{ ward_name }} </textarea>',
    '<textarea name="ctl00$ContentPlaceHolder1$listParishes"> {{ parish }} </textarea>',
    '<a id="ContentPlaceHolder1_MappingLink" href="https://www.yoururlhere.gov.uk/{{easting}},{{northing}}"> Link to Devon Mapping System </a>'
    ]
    detail_tests = [
        { 'uid': 'DCC/3291/2011', 'len': 24 },
        { 'uid': 'DCC/1096/2002', 'len': 14 }, ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '03/09/2012', 'to': '23/10/2012', 'len': 16 }, 
        { 'from': '09/08/2012', 'to': '09/08/2012', 'len': 1 } ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        
        #Accept disclaimer
        response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s", response.read())
        
        this_url = response.geturl()
        if this_url.startswith(self._disclaimer_url):
            # accept disclaimer
            scrapeutils.setup_form(self.br, self._search_form) 
            self.logger.debug("Disclaimer form: %s", str(self.br.form))
            response = scrapeutils.submit_form(self.br)
        
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
        try:
            result = scrapemark.scrape(self._scrape_max_recs, html)
            if result:
                max_recs = int(result['max_recs'])
            else:
                max_recs = 0
        except:
            max_recs = 0
        
        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        while response and len(final_result) < max_recs and page_count < max_pages:
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
            if len(final_result) >= max_recs: break
            try:
                scrapeutils.setup_form(self.br, self._search_form)
                self.logger.debug("ID next form: %s", str(self.br.form))
                response = scrapeutils.submit_form(self.br, self._submit_next)
                html = response.read()
            except: # failure to find next page link at end of page sequence here
                self.logger.debug("No next form after %d pages", page_count)
                break
                
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
               
        return final_result
        
    def get_html_from_uid (self, uid):
        url = urlparse.urljoin(self._search_url, self._detail_page) + '?AppNo=' + urllib.quote_plus(uid)
        return self.get_html_from_url(url)
        
    def get_html_from_url (self, url):
        """ Get the html and url for one record given a URL """
        if self._uid_only:
            return None, None
        if self._search_url and self._detail_page:
            url_parts = urlparse.urlsplit(url)
            url = urlparse.urljoin(self._search_url, self._detail_page)
            if url_parts.query:
                url = url + '?' + url_parts.query
        response = self.br.open(url)
        this_url = response.geturl()
        if this_url.startswith(self._disclaimer_url):
            # accept disclaimer
            scrapeutils.setup_form(self.br, self._search_form) 
            self.logger.debug("Disclaimer form: %s", str(self.br.form))
            response = scrapeutils.submit_form(self.br)
        return self._get_html(response)
        

