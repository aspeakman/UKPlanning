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
from datetime import date
try:
    from ukplanning import scrapemark
except ImportError:
    import scrapemark
try:
    from ukplanning import scrapeutils
except ImportError:
    import scrapeutils
from .. import base
import urllib, urlparse
import mechanize

# Carmarthenshire only now - see separate Telford module

class EAccessv2Scraper(base.DateScraper):

    min_id_goal = 200 # min target for application ids to fetch in one go
    
    _scraper_type = 'EAccessv2'
    _start_fields = { '__EVENTTARGET': 'lnkSearchPlanning', '__EVENTARGUMENT': '', }
    _request_date_format = '%d-%m-%Y'
    _progress_link = 'Progress'
    _detail_page = 'pa-applicationsummary.aspx'
    _handler = 'etree'
    
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <div class="informationarea"> {{ block|html }} </div>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <tr> Application number {{ reference }} </tr>
    <tr> Site address {{ address }} </tr>
    <tr> Descripton of proposal {{ description }} </tr>
    <tr> Date valid {{ date_validated }} </tr>
    """ # note spelling mistake (Descripton)
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
            response = self.br.follow_link(text=self._progress_link)
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
        
class CarmarthenshireScraper(EAccessv2Scraper):

    _authority_name = 'Carmarthenshire'
    _search_url = 'http://online.carmarthenshire.gov.uk/eaccessv2/search-all.aspx'
    _details_suffix = '?Tab=Details'
    _date_from_field = 'DCdatefrom'
    _date_to_field = 'DCdateto'
    _search_form = '0'
    _search_submit = 'btnSearchPlanningDetails'
    _search_fields = { '__EVENTTARGET': 'btnSearchPlanningDetails', '__EVENTARGUMENT': '', }
    _search_action = 'SearchAllPCByDetailsResults.aspx'
    _link_next = 'Next'
    _scrape_max_recs = '<span id="lblNowShowingTop"> of {{ max_recs }} items </span>'
    _scrape_ids = """
    <table id="TableResults"> <tr />
        {* <tr>
        <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
        <td> Development Control </td>
        </tr> *}
    </table>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <tr> Application number {{ reference }} </tr>
    <tr> Site address {{ address }} </tr>
    <tr> Descripton of proposal {{ description }} </tr>
    <tr> Date valid {{ date_validated }} </tr>
    """ # note spelling mistake (Descripton)
    detail_tests = [
        { 'uid': 'W/25167', 'len': 23 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 8 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 1 } ]
        
    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url + self._details_suffix, urllib.urlencode(self._start_fields))
        #self.logger.debug("Start html: %s", response.read())

        fields = {}
        fields.update(self._search_fields)
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields, self._search_action)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._search_submit)
        
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
                response = self.br.follow_link(text=self._link_next)
                html = response.read()
            except: # normal failure to find next page link at end of page sequence here
                self.logger.debug("No next link after %d pages", page_count)
                break
                
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
       
        return final_result


"""class TelfordScraper(EAccessv2Scraper): now new scraper for JSON service based on 'requests'

    _authority_name = 'Telford'
    _search_url = 'https://secure.telford.gov.uk/planning/search-all.aspx'
    _headers = {
    'User-Agent': 'Mozilla/5.0 (Windows; U; MSIE 7.0; Windows NT 6.0; en-US)',
    'Accept-Charset': 'UTF-8,*',
    'Accept': 'text/html',
    'Accept-Language': 'en-gb,en',
    }
    _date_from_field = 'ctl00$ContentPlaceHolder1$DCdatefrom'
    _date_to_field = 'ctl00$ContentPlaceHolder1$DCdateto'
    _search_form = '0'
    _search_submit = 'ctl00$ContentPlaceHolder1$btnSearchPlanningDetails'
    _result_tabs = [ 
        '',
        'ctl00$ContentPlaceHolder1$lbPlanning2ndLevel3',
        'ctl00$ContentPlaceHolder1$lbPlanning2ndLevel1', ]
    _search_fields = { '__EVENTTARGET': '', '__EVENTARGUMENT': '', }
    _next_fields = { '__EVENTTARGET': 'ctl00$ContentPlaceHolder1$gvResults$ctl01$lbPagerTopNext', '__EVENTARGUMENT': '', }
    _search_action = 'default.aspx'
    _scrape_max_recs = '<span id="ctl00_ContentPlaceHolder1_gvResults_ctl01_lblNowShowingTotal"> {{ max_recs }} </span>'
    _scrape_ids = ""
    <table> <tr /> <tr />
        {* <tr>
        <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
        </tr> *}
        <tr> <div class="resultsarea"> Showing </div> </tr>
    </table>
    ""
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = ""
    <tr> Application number {{ reference }} </tr>
    <tr> Site address {{ address }} </tr>
    <tr> Description of proposal {{ description }} </tr>
    <tr> Date valid {{ date_validated }} </tr>
    ""
    detail_tests = [
        { 'uid': 'TWC/2012/0233', 'len': 26 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '28/06/2011', 'to': '11/07/2011', 'len': 46 }, 
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 25 }, 
        { 'from': '15/08/2012', 'to': '15/08/2012', 'len': 6 },
        { 'from': '01/12/2015', 'to': '12/12/2015', 'len': 49 }, 
        ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url, urllib.urlencode(self._start_fields))
        #self.logger.debug("Start html: %s", response.read())

        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        n_recs = 0

        for tab in self._result_tabs:
            
            if not tab:
                fields = {}
                fields[self._date_from_field] = date_from.strftime(self._request_date_format)
                fields[self._date_to_field] = date_to.strftime(self._request_date_format)
                scrapeutils.setup_form(self.br, self._search_form, fields, self._search_action)
                self.logger.debug("ID batch form: %s", str(self.br.form))
                response = scrapeutils.submit_form(self.br, self._search_submit)
                html = response.read()
                #self.logger.debug("ID batch page html: %s", html)
            else:
                fields = { '__EVENTARGUMENT': '', }
                fields['__EVENTTARGET'] = tab
                try:
                    scrapeutils.setup_form(self.br, self._search_form, fields)
                except mechanize.FormNotFoundError as e:
                    continue
                for control in self.br.form.controls:
                    if control.type == "submit":
                        control.disabled = True
                self.logger.debug("ID next form: %s", str(self.br.form))
                response = scrapeutils.submit_form(self.br)
                html = response.read()
                #self.logger.debug("ID next tab html: %s", html)
            
            try:
                result = scrapemark.scrape(self._scrape_max_recs, html)
                max_recs = int(result['max_recs'])
            except:
                max_recs = 0
    
            n_recs += max_recs
            while response and len(final_result) < n_recs and page_count < max_pages:
                url = response.geturl()
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
                    fields = self._next_fields
                    scrapeutils.setup_form(self.br, self._search_form, fields)
                    for control in self.br.form.controls:
                        if control.type == "submit":
                            control.disabled = True
                    self.logger.debug("ID next form: %s", str(self.br.form))
                    response = scrapeutils.submit_form(self.br)
                    html = response.read()
                except: # normal failure to find next page link at end of page sequence here
                    self.logger.debug("No next form after %d pages", page_count)
                    break
                    
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
       
        return final_result"""
