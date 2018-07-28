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

# also see CCED = Christchurch and East Dorset
# and WelwynHatfield, Devon, Nottinghamshire, Lancashire, NorthumberlandPark

class TelerikScraper(base.DateScraper):
    
    _scraper_type = 'Telerik'    
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
    _submit_control = 'ctl00$ContentPlaceHolder1$btnSearch'
    _ref_field = 'ctl00$ContentPlaceHolder1$txtAppNumber'
    _submit_next = 'ctl00$ContentPlaceHolder1$lvResults$pager$ctl02$NextButton'
     
    _scrape_max_pages = '<div class="rdpWrap"> of {{ max_pages }} </div>'
    _scrape_ids = """
    <div id="news_results_list"> <tbody>
        {* <tr> <td>
        <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a>  
        </td> </tr> *}
    </tbody> </div>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <form id="aspnetForm"> {{ block|html }} </form>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <tr> <td> Application Number </td> <td> {{ reference }} </td> </tr>
    <tr> <td> Location Address </td> <td> {{ address }} </td> </tr>
    <tr> <td> Proposal </td> <td> {{ description }} </td> </tr>
    <tr> <td> Received Date </td> <td> {{ date_received }} </td> </tr>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<tr> <td> Valid Date </td> <td> {{ date_validated }} </td> </tr>',
    '<tr> <td> Status </td> <td> {{ status }} </td> </tr>',
    '<tr> <td> Case Officer </td> <td> {{ case_officer }} </td> </tr>',
    '<tr> <td> Application Type </td> <td> {{ application_type }} </td> </tr>',
    '<tr> <td> Committee Date </td> <td> {{ meeting_date }} </td> </tr>',
    '<tr> <td> Decision Level </td> <td> {{ decided_by }} </td> </tr>',
    '<tr> <td> Decision Date </td> <td> {{ decision_date }} </td> </tr>',
    '<tr> <td> Ward </td> <td> {{ ward_name }} </td> </tr>',
    '<tr> <td> Parish </td> <td> {{ parish }} </td> </tr>',
    '<tr> <td> Appeal Decision </td> <td> {{ appeal_result }} </td> </tr>',
    '<tr> <td> Consultation Start </td> <td> {{ consultation_start_date }} </td> </tr>',
    '<tr> <td> Consultation End </td> <td> {{ consultation_end_date }} </td> </tr>',
    '<tr> <td> Advert Expiry </td> <td> {{ latest_advertisement_expiry_date }} </td> </tr>', 
    '<tr> <td> Site Notice Date </td> <td> {{ site_notice_start_date }} </td> </tr>', 
    '<tr> <td> Applicant Name </td> <td> {{ applicant_name }} </td> </tr>',
    '<tr> <td> Applicant Address </td> <td> {{ applicant_address }} </td> </tr>',
    '<tr> <td> Agent Name</td> <td> {{ agent_name }} </td> </tr>',
    '<tr> <td> Agent Address </td> <td> {{ agent_address }} </td> </tr>',
    '<tr> <td> UPRN </td> <td> {{ uprn }} </td> </tr>', 
    '<tr> <td> Easting </td> <td> {{ easting }} </td> </tr>',
    '<tr> <td> Northing </td> <td> {{ northing }} </td> </tr>',
    ]

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
        response = self.br.open(self._applic_url)
        #self.logger.debug("ID detail start html: %s", response.read())
        fields = {}
        fields.update(self._search_fields)
        fields[self._ref_field] = uid
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("Get UID form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._submit_control)
        html, url = self._get_html(response)
        #self.logger.debug("ID detail page html: %s", html)
        result = scrapemark.scrape(self._scrape_ids, html, url)
        #print result
        if result and result.get('records'):
            self._clean_ids(result['records'])
            if len(result['records']) == 1:
                r = result['records'][0]
                if uid in r.get('uid', '') and r.get('url'):
                    self.logger.debug("Scraped url: %s", r['url'])
                    return self.get_html_from_url(r['url'])
        return None, None

class MalvernHillsScraper(TelerikScraper):
    
    _authority_name = 'MalvernHills'
    _comment = 'was EAccessScraper'
    _search_url = 'https://plan.malvernhills.gov.uk/advsearch.aspx'
    _applic_url = 'https://plan.malvernhills.gov.uk/'
    
    detail_tests = [
        { 'uid': '12/01042/HOU', 'len': 20 }, ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 35 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 8 } ]

class WychavonScraper(TelerikScraper):
    
    _authority_name = 'Wychavon'
    _comment = 'was month based PeriodScraper'
    _search_url = 'https://plan.wychavon.gov.uk/advsearch.aspx'
    _applic_url = 'https://plan.wychavon.gov.uk/'
    
    detail_tests = [
        { 'uid': '12/00570', 'len': 19 },
        { 'uid': 'W/12/00570/PP', 'len': 19 }, ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 32 }, 
        { 'from': '09/08/2012', 'to': '09/08/2012', 'len': 2 } ]
 

