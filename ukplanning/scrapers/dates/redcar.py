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

# also see Kirklees and Glamorgan

class RedcarScraper(base.DateScraper):

    min_id_goal = 400 # min target for application ids to fetch in one go

    _authority_name = 'Redcar'
    _handler = 'etree'
    _date_from_field = 'ctl00$ContentPlaceHolder1$txtRecFrom'
    _date_to_field = 'ctl00$ContentPlaceHolder1$txtRecTo'
    _search_form = '1'
    _search_url = 'https://planning.redcar-cleveland.gov.uk/%28S%28ne5wxckt3lgrtfwtxqt3skxw%29%29/Plastandard.aspx'
    _detail_page = 'PlaRecord.aspx'
    _scrape_next_submit = '<input class="rgPageNext" name="{{ next_submit }}">'
    _scrape_max_recs = '<div class="rgWrap rgInfoPart"> <strong> {{ max_recs }} </strong> items </div>'
    _scrape_ids = """
    <table class="rgMasterTable"> <thead /> <tfoot /> <tbody> 
    {* <tr>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    </tr> *}
    </tbody> </table>
    """
    _scrape_ids_no_foot = """
    <table class="rgMasterTable"> <thead /> <tbody> 
    {* <tr>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    </tr> *}
    </tbody> </table>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <form id="form1"> {{ block|html }} </form>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <span id="ContentPlaceHolder1_lblTitle"> Planning Application Details for : {{ reference }} </span>
    <textarea id="ContentPlaceHolder1_TabContainer1_tabDetails_txtLocation"> {{ address }} </textarea>
    <textarea id="ContentPlaceHolder1_TabContainer1_tabDetails_txtProposal"> {{ description }} </textarea>
    <input id="ContentPlaceHolder1_TabContainer1_tabOtherDetails_txtRec" value="{{ date_received }}" /> 
    <input id="ContentPlaceHolder1_TabContainer1_tabOtherDetails_txtComplete" value="{{ date_validated }}" />
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<input id="ContentPlaceHolder1_TabContainer1_tabDetails_txtParish" value="{{ parish }}" />',
    '<input id="ContentPlaceHolder1_TabContainer1_tabDetails_txtAppType" value="{{ application_type }}" />',
    '<input id="ContentPlaceHolder1_TabContainer1_tabDetails_txtStatus" value="{{ status }}" />',
    '<input id="ContentPlaceHolder1_TabContainer1_tabDetails_txtAppName" value="{{ applicant_name }}" />',
    '<input id="ContentPlaceHolder1_TabContainer1_tabDetails_txtAgtName" value="{{ agent_name }}" />',
    '<textarea id="ContentPlaceHolder1_TabContainer1_tabDetails_txtAppAddress"> {{ applicant_address }} </textarea>',
    '<textarea id="ContentPlaceHolder1_TabContainer1_tabDetails_txtAgtAddress"> {{ agent_address }} </textarea>',
    '<input id="ContentPlaceHolder1_TabContainer1_tabOtherDetails_txtOffName" value="{{ case_officer }}" />',
    '<input id="ContentPlaceHolder1_TabContainer1_tabOtherDetails_txtExpiry" value="{{ application_expires_date }}" />',
    '<input id="ContentPlaceHolder1_TabContainer1_tabOtherDetails_txtpubconsultstartdate" value="{{ consultation_start_date }}" />',
    '<input id="ContentPlaceHolder1_TabContainer1_tabOtherDetails_txtpubconsultenddate" value="{{ consultation_end_date }}" />',
    '<input id="ContentPlaceHolder1_TabContainer1_tabDecision_txtDecision" value="{{ decision }}" />',
    '<input id="ContentPlaceHolder1_TabContainer1_tabDecision_txtDecisionType" value="{{ decided_by }}" />',
    '<input id="ContentPlaceHolder1_TabContainer1_tabDecision_txtDecDate" value="{{ decision_date }}" />',
    '<input id="ContentPlaceHolder1_TabContainer1_tabDecision_txtAppealStatus" value="{{ appeal_status }}" />',
    '<input id="ContentPlaceHolder1_TabContainer1_tabDecision_txtAppealDecDate" value="{{ appeal_decision_date }}" />',
    ]
    detail_tests = [
        { 'uid': 'R/2011/0554/CL', 'len': 17 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 14 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 3 } ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s" % response.read())
        
        fields = {}
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        
        html = response.read()
        #self.logger.debug("ID batch page html: %s", html)
        try:
            result = scrapemark.scrape(self._scrape_max_recs, html)
            max_recs = int(result['max_recs'])
        except:
            max_recs = 0 # note max recs is in the footer which is omitted if only one page of results
            
        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        while response and page_count < max_pages:
            url = response.geturl()
            #self.logger.debug("Batch html: %s" % html)
            if max_recs == 0: # one page, no footer
                result = scrapemark.scrape(self._scrape_ids_no_foot, html, url)
            else:
                result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                page_count += 1
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            else:
                self.logger.debug("Empty result after %d pages", page_count)
                break
            if max_recs == 0 or len(final_result) >= max_recs: break
            try:
                result = scrapemark.scrape(self._scrape_next_submit, html)
                scrapeutils.setup_form(self.br, self._search_form)
                #self.logger.debug("Next page form: %s", str(self.br.form))
                response = scrapeutils.submit_form(self.br, result['next_submit'])
                html = response.read()
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next form after %d pages", page_count)
                break
        
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
            
        return final_result

    def get_html_from_uid(self, uid): 
        url = urlparse.urljoin(self._search_url, self._detail_page) + '?AppNo=' + urllib.quote_plus(uid)
        return self.get_html_from_url(url) 

        

