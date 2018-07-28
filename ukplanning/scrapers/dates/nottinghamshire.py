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

# also see Lancashire, Northumberland Park, Devon and CCED = Christchurch and East Dorset

class NottinghamshireScraper(base.DateScraper):

    batch_size = 28 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 28 # start this number of days ago when gathering current ids
    min_id_goal = 200 # min target for application ids to fetch in one go
    
    _authority_name = 'Nottinghamshire'
    _date_from_field = 'ctl00_MainContent_txtDateReceivedFrom_dateInput_ClientState'
    _date_to_field = 'ctl00_MainContent_txtDateReceivedTo_dateInput_ClientState'
    _request_date_format = '{"enabled":true,"emptyMessage":"","validationText":"%Y-%m-%d-00-00-00","valueAsString":"%Y-%m-%d-00-00-00","minDateStr":"01/01/1900","maxDateStr":"12/31/2099"}'
    #date_from_field2 = 'ctl00$MainContent$txtDateReceivedFrom'
    #date_to_field2 = 'ctl00$MainContent$txtDateReceivedTo'
    #request_date_format2 = '%Y-%m-%d'
    _search_fields = { '__EVENTTARGET': '', '__EVENTARGUMENT': '' } 
    _search_form = '1'
    _start_fields = { 'ctl00$MainContent$radSearchType': 'ADV' }
    _submit_continue = "ctl00$MainContent$btnContinue"
    _submit_control = 'ctl00$MainContent$btnSearch'
    _submit_next = 'ctl00$MainContent$lvResults$pager$ctl02$NextButton'
    
    _search_url = 'http://www.nottinghamshire.gov.uk/planningsearch/planhome.aspx'
    _applic_url = 'http://www.nottinghamshire.gov.uk/planningsearch/plandisp.aspx'
    
    _scrape_max_recs = '<div> Your search returned the following results (a total of {{ max_recs }}). </div>'
    _scrape_ids = """
    <div id="news_results_list">
        {* <div> <div class="SearchResultRow">
        <div> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </div> <div> {{ [records].reference }} </div> 
        </div> </div> *}
    </div>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <form id="form1"> {{ block|html }} </form>
    """
    _min_fields = [ 'address', 'description', 'date_received' ] # min fields list used in testing only
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <textarea name="ctl00$MainContent$txtLocation"> {{ address }} </textarea>
    <textarea name="ctl00$MainContent$txtProposal"> {{ description }} </textarea>
    <input value="{{ date_received }}" name="ctl00$MainContent$txtReceivedDate" />
    <input value="{{ date_validated }}" name="ctl00$MainContent$txtValidDate" />
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<select name="ctl00$MainContent$listDistricts"> {{ district }} </select>',
    '<select name="ctl00$MainContent$listParishes"> {{ parish }} </select>', 
    '<textarea name="ctl00$MainContent$txtAppName"> {{ applicant_name }} </textarea>',
    '<textarea name="ctl00$MainContent$txtAgentsName"> {{ agent_name }} </textarea>',
    '<input value="{{ case_officer }}" name="ctl00$MainContent$txtCaseOfficer" />', 
    '<input value="{{ decision }}" name="ctl00$MainContent$txtDecision" />',
    '<input value="{{ decision_date }}" name="ctl00$MainContent$txtDecisionDate2" />',
    '<tr> <td> Site Notice </td> <td /> <td> {{ site_notice_start_date }} </td> <td> {{ site_notice_end_date }} </td> </tr>',
    '<tr> <td> Press Advert </td> <td /> <td> {{ consultation_start_date }} </td> <td> {{ consultation_end_date }} </td> </tr>',
    ]
    detail_tests = [
        { 'uid': 'T/2297', 'len': 14 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '03/09/2012', 'to': '23/10/2012', 'len': 17 }, 
        { 'from': '09/08/2012', 'to': '09/08/2012', 'len': 1 } ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        
        response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s", response.read())
        
        scrapeutils.setup_form(self.br, self._search_form, self._start_fields)
        self.logger.debug("Start form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._submit_continue)

        fields = {}
        fields.update(self._search_fields)
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
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
                self.logger.debug("No next form link after %d pages", page_count)
                break
                
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
               
        return final_result
        
    def get_html_from_uid (self, uid):
        url = self._applic_url + '?AppNo=' + urllib.quote_plus(uid)
        return self.get_html_from_url(url)
        

