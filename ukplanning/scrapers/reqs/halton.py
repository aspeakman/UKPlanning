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
from .. import basereq
try:
    from ukplanning import scrapeutils
except ImportError:
    import scrapeutils
import urllib, urlparse
from datetime import timedelta
import re
import requests

# Now using requests[security] package for kludge fix verify=False work around for the following errors found with mechanize
# error:140770FC:SSL routines:SSL23_GET_SERVER_HELLO:unknown protocol
# error:1408F10B:SSL routines:SSL3_GET_RECORD:wrong version number
#[Errno bad handshake] [('SSL routines', 'ssl3_get_server_certificate', 'certificate verify failed')]

# also see Castle Point
# and alternative non-requests fix for Suffolk

requests.packages.urllib3.disable_warnings()

class HaltonScraper(basereq.DateReqScraper):

    min_id_goal = 350
    
    _authority_name = 'Halton'
    _uid_only = True # can only access applications via uid not url
    _search_url = 'https://webapp.halton.gov.uk/PlanningApps/index.asp'
    #_search_url = 'http://www.halton.gov.uk/planningapps/'
    _date_from_field = 'DateApValFrom' 
    _date_to_field = 'DateApValTo' # NB end date is exclusive
    _search_fields = {
        'DropWeekDate': '0',
        'DropAppealStatus': '0',
        'Action': 'Search' }
    _next_fields = {
        'Pagesize': '5',
        'Action': 'Next' }
    _ref_field = 'CaseNo'
    #_next_form = 'formNext'
    #_search_form = '0'
    #_search_submit = 'Action'
    _scrape_max_recs = '<td class="recordCell" colspan="5"> Record: 1 of {{ max_recs }} </td>'

    _scrape_ids = """
    <div class="hbc-main">
    {* <table class="tab"> <table />
    <tr> Case No: {{ [records].uid }} Officer name: </tr>
    </table> *}
    </div>
    """
    _address_regex = re.compile(r'\s+AT\s+(.+?)$', re.I) # matches AT address at the end of the proposal (ignoring case)
    _scrape_data_block = """
    <table id="Details0"> {{ block|html }} </table>
    """
    _scrape_min_data = """
    <tr> <td> Case No </td> <td> {{ reference }} </td> </tr>
    <tr> <td> Details of Proposal </td> <td> {{ description }} </td> </tr>
    <tr> <td> Date Received </td> <td> {{ date_received }} </td> </tr>
    <tr> <td> Date Valid </td> <td> {{ date_validated }} </td> </tr>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<tr> <td> Officer Name </td> <td> {{ case_officer }} </td> </tr>',
    '<tr> <td> Status </td> <td> {{ status }} </td> </tr>',
    '<tr> <td> Ward </td> <td> {{ ward_name }} </td> </tr>',
    '<tr> <td> Applicants Name </td> <td> {{ applicant_name }} </td> <td> Applicants Address </td> <td> {{ applicant_address }} </td> </tr>',
    '<tr> <td> Agents Name </td> <td> {{ agent_name }} </td> <td> Agents Address </td> <td> {{ agent_address }} </td> </tr>',
    '<tr> <td> Comment Between </td> <td> {{ consultation_start_date }} and {{ consultation_end_date }} </td> </tr>',
    '<tr> <td> Target Date </td> <td> {{ target_decision_date }} </td> </tr>',
    '<tr> <td> Decision Date </td> <td> {{ decision_date }} </td> </tr>',
    '<a href="{{ comment_url|abs }}"> Comment Now </a>',
    ]
    detail_tests = [
        { 'uid': '11/00342/FUL', 'len': 14 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '01/09/2015', 'to': '13/09/2015', 'len': 18 },
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 15 },
        { 'from': '15/08/2012', 'to': '15/08/2012', 'len': 1 } ]
    
    def get_id_batch (self, date_from, date_to):

        final_result = []
        new_date_to = date_to + timedelta(days=1) # end date is exclusive, increment end date by one day
        r = self.rs.get(self._search_url, verify=False, timeout=self._timeout)
        #response.set_data(r.text)
        #self.br.set_response(response)
        #response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s", response.read())
        
        fields = {}
        fields.update(self._search_fields)
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = new_date_to.strftime(self._request_date_format)
        #scrapeutils.setup_form(self.br, self._search_form, fields)
        #self.logger.debug("ID batch form: %s", str(self.br.form))
        #response = scrapeutils.submit_form(self.br)
        #html = response.read()
        r = self.rs.post(self._search_url, verify=False, data=fields, timeout=self._timeout)
        html = r.text
        #self.logger.debug("ID batch page html: %s", html)
        
        try:
            result = scrapemark.scrape(self._scrape_max_recs, html)
            max_recs = int(result['max_recs'])
        except:
            max_recs = 0
        
        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        while html and len(final_result) < max_recs and page_count < max_pages:
            #url = response.geturl()
            url = r.url
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
                #scrapeutils.setup_form(self.br, self._next_form)
                #self.logger.debug("ID next form: %s", str(self.br.form))
                #response = scrapeutils.submit_form(self.br, self._search_submit)
                #html = response.read()
                fields = {}
                fields.update(self._next_fields)
                fields['CurrentRecord'] = str((page_count-1)*5)
                fields['MaxRecord'] = str(max_recs)
                fields['MaxPage'] = str(int((max_recs+4)/5))
                r = self.rs.post(self._search_url, verify=False, data=fields, timeout=self._timeout)
                html = r.text
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next form after %d pages", page_count)
                break
        
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
        
        return final_result
        
    def get_html_from_url(self, url):
        """ Get the html and url for one record given a URL """
        if self._uid_only:
            return None, None
        if self._search_url and self._detail_page:
            url_parts = urlparse.urlsplit(url)
            url = urlparse.urljoin(self._search_url, self._detail_page)
            if url_parts.query:
                url = url + '?' + url_parts.query
        response = self.rs.get(url, verify=False, timeout=self._timeout) 
        return self._get_html(response)
        
    def get_html_from_uid (self, uid):
        #response = self.br.open(self._search_url)
        r = self.rs.get(self._search_url, verify=False, timeout=self._timeout)
        #self.logger.debug("ID detail start html: %s", response.read())
        fields = {}
        fields[self._ref_field] = uid
        fields.update(self._search_fields)
        #scrapeutils.setup_form(self.br, self._search_form, fields)
        #self.logger.debug("Get UID form: %s", str(self.br.form))
        #response = scrapeutils.submit_form(self.br)
        #html, url = self._get_html(response)
        r = self.rs.post(self._search_url, verify=False, data=fields, timeout=self._timeout)
        html = r.text
        url = r.url
        result = scrapemark.scrape(self._scrape_ids, html, url)
        if result and result.get('records'):
            self._clean_ids(result['records'])
            for rr in result['records']:
                if rr.get('uid', '') == uid:
                    return html, url
        return None, None 
        
    def _clean_record(self, record):
        super(HaltonScraper, self)._clean_record(record)
        if record.get('description') and not record.get('address'):
            address_match = self._address_regex.search(record['description'])
            if address_match and address_match.group(1):
                address = address_match.group(1)
                record['address'] = address
            else:
                record['address'] = record['description']
        

