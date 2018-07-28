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
try:
    from ukplanning import scrapeutils
except ImportError:
    import scrapeutils
from .. import basereq
import urllib
import requests

#Seems to have 2 separate lists ->
#Status = 1 = current undecided applications
#Status = 2 = historical decided applications

# Now using requests[security] package for kludge fix verify=False and SSL3 force work around 
# Solves the following errors found with mechanize
# SSL error  on Telford - urlopen error EOF occurred in violation of protocol (_ssl.c:590)
# see https://stackoverflow.com/questions/14102416/python-requests-requests-exceptions-sslerror-errno-8-ssl-c504-eof-occurred
# The site offers mainly insecure SSL protocols - see
# https://www.ssllabs.com/ssltest/analyze.html?d=www2.wokingham.gov.uk

# also see Carmarthenshire and Telford

requests.packages.urllib3.disable_warnings()

class WokinghamScraper(basereq.PeriodReqScraper):

    min_id_goal = 350 # min target for application ids to fetch in one go = 150 or so per month
    
    _authority_name = 'Wokingham'
    _period_type = 'Month'
    _date_field = { 'month': 'Month', 'year': 'Year' }
    _query_fields = {  'pgid': '1813', 'tid': '147' }
    _scrape_next_link = """
    <div class="PageNavBar"> <strong /> 
    <a href="{{ next_link|abs }}" /> </div>
    """
    #request_date_format = '%-d/%-m/%Y' only works on Linux
    _search_url = 'https://www2.wokingham.gov.uk/environment/planning/planning-applications/planning-applications-search'
    _results_url = 'https://www2.wokingham.gov.uk/sys_upl/templates/BT_WOK_PlanningApplication/BT_WOK_PlanningApplication_details.asp'
    #_applic_url = 'https://www2.wokingham.gov.uk/sys_upl/templates/BT_WOK_PlanningApplication/BT_WOK_PlanningApplication_details.asp?action=DocumentView&pgid=22472&tid=176'
    _applic_url = 'https://www2.wokingham.gov.uk/sys_upl/templates/BT_WOK_PlanningApplication/BT_WOK_PlanningApplication_details.asp?action=DocumentView&pgid=1813&tid=147'
    _scrape_ids = """
    <div id="template-zone">
        {* <table summary="*"> 
        <tr> Application No: {{ [records].uid }} </tr>
        <tr> Plans and Documents: <a href="{{ [records].url|abs }}" /> </tr>
        </table>  *}
    </div>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <div id="content-inner">  {{ block|html }} </div>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <table summary="*">
    <tr> Application No: {{ reference }} </tr>
    <tr> Location: {{ address }} </tr>
    <tr> Received Date: {{ date_received }} </tr>
    <tr> Valid Date: {{ date_validated }} </tr>
    <tr> Proposal: {{ description }} </tr>
    </table>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<table summary="*"> <tr> Consultation Start Date: {{ consultation_start_date }} </tr> </table>',
    '<table summary="*"> <tr> Deadline for Comments: {{ consultation_end_date }} </tr> </table>',
    '<table summary="*"> <tr> Planning Officer: {{ case_officer }} </tr> </table>',
    '<table summary="*"> <tr> Decision: {{ decision }} </tr> </table>',
    '<table summary="*"> <tr> Decision Date: {{ decision_date }} </tr> </table>',
    '<table summary="*"> <tr> Appeal Received Date: {{ appeal_date }} </tr> </table>',
    '<div class="SmallTitle"> {{ parish }} Parish </div>',
    ]
    detail_tests = [
        { 'uid': 'F/2010/2048', 'len': 11 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'date': '13/09/2012', 'len': 141 }, # 0 + 141
        { 'date': '13/08/2012', 'len': 159 } ] # 1 + 158

    # force use of insecure SSL3 - see https://www.ssllabs.com/ssltest/analyze.html
    def __init__(self, *args, **kwargs):
        super(WokinghamScraper, self).__init__(*args, **kwargs)
        self.rs.mount('https://www2.wokingham.gov.uk', basereq.Ssl3HttpAdapter())
        
    def get_id_period (self, this_date):

        final_result = []
        from_dt, to_dt = scrapeutils.inc_dt(this_date, self._period_type)
        
        fields = {}
        fields.update(self._query_fields)
        fields [self._date_field['month']] = str(this_date.month)
        fields [self._date_field['year']] = str(this_date.year)

        page_count = 0
        max_pages = (2 * self.min_id_goal / 5) + 20 # guard against infinite loop  
        for i in range(1, 3):
            fields['Status'] = str(i)
            #response = self.br.open(self._results_url + '?' + urllib.urlencode(fields))
            this_url = self._results_url + '?' + urllib.urlencode(fields)
            response = self.rs.get(this_url, verify=False, timeout=self._timeout)
            while response and page_count < max_pages:
                html, url = self._get_html(response)
                #self.logger.debug("ID batch page html: %s", html)
                result = scrapemark.scrape(self._scrape_ids, html, url)
                if result and result.get('records'):
                    page_count += 1
                    self._clean_ids(result['records'])
                    final_result.extend(result['records'])
                else:
                    self.logger.debug("Empty result after %d pages", page_count)
                    break
                try:
                    result = scrapemark.scrape(self._scrape_next_link, html, url)
                    #response = self.br.open(result['next_link'])
                    response = self.rs.get(result['next_link'], verify=False, timeout=self._timeout)
                except:
                    self.logger.debug("No next link after %d pages", page_count)
                    break
            
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
            
        if final_result:
            return final_result, from_dt, to_dt
        else:
            return [], None, None # monthly scraper - so empty result is always invalid

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
        url = self._applic_url + '&ApplicationCode='+ urllib.quote_plus(uid)
        return self.get_html_from_url(url)


