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
import urllib
import json

class AmberValleyScraper(base.DateScraper):

    min_id_goal = 250 # min target for application ids to fetch in one go

    _authority_name = 'AmberValley'
    _handler = 'etree'
    _uid_only = True # there is direct URL access for application detail, but it is JSON and not a public Web page
    _search_url = 'http://www.ambervalley.gov.uk/environment-and-planning/planning/development-management/planning-applications/view-a-planning-application.aspx'
    _applic_url= 'http://www.ambervalley.gov.uk/ajaxfeeds/PlanAppJSON.aspx?action=getappdetails&refval='
    _headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 5.1; rv:8.0) Gecko/20100101 Firefox/8.0',
    'Accept-Charset': 'UTF-8,*',
    'Accept': 'text/html',
    'Accept-Language': 'en-gb,en',
    }
    _response_date_format = '%d-%b-%y'
    _date_from_field = {
        'day': 'ctl00$ctl00$ctl00$ContentPlaceHolderDefault$MasterTemplateBodyMainPlaceHolder$ctl01$PlanApps_9$lstDayStartCus',
        'month': 'ctl00$ctl00$ctl00$ContentPlaceHolderDefault$MasterTemplateBodyMainPlaceHolder$ctl01$PlanApps_9$lstMonthStartCus',
        'year': 'ctl00$ctl00$ctl00$ContentPlaceHolderDefault$MasterTemplateBodyMainPlaceHolder$ctl01$PlanApps_9$lstYearStartCus',
        }
    _date_to_field = {
        'day': 'ctl00$ctl00$ctl00$ContentPlaceHolderDefault$MasterTemplateBodyMainPlaceHolder$ctl01$PlanApps_9$lstDayEndCus',
        'month': 'ctl00$ctl00$ctl00$ContentPlaceHolderDefault$MasterTemplateBodyMainPlaceHolder$ctl01$PlanApps_9$lstMonthEndCus',
        'year': 'ctl00$ctl00$ctl00$ContentPlaceHolderDefault$MasterTemplateBodyMainPlaceHolder$ctl01$PlanApps_9$lstYearEndCus',
        }
    _search_fields = {
        'ctl00$ctl00$ctl00$ContentPlaceHolderDefault$MasterTemplateBodyMainPlaceHolder$ctl01$PlanApps_9$chkIncludeTPOCus': 'on', # include tree applications
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        }
    #_ref_field = 'ctl00$ctl00$ctl00$ContentPlaceHolderDefault$MasterTemplateBodyMainPlaceHolder$ctl01$PlanApps_9$txbAppRef'
    _search_form = '0'
    _search_submit = 'ctl00$ctl00$ctl00$ContentPlaceHolderDefault$MasterTemplateBodyMainPlaceHolder$ctl01$PlanApps_9$btnViewCustom'
    #_ref_submit = 'ctl00$ctl00$ctl00$ContentPlaceHolderDefault$MasterTemplateBodyMainPlaceHolder$ctl01$PlanApps_9$btnViewByAppRef'
    _scrape_ids = """
    <div id="planAppList"> <table> <tr />
    {* <tr> <td>
    <a> {{ [records].uid }} </a>  Val: {{ [records].date_received }} Dec: {{ [records].decision_date }} </td> </tr> *}
    </table> </div>
    """
    """_scrape_data_block = ""
    <div id="dialogPlanAppDetails"> {{ block|html }} </div>
    ""
    _scrape_min_data = ""
    <div class="detailName"> Application Reference </div> <div class="detailContent"> {{ reference }} </div>
    <div class="detailName"> Address </div> <div class="detailContent"> {{ address }} </div>
    <div class="detailName"> Proposal </div> <div class="detailContent"> {{ description }} </div>
    <div class="detailName"> Registered </div> <div class="detailContent"> {{ date_validated }} </div>
    ""
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<div class="detailName"> Case Officer </div> <div class="detailContent"> {{ case_officer }} </div>',
    '<div class="detailName"> Status </div> <div class="detailContent"> {{ status }} </div>',
    '<div class="detailName"> Applicant </div> <div class="detailContent"> {{ applicant_name }} <br> {{ applicant_address }} </div>',
    '<div class="detailName"> Agent </div> <div class="detailContent"> {{ agent_name }} <br> {{ agent_address }} </div>',
    '<a href="{{ comment_url|abs }}"> Comment on this Application </a>',
    'href="https://maps.google.com/maps?ll={{latitude}},{{longitude}}&z=16&t=m&hl=en-US&gl=US&mapclient=apiv3"'
    ]"""
    _scrape_data_block = 'item'
    _scrape_min_data = {
        'refVal': 'reference',
        'applicationAddress': 'address',
        'proposal': 'description',
        'dateRegistered': 'date_validated' }
    _scrape_optional_data = {
        'officerName': 'case_officer',
        'status': 'status',
        'applicantName': 'applicant_name',
        'applicantAddress': 'applicant_address',
        'agentName': 'agent_name',
        'agentAddress': 'agent_address',
        'eastings': 'easting',
        'northings': 'northing' }
    detail_tests = [
        { 'uid': 'AVA/2011/0742', 'len': 10 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 63 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 2 } ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s", response.read())
        
        fields = {}
        fields.update(self._search_fields)
        dfrom = date_from.strftime('X%d/%b/%Y').replace('X0','X').replace('X','')
        date_parts = dfrom.split('/')
        fields[self._date_from_field['day']] = [ date_parts[0] ]
        fields[self._date_from_field['month']] = [ date_parts[1] ]
        fields[self._date_from_field['year']] = [ date_parts[2] ]
        dto = date_to.strftime('X%d/%b/%Y').replace('X0','X').replace('X','')
        date_parts = dto.split('/')
        fields[self._date_to_field['day']] = [ date_parts[0] ]
        fields[self._date_to_field['month']] = [ date_parts[1] ]
        fields[self._date_to_field['year']] = [ date_parts[2] ]
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._search_submit)
        
        if response:
            html = response.read()
            url = response.geturl()
            #self.logger.debug("Batch html: %s" % html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            
        return final_result
        
    def get_html_from_uid(self, uid): # in this case it is JSON not HTML
        url = self._applic_url + urllib.quote_plus(uid)
        response = self.br.open(url) # use mechanize, to get same handler interface as elsewhere
        return self._get_html(response)

    """def get_html_from_uid(self, uid):
        " Get the html response for one record given its uid "
        response = self.br.open(self._search_url)
        #self.logger.debug("ID detail start html: %s", response.read())
        fields = { self._ref_field: uid }
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID detail form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._ref_submit)
        return self._get_html(response)"""
        
    def _get_details(self, html, this_url):
        """ Scrapes detailed information for one record given html and url 
        - this is an optional hook to allow data from multiple linked pages to be merged """
        return self._get_detail_json(html, this_url)
        
    def _get_detail_json(self, json_string, url, data_block = None, min_data = None, optional_data = {}, invalid_format = None):
        """ Scrapes detailed information for one record given its JSON and URL and scraper config dicts
        returns a cleaned dict with application information if finds correctly configured data
        otherwise a dict with a 'scrape_error' key if there is a problem
        """
        scrape_data_block = data_block or self._scrape_data_block # use class defaults if none supplied
        scrape_min_data = min_data or self._scrape_min_data
        scrape_optional_data = optional_data or self._scrape_optional_data
        scrape_invalid_format = invalid_format or self._scrape_invalid_format
        result = json.loads(json_string)
        #self.logger.debug("JSON: %s %s" % (json_string, str(result)))
        data_out = None
        if result and scrape_data_block and result.get(scrape_data_block):
            data_out = result[scrape_data_block]
        elif result and not scrape_data_block:
            data_out = result
        if data_out and scrape_min_data:
            if set(scrape_min_data.keys()) <= set(data_out.keys()):
                result = {}
                for k, v in scrape_min_data.items():
                    result[v] = data_out[k]
                self.logger.debug("Scraped %d min data items", len(result))
                opt_count = 0
                for k, v in scrape_optional_data.items():
                    next_val = data_out[k]
                    if next_val:
                        result[v] = next_val
                        opt_count += 1
                if opt_count:
                    self.logger.debug("Scraped %d optional data items", opt_count)
                elif scrape_optional_data:
                    self.logger.warning("Scraped no optional data items")
                self._clean_record(result)
                return result
            elif scrape_invalid_format:
                if set(scrape_invalid_format) <= set(data_out.keys()): # just tests if the element is in the set of keys
                    self.logger.warning("Error when getting detail from %s: %s" % (url, self.errors[self.INVALID_FORMAT]))
                    return { 'scrape_error': self.errors[self.INVALID_FORMAT] } 
            self.logger.warning("Error when getting detail from %s: %s" % (url, self.errors[self.NO_DETAIL]))
            return { 'scrape_error': self.errors[self.NO_DETAIL] }     
        else:
            self.logger.warning("Error when getting detail from %s: %s" % (url, self.errors[self.NO_DATA]))
            return { 'scrape_error': self.errors[self.NO_DATA] }
        


