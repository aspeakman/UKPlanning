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
from datetime import date
import re
import requests

# Now using requests[security] package for kludge fix verify=False and SSL3 force work around 
# Solves the following errors found with mechanize
# SSL error  on Telford - urlopen error EOF occurred in violation of protocol (_ssl.c:590)
# see https://stackoverflow.com/questions/14102416/python-requests-requests-exceptions-sslerror-errno-8-ssl-c504-eof-occurred
# See https://www.ssllabs.com/ssltest/analyze.html

requests.packages.urllib3.disable_warnings()

class TelfordScraper(basereq.DateReqScraper):
    
    min_id_goal = 200 # min target for application ids to fetch in one go
    
    _authority_name = 'Telford'
    _search_url = 'https://secure.telford.gov.uk/planning/search-all.aspx'
    _start_fields = { '__EVENTTARGET': 'lnkSearchPlanning', '__EVENTARGUMENT': '', }
    _action_url = 'https://secure.telford.gov.uk/planningsearch/default.aspx'
    _request_date_format = '%d-%m-%Y'
    _progress_page = 'pa-progresstracking-public.aspx'
    _detail_page = 'pa-applicationsummary.aspx'
    _date_from_field = 'ctl00$ContentPlaceHolder1$DCdatefrom'
    _date_to_field = 'ctl00$ContentPlaceHolder1$DCdateto'
    _search_form = '0'
    _search_submit = 'ctl00$ContentPlaceHolder1$btnSearchPlanningDetails'
    _result_tabs = [ 
        { 'target': '', 
            'scrape_max_recs': '<span id="ctl00_ContentPlaceHolder1_lblRegistered"> {{ max_recs }} </span>' },
        { 'target': 'ctl00$ContentPlaceHolder1$lbPlanning2ndLevel3',
            'scrape_max_recs': '<span id="ctl00_ContentPlaceHolder1_lblDetermined"> {{ max_recs }} </span>' },
        { 'target': 'ctl00$ContentPlaceHolder1$lbPlanning2ndLevel1',
            'scrape_max_recs': '<span id="ctl00_ContentPlaceHolder1_lblPARecieved"> {{ max_recs }} </span>' },]
    _search_fields = { '__EVENTTARGET': '', '__EVENTARGUMENT': '', 
            'ctl00$ContentPlaceHolder1$txtPlanningKeywords': '',
            'ctl00$ContentPlaceHolder1$dlPlanningParishs': '0',
            'ctl00$ContentPlaceHolder1$dlPlanningWard': '0',
            'ctl00$ContentPlaceHolder1$ddlPlanningapplicationtype': '0',
            'ctl00$ContentPlaceHolder1$txtDCAgent': '',
            'ctl00$ContentPlaceHolder1$txtDCApplicant': ''
    }
    _next_target = 'ctl00$ContentPlaceHolder1$gvResults$ctl01$lbPagerTopNext'
    _scrape_state1 = """
        <input name="__VIEWSTATE" value="{{ __VIEWSTATE }}" />
        <input name="__VIEWSTATEGENERATOR" value="{{ __VIEWSTATEGENERATOR }}" />
        <input name="__PREVIOUSPAGE" value="{{ __PREVIOUSPAGE }}" />
        <input name="__EVENTVALIDATION" value="{{ __EVENTVALIDATION }}" />   
    """
    _scrape_state2 = """
        <input name="__VIEWSTATE" value="{{ __VIEWSTATE }}" />
        <input name="__VIEWSTATEGENERATOR" value="{{ __VIEWSTATEGENERATOR }}" />
        <input name="__EVENTVALIDATION" value="{{ __EVENTVALIDATION }}" />   
    """
    _scrape_ids = """
    <table> <tr /> <tr />
        {* <tr>
        <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
        </tr> *}
        <tr> <div class="resultsarea"> Showing </div> </tr>
    </table>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <div class="informationarea"> {{ block|html }} </div>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <tr> Application number {{ reference }} </tr>
    <tr> Site address {{ address }} </tr>
    <tr> Description of proposal {{ description }} </tr>
    <tr> Date valid {{ date_validated }} </tr>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    "<tr> Application type {{ application_type }} </tr>", # OK
    '<ul id="ApplicationStatuslist"> <li class="selected"> {{ status }} </li> </ul>', # OK
    '<ul id="ApplicationStatuslist"> <li class="first selected"> {{ status }} </li> </ul>', # OK
    '<ul id="ApplicationStatuslist"> <li class="last selected"> {{ status }} </li> </ul>', # OK
    "<tr> Grid reference <span> {{ easting }} </span> <span> {{ northing }} </span> </tr>", # OK
    "<tr> Case officer {{ case_officer }} </tr>", # OK
    "<tr> Parish {{ parish }} </tr>", # OK
    "<tr> Ward {{ ward_name }} </tr>", # OK
    "<tr> Delegation level {{ decided_by }} </tr>", # OK
    """<tr> <th> Decision </th> {{ decision }} </tr>
    <tr> <th> Decision date </th> {{ decision_date }} </tr>""", # OK
    """<tr> Agent {{ agent_name }} </tr>
    <tr> Agent Company Name {{ agent_company }} </tr>""", # OK
    "<tr> Agent address {{ agent_address }} </tr>", # OK
    """<tr> Applicant {{ applicant_name }} </tr>
    <tr> Applicant Company Name {{ applicant_company }} </tr>""", #OK
    "<tr> Applicant address {{ applicant_address }} </tr>", # OK
    """<tr> <th> Appeal decision </th> {{ appeal_result }} </tr>
    <tr> <th> Appeal decision date </th> {{ appeal_decision_date }} </tr>""", # OK
    '<tr> Planning portal reference {{ planning_portal_id }} </tr>'
    ]
    _scrape_min_extra = """
    <tr> Application Received {{ date_received }} </tr>
    """
    # min field list used in testing only
    _min_fields = [ 'reference', 'address', 'description', 'date_received' ]
    # other parameters that appear on the progress page
    _scrape_optional_extra = [
    "<tr> Consultation expiry date {{ consultation_end_date }} </tr>", # OK
    "<tr> Press notice expires {{ last_advertised_date }} </tr>", # OK
    "<tr> Site notice expires {{ site_notice_end_date }} </tr>", # OK
    "<tr> Plans board date(s) {{ meeting_date }} </tr>", # OK
    "<tr> Planning committee date {{ meeting_date }} </tr>", # OK
    "<tr> Application expiry date {{ application_expires_date }} </tr>", # OK
    ]
    detail_tests = [
        { 'uid': 'TWC/2012/0233', 'len': 26 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '28/06/2011', 'to': '11/07/2011', 'len': 46 }, 
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 25 }, 
        { 'from': '15/08/2012', 'to': '15/08/2012', 'len': 6 },
        { 'from': '01/12/2015', 'to': '12/12/2015', 'len': 38 }, 
        ]
    
    # force use of insecure SSL3 - see https://www.ssllabs.com/ssltest/analyze.html
    def __init__(self, *args, **kwargs):
        super(TelfordScraper, self).__init__(*args, **kwargs)
        self.rs.mount('https://secure.telford.gov.uk', basereq.Ssl3HttpAdapter())

    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.rs.post(self._search_url, verify=False, data=self._start_fields, timeout=self._timeout)
        html, url = self._get_html(response)
        #self.logger.debug("Start html: %s", html)
        
        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        n_recs = 0
                 
        for tab in self._result_tabs:
            
            if not tab['target']:
                state_result = scrapemark.scrape(self._scrape_state1, html)
                fields = {}
                fields.update(self._search_fields)
                fields[self._search_submit] = 'Search'
                fields['__EVENTTARGET'] = ''
                if state_result:
                    for k,v in state_result.items():
                        fields[k] = v
                fields[self._date_from_field] = date_from.strftime(self._request_date_format)
                fields[self._date_to_field] = date_to.strftime(self._request_date_format)
                self.logger.debug("Batch form fields: %s", str(fields))
                response = self.rs.post(self._action_url, verify=False, data=fields, timeout=self._timeout)
                html, url = self._get_html(response)
                #self.logger.debug("ID batch page html: %s", html)
            else:
                state_result = scrapemark.scrape(self._scrape_state2, html)
                fields = {}
                fields.update(self._search_fields)
                fields['__EVENTTARGET'] = tab['target']
                if state_result:
                    for k,v in state_result.items():
                        fields[k] = v
                self.logger.debug("Tab form fields: %s", str(fields))
                response = self.rs.post(self._action_url, verify=False, data=fields, timeout=self._timeout)
                html, url = self._get_html(response)
                #self.logger.debug("ID next tab html: %s", html)
            
            try:
                result = scrapemark.scrape(tab['scrape_max_recs'], html)
                max_recs = int(result['max_recs'])
            except:
                max_recs = 0

            n_recs += max_recs
            while response and len(final_result) < n_recs and page_count < max_pages:
                result = scrapemark.scrape(self._scrape_ids, html, url)
                if result and result.get('records'):
                    page_count += 1
                    self._clean_ids(result['records'])
                    #for res in result['records']:
                    #    print res['uid']
                    final_result.extend(result['records'])
                    #print 'n', len(result['records'])
                else:
                    self.logger.debug("Empty result after %d pages", page_count)
                    break
                if len(final_result) >= n_recs: break
                try:
                    state_result = scrapemark.scrape(self._scrape_state2, html)
                    fields = {}
                    fields.update(self._search_fields)
                    fields['__EVENTTARGET'] = self._next_target
                    if state_result:
                        for k,v in state_result.items():
                            fields[k] = v
                    self.logger.debug("Next form fields: %s", str(fields))
                    response = self.rs.post(self._action_url, verify=False, data=fields, timeout=self._timeout)
                    html, url = self._get_html(response)
                except: # normal failure to find next page link at end of page sequence here
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
        
    def get_html_from_uid(self, uid):
        url = urlparse.urljoin(self._search_url, self._detail_page) + '?applicationnumber=' + urllib.quote_plus(uid)
        return self.get_html_from_url(url)
        
    def _get_details(self, html, this_url):
        """ Scrapes detailed information for one record given html and url 
        - this is an optional hook to allow data from multiple linked pages to be merged """
        result = self._get_detail(html, this_url)
        if 'scrape_error' in result:
            return result
        try:
            url_parts = urlparse.urlsplit(this_url)
            progress_url = urlparse.urljoin(self._search_url, self._progress_page) + '?' + url_parts.query
            self.logger.debug("Progress url: %s", progress_url)
            response = self.rs.get(progress_url, verify=False, timeout=self._timeout)
            html, url = self._get_html(response)
        except:
            self.logger.warning("No link to progress page found")
        else:
            #self.logger.debug("Html obtained from progress url: %s" % html)
            result2 = self._get_detail(html, url, self._scrape_data_block, self._scrape_min_extra, self._scrape_optional_extra)
            if 'scrape_error' not in result2:
                result.update(result2)
            else:
                self.logger.warning("No information found on progress page")
        return result

        

