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
from datetime import timedelta
import re

class FlintshireScraper(base.DateScraper):
    
    min_id_goal = 300 # min target for application ids to fetch in one go
    data_start_target = '2004-01-05'

    _authority_name = 'Flintshire'
    _search_url = 'https://digital.flintshire.gov.uk/FCC_Planning/' 
    _applic_url = 'https://digital.flintshire.gov.uk/FCC_Planning/Home/Details?refno='
    _headers = {
    'User-Agent': 'Mozilla/5.0 (Windows; U; MSIE 7.0; Windows NT 6.0; en-US)',
    'Accept-Charset': 'UTF-8,*',
    'Accept': 'text/html',
    'Accept-Language': 'en-gb,en',
    }
    _date_from_field = 'StartDate'
    _date_to_field = 'EndDate'
    _search_form = '0'
    _search_fields = { 'lengthMenu': 'All' }
    _scrape_ids = """
    <table id="planning"> <tbody>
    {* <tr> <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td> </tr>  *}
    </tbody> </table>
    """
    _html_subs = { 
        r'<script\s.*?</script>': r'',
    }
    _scrape_max_recs = '<div id="planning_info"> of {{ max_recs }} entries </div>'

    _scrape_data_block = '<div id="Dets"> {{ block|html }} </div>'
    _scrape_min_data = """
    <dt> Reference </dt> <dd> {{ reference }} </dd>
    <dt> Description </dt> <dd> {{ description }} </dd>
    {* <dt> Location </dt> <dd> {{ [address] }} </dd> *}
    <dt> Date Valid </dt> <dd> {{ date_validated }} </dd>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<dt> Location Post Code </dt> <dd> {{ postcode }} </dd>',
    '<dt> Status </dt> <dd> {{ status }} </dd>',
    '<dt> Application Type </dt> <dd> {{ application_type }} </dd>',
    '<dt> Comment By </dt> <dd> {{ comment_date }} </dd>',
    '<dt> Town Council </dt> <dd> {{ parish }} </dd>',
    '<dt> Ward </dt> <dd> {{ ward_name }} </dd>',
    '<dt> Northing </dt> <dd> {{ northing }} </dd>',
    '<dt> Easting </dt> <dd> {{ easting }} </dd>',
    '<dt> Decision Level </dt> <dd> {{ decided_by }} </dd>',
    '<dt> Decision Type </dt> <dd> {{ decision }} </dd>',
    '<dt> Decision Target Date </dt> <dd> {{ target_decision_date }} </dd>',
    """<dt> Decision Target Date </dt> <dd> {{ target_decision_date }} </dd>
    <dt> Decision Date </dt> <dd> {{ decision_date }} </dd>""",
    """<dt> Applicant Name </dt> <dd> {{ applicant_name }} </dd>
    {* <dt> Applicant </dt> <dd> {{ [applicant_address] }} </dd> *}""",
    """<dt> Agent Name </dt> <dd> {{ agent_name }} </dd>
    {* <dt> Agent </dt> <dd> {{ [agent_address] }} </dd> *}""",
    '<dt> Case Officers Name </dt> <dd> {{ case_officer }} </dd>',
    '<dt> Committee Date </dt> <dd> {{ meeting_date }} </dd>',
    '<dt> Appeal Received </dt> <dd> {{ appeal_date }} </dd>',
    '<dt> Appeal Type </dt> <dd> {{ appeal_type }} </dd>',
    """<dt> Appeal Decision </dt> <dd> {{ appeal_result }} </dd>
    <dt> Appeal Decision Date </dt> <dd> {{ appeal_decision_date }} </dd>""",
    ]
    detail_tests = [
        { 'uid': '048879', 'len': 20 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 47 }, 
        { 'from': '17/08/2012', 'to': '17/08/2012', 'len': 3 } ]

    def get_id_batch (self, date_from, date_to): # note end date is exclusive

        final_result = []
        response = self.br.open(self._search_url)
        self._adjust_response(response)
        #self.logger.debug("ID batch start html: %s", response.read())
            
        new_date_to = date_to + timedelta(days=1) # end date is exclusive, increment end date by one day
        fields = { }
        fields.update(self._search_fields)
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = new_date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
             
        #try:
        #    result = scrapemark.scrape(self._scrape_max_recs, html)
        #    max_recs = int(result['max_recs'])
        #except:
        #    max_recs = 1
        
        #self.logger.debug("Max recs: %d", max_recs)
        page_count = 0
        #max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        #while response and len(final_result) < max_recs and page_count < max_pages:
        if response:
            html = response.read()
            url = response.geturl()
            #self.logger.debug("ID batch page html: %s", html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                #page_count += 1
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            #else:
            #    self.logger.debug("Empty result after %d pages", page_count)
            #    break
            #if len(final_result) >= max_recs: break
            #try:
            #    result = scrapemark.scrape(self._scrape_next_link, html, url)
            #    response = self.br.open(result['next_link'])
            #    html = response.read()
            #except:
            #    self.logger.debug("No next link after %d pages", page_count)
            #    break
                
        #if page_count >= max_pages:
        #    self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
                         
        return final_result
        
    def get_html_from_uid(self, uid):
        url = self._applic_url + urllib.quote_plus(uid)
        return self.get_html_from_url(url)
            
    def _adjust_response(self, response): 
        """ fixes bad html that breaks form processing """
        if self._html_subs:
            html = response.get_data()
            for k, v in self._html_subs.items():
                html = re.sub(k, v, html, 0, re.U|re.S|re.I) # unicode|dot matches new line|ignore case
            response.set_data(html)
            self.br.set_response(response)
        
"""class FlintshireOldScraper(base.DateScraper):

    min_id_goal = 300 # min target for application ids to fetch in one go
    data_start_target = '2004-01-05'
    batch_size = 20 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 20 # start this number of days ago when gathering current ids

    _authority_name = 'FlintshireOld'
    _search_url = 'http://www.flintshire.gov.uk/en/Resident/Council-Apps/Planning-Applications.aspx'
    _applic_url = 'http://www.flintshire.gov.uk/PlanningRegister.aspx?u='
    _headers = {
    'User-Agent': 'Mozilla/5.0 (Windows; U; MSIE 7.0; Windows NT 6.0; en-US)',
    'Accept-Charset': 'UTF-8,*',
    'Accept': 'text/html',
    'Accept-Language': 'en-gb,en',
    }
    _search_tpl = "[frmDteAppldate]~gte~%s AND [frmDteAppldate]~lte~%s"
    _scrape_ids = ""
    <div id="data">
    <table> <tr />
    {* <tr> <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td> </tr>  *}
    </table> </div>
    ""
    _scrape_max_recs = '<h3> Your search found: {{ max_recs }} planning applications <a /> </h3>'
    _scrape_data_block = '<table summary="Planning Application Details"> {{ block|html }} </table>'
    _scrape_min_data = ""
    <tr> <td> Reference </td> <td> {{ reference }} </td> </tr>
    <tr> <td> Description </td> <td> {{ description }} </td> </tr>
    {* <tr> <td> Location Address </td> <td> {{ [address] }} </td> </tr> *}
    <tr> <td> Date Valid </td> <td> {{ date_validated }} </td> </tr>
    ""
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<tr> <td> Status </td> <td> {{ status }} </td> </tr>',
    '<tr> <td> Application Type </td> <td> {{ application_type }} </td> </tr>',
    '<tr> <td> Comment By </td> <td> {{ comment_date }} </td> </tr>',
    '<tr> <td> Town Council </td> <td> {{ parish }} </td> </tr>',
    '<tr> <td> Ward </td> <td> {{ ward_name }} </td> </tr>',
    '<tr> <td> Northing </td> <td> {{ northing }} </td> </tr>',
    '<tr> <td> Easting </td> <td> {{ easting }} </td> </tr>',
    '<tr> <td> Decision Level </td> <td> {{ decided_by }} </td> </tr>',
    '<tr> <td> Decision Type </td> <td> {{ decision }} </td> </tr>',
    ""<tr> <td> Decision Target Date </td> <td> {{ target_decision_date }} </td> </tr>
    <tr> <td> Decision Date </td> <td> {{ decision_date }} </td> </tr>"",
    '<tr> <td> Applicant Name </td> <td> {{ applicant_name }} </td> </tr>',
    '<tr> <td> Agents Name </td> <td> {{ agent_name }} </td> </tr>',
    '{* <tr> <td> Applicant Address </td> <td> {{ [applicant_address] }} </td> </tr> *}',
    '{* <tr> <td> Agents Address </td> <td> {{ [agent_address] }} </td> </tr> *}',
    '<tr> <td> Case Officers Name </td> <td> {{ case_officer }} </td> </tr>',
    '<tr> <td> Committee Date </td> <td> {{ meeting_date }} </td> </tr>',
    '<tr> <td> Appeal Received </td> <td> {{ appeal_date }} </td> </tr>',
    '<tr> <td> Appeal Type </td> <td> {{ appeal_type }} </td> </tr>',
    ""<tr> <td> Appeal Decision </td> <td> {{ appeal_result }} </td> </tr>
    <tr> <td> Appeal Decision Date </td> <td> {{ appeal_decision_date }} </td> </tr>"",
    ]
    detail_tests = [
        { 'uid': '048879', 'len': 21 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 47 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 4 } ]

    def get_id_batch (self, date_from, date_to): 

        final_result = []
        dfrom = date_from.strftime(self._request_date_format)
        dto = date_to.strftime(self._request_date_format)
        search_param = self._search_tpl % (dfrom, dto)
        url = self._search_url + '?s=' + urllib.quote_plus(search_param)
        response = self.br.open(url)
        
        if response:
            html = response.read()
            #self.logger.debug("ID batch page html: %s", html)
            url = response.geturl()
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                for r in result['records']: # supplied URL does not work off form/session - replace with normalised version
                    r['url'] = self._applic_url + urllib.quote_plus(r['uid'])
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            else:
                self.logger.debug("Empty id result page")
                         
        return final_result
               
    def get_html_from_uid(self, uid):
        url = self._applic_url + urllib.quote_plus(uid)
        return self.get_html_from_url(url)"""

