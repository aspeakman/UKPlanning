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
try:
    from ukplanning import scrapeutils
except ImportError:
    import scrapeutils
from .. import base
import urllib
from datetime import date
import mechanize
import re

class SedgemoorScraper(base.DateScraper):

    min_id_goal = 250 # min target for application ids to fetch in one go
    
    _authority_name = 'Sedgemoor'
    _period_type = 'Month'
    _uid_only = True # URLs are available, but they expire = time limited
    _search_form = '0'
    #_start_fields = {  'drpYearRange': '2', 'ImageButton1': None }
    _start_fields_date = { '__EVENTTARGET': '', '__EVENTARGUMENT': '' }
    _search_fields_date = { '__EVENTTARGET': '', '__EVENTARGUMENT': '', 
        'ctl00$MainContent$planSearch$ddlAppDateStatus': 'WkListDate' }
    _date_from_field = 'ctl00$MainContent$planSearch$txtDateFrom'
    _date_to_field = 'ctl00$MainContent$planSearch$txtDateTo'
    _start_submit = 'ctl00$MainContent$btnSubmit'
    _search_submit = 'ctl00$MainContent$planSearch$btnSearch'
    _search_fields_applic = { '__EVENTTARGET': '', '__EVENTARGUMENT': '',
        'ctl00$sideBar$sdcAppSearch$imgBtnAppSearch.x': '12', 'ctl00$sideBar$sdcAppSearch$imgBtnAppSearch.y': '12' }
    #_detail_fields = { 'TextBox1': '', '__EVENTTARGET': 'dgrList:_ctl3:_ctl0', '__EVENTARGUMENT': '', 'imbSubmit': None, 'ibSendME': None }
    #_next_fields = { 'TextBox1': '', '__EVENTTARGET': 'dgrList$_ctl1$_ctl1', '__EVENTARGUMENT': '', 'imbSubmit': None } 
    _detail_fields = { '__EVENTTARGET': 'ctl00$MainContent$planList$lvPlanList$ctrl0$lnkBtnView', '__EVENTARGUMENT': '' }
    _html_subs = { 
        r'name="ctl00\$MainContent\$btnSubmit" value=".*?Proceed"': 'name="ctl00$MainContent$btnSubmit" value=" Proceed"',
        r'name="ctl00\$sideBar\$sdcTelecomsSearch\$btnSubmit" value="Submit.*?"': 'name="ctl00$sideBar$sdcTelecomsSearch$btnSubmit" value="Submit "',
        r'name="ctl00\$MainContent\$planSearch\$btnFindAddress" value="Find Address.*?"': 'name="ctl00$MainContent$planSearch$btnFindAddress" value="Find Address "'
        # these substitutions fix the following error caused by stray \xc2\xa0 UTF-8 non-break space characters in the source
        # UnicodeEncodeError: 'ascii' codec can't encode character u'\xa0' in position 43: ordinal not in range(128)
        # also some other \xe9 UTF8 characters - so now we also have a catch all to remove any other non ASCI chars
        # see _adjust_response
    }
    _next_form = '0'
    _search_url = 'http://www.sedgemoor.gov.uk/planning%20online/'
    _scrape_max_pages = """
    <span id="lblPageCount"><b> of {{ max_pages }} </b></span>
    """
    _scrape_max_recs = """
    <span id="MainContent_planList_lblTotal"> Results Found: {{ max_recs }} </span>
    """
    _scrape_ids = """
    <section class="main-content">
        {* <div class="headerRow"> Application Number: {{ [records].uid }} </div>
        <div class="contentRow"> Registered Date: {{ [records].date_validated }} </div> *}
    </section>
    """
    _scrape_applic_types = """
    <select id="ddlAppType"> <option />
        {* <option value="{{ [options] }}" /> *}
    </select>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <div id="body">  {{ block|html }} </div>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <span id="MainContent_ctl00_lblAppNo"> {{ reference }} </span>
    <span id="MainContent_ctl00_lblRecDate"> {{ date_received }} </span>
    <span id="MainContent_ctl00_tabContainer_tabAppDetails_rptDetails_lblLoc_0"> {{ address }} </span>
    <span id="MainContent_ctl00_tabContainer_tabAppDetails_rptDetails_lblPro_0"> {{ description }} </span>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<span id="MainContent_ctl00_lblAppRegDate"> {{ date_validated }} </span>',
    '<span id="MainContent_ctl00_lblComDate"> {{ consultation_end_date }} </span>',
    '<span id="MainContent_ctl00_lblConsideration"> {{ status }} </span>',
    '<span id="MainContent_ctl00_lblParish"> {{ parish }} </span>',
    '<span id="MainContent_ctl00_tabContainer_tabAppDetails_rptDetails_lblType_0"> {{ application_type }} </span>',
    '<div class="tabRow"> Applicant: {{ applicant_name }} </div>',
    '<span id="MainContent_ctl00_tabContainer_tabAppDetails_rptDetails_lblCaseOff_0"> {{ case_officer }} </span>',
    '<div class="tabRow"> Applicant Address: {{ applicant_address }} </div>',
    '<div class="tabRow"> Agent: {{ agent_name }} </div>',
    '<div class="tabRow"> Agent Address: {{ agent_address }} </div>',
    '<span id="MainContent_ctl00_tabContainer_tabAppDetails_rptDetails_lblConStartDate_0"> {{ consultation_start_date }} </span>', 
    '<span id="MainContent_ctl00_tabContainer_tabAppDetails_rptDetails_lblEarDecDate_0"> {{ target_decision_date }} </span>', 
    '<span id="MainContent_ctl00_tabContainer_tabAppDetails_rptDetails_lblComDel_0"> {{ decided_by }} </span>', 
    '<span id="MainContent_ctl00_tabContainer_tabAppDetails_rptDetails_lblComDate1_0"> {{ meeting_date }} </span>', 
    '<span id="MainContent_ctl00_tabContainer_tabAppDetails_rptDetails_lblDec_0"> {{ decision }} </span>',
    #'<span id="MainContent_ctl00_lblDecDate"> {{ decision_date }} </span>',
    '<span id="MainContent_ctl00_tabContainer_tabAppDetails_rptDetails_lblDecDate1_0"> {{ decision_date }} </span>',
    '<span id="MainContent_ctl00_lblAppealRecDate"> {{ appeal_date }} </span>',
    #'<span id="MainContent_ctl00_tabContainer_tabAppDetails_rptDetails_lblAppeal_0"> {{ appeal_result }} </span>',
    '<span id="MainContent_ctl00_lblAppealDecDate"> {{ appeal_decision_date }} </span>', 
    ]
    detail_tests = [
        { 'uid': '08/11/00250', 'len': 19 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 25 },
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 10 } ]
        
    def __init__(self, *args, **kwargs):
        super(SedgemoorScraper, self).__init__(*args, **kwargs)
        # Follows refresh 0 but not hangs on refresh > 0
        self.br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

    def get_id_batch (self, date_from, date_to):

        final_result = []
        
        response = self.br.open(self._search_url)
        self._adjust_response(response)
        #self.logger.debug("Start page html: %s", response.read())
        
        # start page
        fields = {}
        fields.update(self._start_fields_date)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID start form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._start_submit)
        self._adjust_response(response)
        #self.logger.debug("Search page html: %s", response.read())
        
        # search page
        fields = {}
        fields.update(self._search_fields_date)
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._search_submit)
        self._adjust_response(response)
        
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
                fields = { '__EVENTARGUMENT': '' }
                fields['__EVENTTARGET'] = 'ctl00$MainContent$planList$dpBottom$ctl00$ctl%s' % (str(page_count).zfill(2))
                scrapeutils.setup_form(self.br, self._next_form, fields)
                for control in self.br.form.controls:
                    if control.type == "submit" or control.type == "image":
                        control.disabled = True
                response = scrapeutils.submit_form(self.br)
                self._adjust_response(response)
                html = response.read()
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next form after %d pages", page_count)
                break
        
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
            
        adjusted_result = []
        for res in final_result: # get rid of entries with dates outside the requested range
            if res['date_validated'] <= date_to.isoformat() and res['date_validated'] >= date_from.isoformat():
                adjusted_result.append(res)
        return adjusted_result
        
    def get_html_from_uid(self, uid):
        
        response = self.br.open(self._search_url)
        self._adjust_response(response)
        #self.logger.debug("Start page html: %s", response.read())
        
        # get first brief application page
        fields = {}
        fields.update(self._search_fields_applic)
        fields ['ctl00$sideBar$sdcAppSearch$ddlCaseType'] = uid[0:2]
        fields ['ctl00$sideBar$sdcAppSearch$ddlCaseYear'] = uid[3:5]
        fields ['ctl00$sideBar$sdcAppSearch$txtCaseNo'] = uid[6:11]
        scrapeutils.setup_form(self.br, self._search_form, fields)
        for control in self.br.form.controls:
            if control.type == "submit" or control.type == "image":
                control.disabled = True
        self.logger.debug("First applic form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        self._adjust_response(response)
        #self.logger.debug("First page: %s", response.read())

        # get second detailed application page
        scrapeutils.setup_form(self.br, self._search_form, self._detail_fields)
        for control in self.br.form.controls:
            if control.type == "submit" or control.type == "image":
                control.disabled = True
        self.logger.debug("Detail applic form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        self._adjust_response(response)
        html, url = self._get_html(response)
        #self.logger.debug("Detail page: %s", html)
        return html, url
        
    def _adjust_response(self, response): 
        """ fixes bad html that breaks form processing """
        if self._html_subs:
            html = response.get_data()
            for k, v in self._html_subs.items():
                html = re.sub(k, v, html, 0, re.U|re.S|re.I) # unicode|dot matches new line|ignore case
            html = ''.join([i if ord(i) < 128 else ' ' for i in html]) #catch all remove any other non ASCII
            response.set_data(html)
            self.br.set_response(response)
        



