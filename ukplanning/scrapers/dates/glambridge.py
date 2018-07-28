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

# also see Kirklees and Redcar

class GlamBridgeScraper(base.DateScraper):

    min_id_goal = 400 # min target for application ids to fetch in one go
    
    _scraper_type = 'GlamBridge'
    _date_from_field = 'ctl00$ContentPlaceHolder1$txtRecFrom'
    _date_to_field = 'ctl00$ContentPlaceHolder1$txtRecTo'
    _search_form = 'aspnetForm'
    _submit_control = 'ctl00$ContentPlaceHolder1$Button1'
    _next_fields = { '__EVENTTARGET': 'ctl00$ContentPlaceHolder1$gvPlanning', '__EVENTARGUMENT': 'Page$' }
    _detail_page = 'PlaRecord.aspx'
    _scrape_ids = """
    <table> <tr />
    {* <tr> <td />
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    </tr> *}
    </table>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <div id="content"> {{ block|html }} </div>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <h1> Planning Application Details for : {{ reference }} </h1>
    <textarea id="ctl00_ContentPlaceHolder1_TabContainer1_tabDetails_txtLocation"> {{ address }} </textarea>
    <textarea id="ctl00_ContentPlaceHolder1_TabContainer1_tabDetails_txtProposal"> {{ description }} </textarea>
    <input id="ctl00_ContentPlaceHolder1_TabContainer1_tabOtherDetails_txtRec" value="{{ date_received }}">
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<input id="ctl00_ContentPlaceHolder1_TabContainer1_tabOtherDetails_txtComplete" value="{{ date_validated }}">',
    '<input id="ctl00_ContentPlaceHolder1_TabContainer1_tabDetails_txtEasting" value="{{ easting }}">',
    '<input id="ctl00_ContentPlaceHolder1_TabContainer1_tabDetails_txtNorthing" value="{{ northing }}">',
    '<input id="ctl00_ContentPlaceHolder1_TabContainer1_tabDetails_txtParish" value="{{ parish }}">',
    '<input id="ctl00_ContentPlaceHolder1_TabContainer1_tabDetails_txtAppType" value="{{ application_type }}">',
    '<input id="ctl00_ContentPlaceHolder1_TabContainer1_tabDetails_txtStatus" value="{{ status }}">',
    '<input id="ctl00_ContentPlaceHolder1_TabContainer1_tabDetails_txtAppName" value="{{ applicant_name }}">',
    '<input id="ctl00_ContentPlaceHolder1_TabContainer1_tabDetails_txtAgtName" value="{{ agent_name }}">',
    '<textarea id="ctl00_ContentPlaceHolder1_TabContainer1_tabDetails_txtAppAddress"> {{ applicant_address }} </textarea>',
    '<textarea id="ctl00_ContentPlaceHolder1_TabContainer1_tabDetails_txtAgtAddress"> {{ agent_address }} </textarea>',
    '<input id="ctl00_ContentPlaceHolder1_TabContainer1_tabOtherDetails_txtOffName" value="{{ case_officer }}">',
    '<input id="ctl00_ContentPlaceHolder1_TabContainer1_tabOtherDetails_txtDecisionType" value="{{ decided_by }}">',
    '<input id="ctl00_ContentPlaceHolder1_TabContainer1_tabOtherDetails_txtExpiry" value="{{ application_expires_date }}">',
    '<input id="ctl00_ContentPlaceHolder1_TabContainer1_tabDecision_txtDecision" value="{{ decision }}">',
    '<input id="ctl00_ContentPlaceHolder1_TabContainer1_tabDecision_txtDecDate" value="{{ decision_date }}">',
    ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s" % response.read())
        
        fields = {}
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._submit_control)
        
        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        while response and page_count < max_pages:
            html = response.read()
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
            try:
                fields = {}
                fields.update(self._next_fields)
                fields['__EVENTARGUMENT'] = 'Page$' + str(page_count+1)
                scrapeutils.setup_form(self.br, self._search_form, fields)
                #self.logger.debug("Next page form: %s", str(self.br.form))
                response = scrapeutils.submit_form(self.br)
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next form after %d pages", page_count)
                break
        
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
            
        return final_result

    def get_html_from_uid(self, uid): 
        url = urlparse.urljoin(self._search_url, self._detail_page) + '?AppNo=' + urllib.quote_plus(uid)
        return self.get_html_from_url(url) 

class BridgendScraper(GlamBridgeScraper):

    _authority_name = 'Bridgend'
    _comment = 'was Ocella2 scraper'
    _search_url = 'http://planning.bridgend.gov.uk/'
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <h2> Planning Application Details for : {{ reference }} </h2>
    <textarea id="ctl00_ContentPlaceHolder1_TabContainer1_tabDetails_txtLocation"> {{ address }} </textarea>
    <textarea id="ctl00_ContentPlaceHolder1_TabContainer1_tabDetails_txtProposal"> {{ description }} </textarea>
    <input id="ctl00_ContentPlaceHolder1_TabContainer1_tabOtherDetails_txtRec" value="{{ date_received }}">
    """
    
    detail_tests = [
        { 'uid': 'P/11/629/FUL', 'len': 20 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 55 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 7 } ]

class GlamorganScraper(GlamBridgeScraper):
    
    _authority_name = 'Glamorgan'
    _search_url = 'http://vogonline.planning-register.co.uk/Plastandard.aspx'
    _search_form = 'form1'
    _scrape_min_data = """
    <h1> Planning Application Details for : {{ reference }} </h1>
    <textarea id="ContentPlaceHolder1_TabContainer1_tabDetails_txtLocation"> {{ address }} </textarea>
    <textarea id="ContentPlaceHolder1_TabContainer1_tabDetails_txtProposal"> {{ description }} </textarea>
    <input id="ContentPlaceHolder1_TabContainer1_tabOtherDetails_txtRec" value="{{ date_received }}">
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<input id="ContentPlaceHolder1_TabContainer1_tabOtherDetails_txtComplete" value="{{ date_validated }}">',
    '<input id="ContentPlaceHolder1_TabContainer1_tabDetails_txtEasting" value="{{ easting }}">',
    '<input id="ContentPlaceHolder1_TabContainer1_tabDetails_txtNorthing" value="{{ northing }}">',
    '<input id="ContentPlaceHolder1_TabContainer1_tabDetails_txtParish" value="{{ parish }}">',
    '<input id="ContentPlaceHolder1_TabContainer1_tabDetails_txtAppType" value="{{ application_type }}">',
    '<input id="ContentPlaceHolder1_TabContainer1_tabDetails_txtStatus" value="{{ status }}">',
    '<input id="ContentPlaceHolder1_TabContainer1_tabDetails_txtAppName" value="{{ applicant_name }}">',
    '<input id="ContentPlaceHolder1_TabContainer1_tabDetails_txtAgtName" value="{{ agent_name }}">',
    '<textarea id="ContentPlaceHolder1_TabContainer1_tabDetails_txtAppAddress"> {{ applicant_address }} </textarea>',
    '<textarea id="ContentPlaceHolder1_TabContainer1_tabDetails_txtAgtAddress"> {{ agent_address }} </textarea>',
    '<input id="ContentPlaceHolder1_TabContainer1_tabOtherDetails_txtOffName" value="{{ case_officer }}">',
    '<input id="ContentPlaceHolder1_TabContainer1_tabOtherDetails_txtDecisionType" value="{{ decided_by }}">',
    '<input id="ContentPlaceHolder1_TabContainer1_tabOtherDetails_txtExpiry" value="{{ application_expires_date }}">',
    '<input id="ContentPlaceHolder1_TabContainer1_tabDecision_txtDecision" value="{{ decision }}">',
    '<input id="ContentPlaceHolder1_TabContainer1_tabDecision_txtDecDate" value="{{ decision_date }}">',
    ]
    
    detail_tests = [
        { 'uid': '2011/00820/FUL', 'len': 20 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 20 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 5 } ]

