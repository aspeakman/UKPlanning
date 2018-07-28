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

class DorsetForYouScraper(base.DateScraper):

    min_id_goal = 300 # min target for application ids to fetch in one go

    _handler = 'etree'
    _scraper_type = 'DorsetForYou'
    _search_url ='http://webapps.westdorset-weymouth.gov.uk/PlanningApps/Pages/Search.aspx'
    _search_form = 'form1'
    _date_from_field = 'txtRegFrom'
    _date_to_field = 'txtRegTo'
    _detail_page = 'Planning.aspx'
    _search_submit = 'btnSearch'
    
    _scrape_ids = """
    <table id="gvApplications"> <tr />
    {* <tr> <td /> <td> {{ [records].uid }} </td> </tr>  *}
    </table>
    """ # note URL not available but computed in get_id_batch
    _scrape_id = """
    <span id="lblAppNo"> {{ uid }} </span>
    """
    _scrape_data_block = '<form id="form1"> {{ block|html }} </form>'
    _scrape_min_data = """
    <span id="lblAddress"> {{ address }} </span>
    <span id="lblAppNo"> {{ reference }} </span>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<span id="lblProposal"> {{ description }} </span>',
    '<span id="lblRegistrationDate"> {{ date_validated }} </span>',
    '<span id="lblStatus"> {{ status }} </span>',
    '<span id="lblDecisionDate"> {{ decision_date }} </span>',
    '<span id="lblDateMadeLive"> {{ consultation_start_date }} </span>',
    '<span id="lblCaseOfficer"> {{ case_officer }} </span>',
    '<span id="lblParish"> {{ parish }} </span>',
    '<span id="lblGridRef"> {{ easting }}/{{ northing }} </span>',
    '<span id="lblApplicantName"> {{ applicant_name }} </span>',
    '<span id="lblApplicantAddress"> {{ applicant_address }} </span>',
    '<span id="lblAgentName"> {{ agent_name }} </span>',
    '<span id="lblAgentAddress"> {{ agent_address }} </span>',
    ]

    detail_tests = [
        { 'uid': '8/11/0324', 'len': 15 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 19 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 } ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s", response.read())

        fields = {}
        fields.update(self._search_fields)
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._search_submit)
        
        applic_url = urlparse.urljoin(self._search_url, self._detail_page) + '?App='
        if response:
            html = response.read()
            url = response.geturl()
            #self.logger.debug("ID batch page html: %s", html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                for record in result['records']:
                    record['url'] = applic_url + urllib.quote_plus(record['uid'])
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            if not final_result: # is it a single record?
                single_result = scrapemark.scrape(self._scrape_id, html, url)
                if single_result:
                    single_result['url'] = url
                    self._clean_record(single_result)
                    final_result = [ single_result ]
                
        return final_result
        
    def get_html_from_uid(self, uid):
        url = urlparse.urljoin(self._search_url, self._detail_page) + '?App=' + urllib.quote_plus(uid)    
        return self.get_html_from_url(url)

class WestDorsetScraper(DorsetForYouScraper):

    _authority_name = 'WestDorset'
    _search_fields = { 'ddlAuthority': 'WDDC' }
    
    detail_tests = [
        { 'uid': '1/D/12/001362', 'len': 16 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 43 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 2 } ]
        
class WeymouthScraper(DorsetForYouScraper):

    _authority_name = 'Weymouth'
    _search_fields = { 'ddlAuthority': 'WPBC' }
    
    detail_tests = [
        { 'uid': '11/00688/FUL', 'len': 15 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 38 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 3 } ]

