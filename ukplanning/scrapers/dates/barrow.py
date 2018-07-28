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
import re
from datetime import timedelta


class BarrowScraper(base.DateScraper):

    min_id_goal = 350
    
    _authority_name = 'Barrow'
    #_search_url = 'http://www.barrowbc.gov.uk/papps/search.aspx'
    _search_url = 'http://www.barrowbc.gov.uk/residents/planning/local-planning-applications/application-search/'
    _find_url = 'http://www.barrowbc.gov.uk/residents/planning/local-planning-applications/weekly-list/weekly-details/'
    #_find_page = 'weeklydetails.aspx'
    _request_date_format = '%d%%20%B%%20%Y'
    #_ref_field = 'txtSearch'
    #_search_submit = 'btnSearch'
    #_search_form = '0'
    
    _search_query = 'sdate=%s&edate=%s&type=r'
    _scrape_ids = """
    <div id="-ux-content">
    <table> <tr />
         {* <tr> <td/> <td/> <td/> <td/>
         <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td> 
         </tr> *}
    </table>
    </div>"""
    
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <div id="-ux-content"> {{ block|html }} </div>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <td> <label> Ref No: </label> </td> <td> <input value="{{ reference }}" /> </td>
    <td> <label> Received Date: </label> </td> <td> <input value="{{ date_received }}" /> </td>
    <td> <label> Site Address: </label> </td> <td> <textarea> {{ address }} </textarea> </td>
    <td> <label> Proposal: </label> </td> <td> <textarea> {{ description }} </textarea> </td>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<td> <label> Application Type: </label> </td> <td> <textarea> {{ application_type }} </textarea> </td>',
    '<td> <label> Valid Date: </label> </td> <td> <input value="{{ date_validated }}" /> </td>',
    '<td> <label> Eastings: </label> </td> <td> <input value="{{ easting }}" /> </td>',
    '<td> <label> Northings: </label> </td> <td> <input value="{{ northing }}" /> </td>',
    '<td> <label> Ward: </label> </td> <td> <input value="{{ ward_name }}" /> </td>',
    '<td> <label> Parish: </label> </td> <td> <input value="{{ parish }}" /> </td>',
    '<td> <label> Decision: </label> </td> <td> <input value="{{ decision }}" /> </td>',
    '<td> <label> Decision Notice Sent Date: </label> </td> <td> <input value="{{ decision_date }}" /> </td>',
    '<td> <label> Committee Date: </label> </td> <td> <input value="{{ meeting_date }}" /> </td>',
    '<td> <label> Committee Type: </label> </td> <td> <input value="{{ decided_by }}" /> </td>',
    '<td> <label> Target Date: </label> </td> <td> <input value="{{ target_decision_date }}" /> </td>',
    '<td> <label> Public Consult Start: </label> </td> <td> <input value="{{ consultation_start_date }}" /> </td>',
    '<td> <label> Public Consult End: </label> </td> <td> <input value="{{ consultation_end_date }}" /> </td>',
    '<td> <label> Applicant Name: </label> </td> <td> <input value="{{ applicant_name }}" /> </td>',
    '<td> <label> Applicant Address: </label> </td> <td> <textarea> {{ applicant_address }} </textarea> </td>',
    '<td> <label> Agent Name: </label> </td> <td> <input value="{{ agent_name }}" /> </td>',
    '<td> <label> Agent Address: </label> </td> <td> <textarea> {{ agent_address }} </textarea> </td>',
    '<a title="View list of Case Officer Details"> {{ case_officer }} </a>',
    '<td> <label> Appeal Type: </label> </td> <td> <input value="{{ appeal_type }}" /> </td>',
    '<td> <label> Appeal Lodged: </label> </td> <td> <input value="{{ appeal_date }}" /> </td>',
    '<td> <label> Appeal Decision: </label> </td> <td> <input value="{{ appeal_result }}" /> </td>',
    '<td> <label> Appeal Decision Date: </label> </td> <td> <input value="{{ appeal_decision_date }}" /> </td>',
    ]
    detail_tests = [
        { 'uid': 'B21/2012/0538', 'len': 23 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 17 },
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 4 } ]
    
    def get_id_batch (self, date_from, date_to):

        final_result = []
        
        dfrom = date_from.strftime(self._request_date_format)
        dto = date_to.strftime(self._request_date_format)
        query = self._search_query % (dfrom, dto)
        #url = urlparse.urljoin(self._search_url, self._find_page)
        #self.logger.debug("Url: %s" % self._find_url + '?' + query)
        response = self.br.open(self._find_url + '?' + query)
        
        if response:
            html = response.read()
            url = response.geturl()
            #self.logger.debug("Batch html: %s" % html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            
        return final_result
        
    """def get_html_from_uid (self, uid):
        response = self.br.open(self._search_url)
        #self.logger.debug("ID detail start html: %s", response.read())
        fields = {  self._ref_field: uid }
        scrapeutils.setup_form(self.br, self._search_form, fields)
        response = scrapeutils.submit_form(self.br, self._search_submit)
        html, url = self._get_html(response)
        result = scrapemark.scrape(self._scrape_ids2, html, url)
        if result and result.get('records'):
            self._clean_ids(result['records'])
            for r in result['records']:
                if r.get('uid', '') == uid:
                    #self.logger.debug("Scraped submit button: %s", r['submit'])
                    scrapeutils.setup_form(self.br, self._search_form)
                    response = scrapeutils.submit_form(self.br, r['submit'])
                    html, url = self._get_html(response)
                    #self.logger.debug("ID detail html: %s", html)
                    return html, url
        return None, None"""
        
    def get_html_from_uid(self, uid): 
        url = self._search_url + '?Ref=' + urllib.quote_plus(uid)
        return self.get_html_from_url(url)
        


