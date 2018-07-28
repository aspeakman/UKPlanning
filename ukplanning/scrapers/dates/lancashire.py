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

# also see Nottinghamshire, NorthumberlandPark, Devon and CCED = Christchurch and East Dorset

class LancashireScraper(base.DateScraper):

    data_start_target = '2000-06-01'
    batch_size = 28 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 28 # start this number of days ago when gathering current ids
    min_id_goal = 200 # min target for application ids to fetch in one go
    
    _authority_name = 'Lancashire'
    _search_url = 'http://planningregister.lancashire.gov.uk/planappsearch.aspx'
    _date_from_field = 'ctl00_ContentPlaceHolder1_txtAppValFrom_dateInput_ClientState'
    _date_to_field = 'ctl00_ContentPlaceHolder1_txtAppValTo_dateInput_ClientState'
    _date_from_field2 = 'ctl00$ContentPlaceHolder1$txtAppValFrom'
    _date_to_field2 = 'ctl00$ContentPlaceHolder1$txtAppValTo'
    _date_from_field3 = 'ctl00$ContentPlaceHolder1$txtAppValFrom$dateInput'
    _date_to_field3 = 'ctl00$ContentPlaceHolder1$txtAppValTo$dateInput'
    _start_fields = { '__EVENTARGUMENT': '', '__EVENTTARGET': '', 'ctl00$ContentPlaceHolder1$Button2': None }
    _next_base_fields = { '__EVENTARGUMENT': '', '__EVENTTARGET': 'ctl00$ContentPlaceHolder1$ddlPager', 
            'ctl00$ContentPlaceHolder1$btnNewSearch': None, 'ctl00$ContentPlaceHolder1$Button1': None }
    _next_field = 'ctl00$ContentPlaceHolder1$ddlPager'
    _ref_field = 'ctl00$ContentPlaceHolder1$txtAppNum'
    _request_date_format = '{"enabled":true,"emptyMessage":"","validationText":"%Y-%m-%d-00-00-00","valueAsString":"%Y-%m-%d-00-00-00","minDateStr":"1900-01-01-00-00-00","maxDateStr":"2099-12-31-00-00-00","lastSetTextBoxValue":"%d/%m/%Y"}'
    _search_form = 'aspnetForm'
    _scrape_max_recs = '<p> Your search has returned {{ max_recs }} applications. </p>'
    _scrape_ids = """
    <table id="ctl00_ContentPlaceHolder1_grdResults_ctl00">
    {* <table>
    Application Number: <a href="{{ [records].url|abs }}">
    {{ [records].uid }} </a>
    </table> *}
    </table>
    """
    _scrape_data_block = """
    <div id="ctl00_ContentPlaceHolder1_RadMultiPage1"> {{ block|html }} </div>
    """
    _scrape_min_data = """
    <input name="txtAppNum" value="{{ reference }}" />
    <textarea name="Location"> {{ address }} </textarea>
    <textarea name="Proposal"> {{ description }} </textarea>
    <input name="RecvDate" value="{{ date_received }}" />
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<input name="SiteNot" value="{{ date_validated }}" />',
    '<input name="txtAppStatus" value="{{ status }}" />',
    '<input name="ctl00$ContentPlaceHolder1$RadLVProperty$ctrl0$txtDistrict" value="{{ district }}" />',
    '<input name="ctl00$ContentPlaceHolder1$RadLVProperty$ctrl0$txtParish" value="{{ parish }}" />',
    '<input name="ctl00$ContentPlaceHolder1$RadLVProperty$ctrl0$txtWard" value="{{ ward_name }}" />',
    '<input name="Easting" value="{{ easting }}" />',
    '<input name="Northing" value="{{ northing }}" />',
    '<input name="AppName" value="{{ applicant_name }}" />',
    '<input name="agentName" value="{{ agent_name }}" />',
    '<textarea name="ctl00$ContentPlaceHolder1$RadLVApplicants$ctrl0$txtAppAddress"> {{ applicant_address }} </textarea>',
    '<textarea name="ctl00$ContentPlaceHolder1$RadLVApplicants$ctrl0$txtAgentAddress"> {{ agent_address }} </textarea>',
    '<input name="delegComm" value="{{ decided_by }}" />',
    '<input name="commDate" value="{{ meeting_date }}" />',
    '<input name="decDate" value="{{ decision_issued_date }}" />',
    '<input name="dec" value="{{ decision }}" />',
    '<input name="aplDate" value="{{ appeal_date }}" />',
    '<input name="aplDec" value="{{ appeal_result }}" />',
    '<input name="planOff" value="{{ case_officer }}" />',
    ]
    detail_tests = [
        { 'uid': '06/11/0713', 'len': 19 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '03/09/2012', 'to': '29/09/2012', 'len': 29 }, 
        { 'from': '15/08/2012', 'to': '15/08/2012', 'len': 1 } ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s", response.read())

        fields = {}
        fields.update(self._start_fields)
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        fields[self._date_from_field2] = date_from.isoformat()
        fields[self._date_to_field2] = date_to.isoformat()
        fields[self._date_from_field3] = date_from.strftime('%d/%m/%Y')
        fields[self._date_to_field3] = date_to.strftime('%d/%m/%Y')
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        
        html = response.read()
        #self.logger.debug("ID batch page html: %s", html)
        try:
            result = scrapemark.scrape(self._scrape_max_recs, html)
            if result:
                max_recs = int(result['max_recs'])
            else:
                # if there is only one result - no records total is displayed
                result = scrapemark.scrape(self._scrape_ids, html)
                if result:
                    max_recs = 1
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
                fields = { }
                fields.update(self._next_base_fields)
                fields [self._next_field] = str(page_count) # note value in this field is 0 to get page 1, 1 for page 2 etc
                scrapeutils.setup_form(self.br, self._search_form, fields)
                self.logger.debug("ID next form: %s", str(self.br.form))
                response = scrapeutils.submit_form(self.br)
                html = response.read()
            except: # failure to find next page link at end of page sequence here
                self.logger.debug("No next form link after %d pages", page_count)
                break
                
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
               
        return final_result
        
    def get_html_from_uid (self, uid):
        response = self.br.open(self._search_url)
        #self.logger.debug("ID detail start html: %s", response.read())
        fields = {  self._ref_field: uid }
        scrapeutils.setup_form(self.br, self._search_form, fields)
        response = scrapeutils.submit_form(self.br)
        html, url = self._get_html(response)
        result = scrapemark.scrape(self._scrape_ids, html, url)
        if result and result.get('records'):
            self._clean_ids(result['records'])
            for r in result['records']:
                if r.get('uid', '') == uid and r.get('url'):
                    self.logger.debug("Scraped url: %s", r['url'])
                    return self.get_html_from_url(r['url'])
        return None, None
            

