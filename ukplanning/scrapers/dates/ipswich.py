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
from datetime import timedelta

class IpswichScraper(base.DateScraper):

    min_id_goal = 350
    
    _authority_name = 'Ipswich'
    _search_url = 'https://ppc.ipswich.gov.uk/appnsearch.asp'
    _detail_page = 'appndetails.asp'
    _date_from_field = 'txtValStartDate' # NB both start and end date are exclusive
    _date_to_field = 'txtValEndDate' 
    _search_form = 'makeSearch'
    _search_submit = 'imgSubmit'
    _scrape_ids = """
    <table id="dgSearchResults"> <tr />
         {* <tr> <td> {{ [records].uid }} </td>
            <td> <a href="{{ [records].url|abs }}"> <img alt="View Application"> </a> </tr>
           *}
    </table>"""
    _scrape_next = '<a href="{{ next_link }}"> <img alt="Next Page" title="Next Page"> </a>'
    _scrape_max_recs = '<form id="searchResults"> <p> {{ max_recs }} applications found </p> </form>'

    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <form id="details"> {{ block|html }} </form>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <input id="txtAppNo" value="{{ reference }}"/>
    <textarea id="txtAddress"> {{ address }} </textarea>
    <textarea id="txtProposal"> {{ description }} </textarea>
    <input id="txtAppRec" value="{{ date_received }}"/>
    <input id="txtAppVal" value="{{ date_validated }}"/>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<input id="txtWard" value="{{ ward_name }}"/>',
    '<input id="txtParish" value="{{ parish }}"/>',
    '<input id="txtCaseOfficer" value="{{ case_officer }}"/>',
    '<input id="txtAppealDecision" value="{{ appeal_result }}"/>',
    '<input id="txtAppType" value="{{ application_type }}"/>',
    '<input id="txtStatus" value="{{ status }}"/>',
    '<input id="txtApplicantName" value="{{ applicant_name }}"/>',
    '<input id="txtAgentName" value="{{ agent_name }}"/>',
    '<textarea id="txtApplicantAddress"> {{ applicant_address }} </textarea>',
    '<textarea id="txtAgentAddress"> {{ agent_address }} </textarea>',
    """<a href="javascript:openMapWindow('http://gis.ipswich.gov.uk/Geomediawww/asp/MAPFRAMESET_PPC.asp', 'APP', {{easting}}, {{northing}} )">
    <img src="images/view_map_on.gif" alt="View Map" title="View Map">
    </a>""",
    '<input id="txt8Week" value="{{ target_decision_date }}"/>',
    '<input id="txtActualComm" value="{{ meeting_date }}"/>',
    '<input id="txtNCSent" value="{{ neighbour_consultation_start_date }}"/>',
    '<input id="txtNCExpires" value="{{ neighbour_consultation_end_date }}"/>',
    '<input id="txtSCSent" value="{{ consultation_start_date }}"/>',
    '<input id="txtSCExpires" value="{{ consultation_end_date }}"/>',
    '<input id="txtAdvertisedOn" value="{{ last_advertised_date }}"/>',
    '<input id="txtAdExpires" value="{{ latest_advertisement_expiry_date }}"/>',
    '<input id="txtSNPosted" value="{{ site_notice_start_date }}"/>',
    '<input id="txtSNExpires" value="{{ site_notice_end_date }}"/>',
    '<input id="txtDecIssued" value="{{ decision_date }}"/>',
    '<input id="txtAppealLodged" value="{{ appeal_date }}"/>',
    '<input id="txtDecOnAppeal" value="{{ appeal_decision_date }}"/>',
    ]
    detail_tests = [
        { 'uid': '12/00735/FUL', 'len': 25 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 25 },
        { 'from': '15/08/2012', 'to': '15/08/2012', 'len': 6 } ]
    
    def get_id_batch (self, date_from, date_to):

        final_result = []
        new_date_from = date_from - timedelta(days=1) # start date is exclusive, decrement start date by one day
        date_to = date_to + timedelta(days=1) # end date is exclusive, increment end date by one day
        response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s", response.read())
        
        fields = {}
        fields[self._date_from_field] = new_date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
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
                result = scrapemark.scrape(self._scrape_next, html, url)
                response = self.br.open(result['next_link'])
                html = response.read()
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next link after %d pages", page_count)
                break
        
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
            
        return final_result
        
    def get_html_from_uid(self, uid):
        url = urlparse.urljoin(self._search_url, self._detail_page) + '?iAppID=' + urllib.quote_plus(uid)
        return self.get_html_from_url(url)
        
        

