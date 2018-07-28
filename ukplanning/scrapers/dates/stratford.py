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
import urllib, urlparse
from datetime import datetime

class StratfordOnAvonScraper(base.DateScraper):

    min_id_goal = 300 # min target for application ids to fetch in one go

    _authority_name = 'StratfordOnAvon'
    _handler = 'etree'
    _search_url = 'https://apps.stratford.gov.uk/eplanning/AdvancedSearch.aspx'
    _detail_page = 'AppDetail.aspx'
    _results_page = 'AppSearchResult.aspx'
    _search_form = 'aspnetForm'
    _date_from_field = 'datereceivedfrom'
    _date_to_field = 'datereceivedto'
    _uid_field = 'appref'
    _search_fields = { 'searchby': 'advanced' }
    _applic_fields = { 'searchby': 'application' }
    _next_target = 'ctl00$ContentPlaceHolder1$searchResultGridView'
    _scrape_ids = """
    <div class="AspNet-GridView">
    <table class="DATEAPVAL|DESC"> <tbody>
    {* <tr> <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td> </tr>  *}
    </tbody> </table> </div>
    """
    _scrape_max_recs = '<span id="ctl00_ContentPlaceHolder1_lbResult"> <strong> {{ max_recs }} </strong> </span>'

    _scrape_data_block = '<form id="aspnetForm"> {{ block|html }} </form>'
    _scrape_min_data = """
    <span id="ctl00_ContentPlaceHolder1_lbApplicationReference"> {{ reference }} </span>
    <span id="ctl00_ContentPlaceHolder1_lbAddress"> {{ address }} </span>
    <div class="row"> <div class="left"> Proposal </div> <div class="right"> {{ description }} </div> </div>
    <div class="row"> <div class="column1"> Application Received </div> <div class="column2"> {{ date_received }} </div> </div>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<div class="row"> <div class="left"> Application Type </div> <div class="right"> {{ application_type }} </div> </div>',
    '<div class="row"> <div class="left"> Status </div> <div class="right"> {{ status }} </div> </div>',
    '<div class="row"> <div class="left"> Case Officer </div> <div class="right"> {{ case_officer }} </div> </div>',
    '<div class="row"> <div class="left"> Parish </div> <div class="right"> {{ parish }} </div> </div>',
    '<div class="row"> <div class="left"> Current Ward </div> <div class="right"> {{ ward_name }} </div> </div>',
    """<div class="row"> <div class="left"> Decision </div> <div class="right"> {{ decision }} </div> </div>
    <div class="row"> <div class="left"> Decision Issued </div> <div class="right"> {{ decision_issued_date }} </div> </div>""",
    '<div class="row"> <div class="left"> Applicant Name </div> <div class="right"> {{ applicant_name }} </div> </div>',
    '<div class="row"> <div class="left"> Applicant Address </div> <div class="right"> {{ applicant_address }} </div> </div>',
    """<div class="row"> <div class="left"> Agent's Name </div> <div class="right"> {{ agent_name }} </div> </div>""",
    """<div class="row"> <div class="left"> Agent's Address </div> <div class="right"> {{ agent_address }} </div> </div>""",
    '<div class="row"> <div class="column1"> Application Valid </div> <div class="column2"> {{ date_validated }} </div> </div>',
    '<div class="row"> <div class="column1"> Neighbour Notifications sent </div> <div class="column2"> {{ neighbour_consultation_start_date }} </div> </div>',
    '<div class="row"> <div class="column1"> Standard Consultations sent </div> <div class="column2"> {{ consultation_start_date }} </div> </div>',
    '<div class="row"> <div class="column1"> Last Advertised </div> <div class="column2"> {{ last_advertised_date }} </div> </div>',
    '<div class="row"> <div class="column1"> Permission Expiry </div> <div class="column2"> {{ permission_expires_date }} </div> </div>',
    '<div class="row"> <div class="column3"> Target Date for Determination </div> <div class="column4"> {{ target_decision_date }} </div> </div>',
    '<div class="row"> <div class="column3"> Expiry Date for Neighbour Notifications </div> <div class="column4"> {{ neighbour_consultation_end_date }} </div> </div>',
    '<div class="row"> <div class="column3"> Expiry Date for Standard Consultations </div> <div class="column4"> {{ consultation_end_date }} </div> </div>',
    '<div class="row"> <div class="column3"> Overall Expiry Date </div> <div class="column4"> {{ application_expires_date }} </div> </div>',
    '<div class="row"> <div class="column3"> Committee Date </div> <div class="column4"> {{ meeting_date }} </div> </div>',
    '<a id="ctl00_ContentPlaceHolder1_lnkViewMap" href="Map.aspx?east={{easting}}&amp;north={{northing}}&amp;appref={{reference}}"> View Map </a>',
    ]
    detail_tests = [
        { 'uid': '12/01924/FUL', 'len': 23 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 26 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 13 } ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        
        fields = {}
        fields.update(self._search_fields)
        fields [self._date_from_field] = date_from.strftime(self._request_date_format)
        fields [self._date_to_field] = date_to.strftime(self._request_date_format)
        
        self.logger.debug("Fields: %s", str(fields))
        query = urllib.urlencode(fields)
        url = urlparse.urljoin(self._search_url, self._results_page) + '?' + query
        response = self.br.open(url)
        
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
                fields = { '__EVENTTARGET': self._next_target }
                fields['__EVENTARGUMENT'] = 'Page$' + str(page_count+1)
                scrapeutils.setup_form(self.br, self._search_form, fields)
                self.logger.debug("Next page form: %s", str(self.br.form))
                response = scrapeutils.submit_form(self.br)
                html = response.read()
                #self.logger.debug("ID next page html: %s", html)
            except: # normal failure to find next page link at end of page sequence here
                self.logger.debug("No next form after %d pages", page_count)
                break
        
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
            
        return final_result
        
    def get_html_from_uid(self, uid): 
        fields = {}
        fields.update(self._applic_fields)
        fields[self._uid_field] = uid
        self.logger.debug("UID fields: %s", str(fields))
        query = urllib.urlencode(fields)
        url = urlparse.urljoin(self._search_url, self._results_page) + '?' + query
        response = self.br.open(url)
        html = response.read()
        url = response.geturl()
        return html, url
        
    # note Stratford service is down for maintenance between midnight and 6 30 am
    @classmethod
    def can_run(cls):
        now = datetime.now()
        if now.hour <= 7:
            return False
        else:
            return True
        
        

