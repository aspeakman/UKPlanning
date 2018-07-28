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

# also see Bournemouth and Wealden

class SouthNorthamptonshireScraper(base.DateScraper):

    min_id_goal = 250
    
    _authority_name = 'SouthNorthamptonshire'
    _search_url = 'http://snc.planning-register.co.uk/planappsrch.aspx?pageprefix=plan'
    _date_from_field = 'ctl00$ctl00$MainContent$MainContent$txtDateReceivedFrom$dateInput'
    _date_to_field = 'ctl00$ctl00$MainContent$MainContent$txtDateReceivedTo$dateInput'
    _ref_field = 'ctl00$ctl00$MainContent$MainContent$txtAppNumber'
    _search_fields = { '__EVENTTARGET': '', '__EVENTARGUMENT': '',  }
    _next_target = 'ctl00$Mainpage$gridMain'
    _request_date_format = '%Y-%m-%d-00-00-00'
    _search_form = 'aspnetForm'
    _search_submit = 'ctl00$ctl00$MainContent$MainContent$btnSearch'
    _scrape_ids = """
    <table id="ctl00_ctl00_MainContent_MainContent_grdResults_ctl00"> <tbody>
    {* <tr> <td> <a href="{{ [records].url|abs }}">
    {{ [records].uid }} </a> </td>
    </tr> *}
    </tbody> </table>
    """
    _scrape_max_recs = '<p> Your search returned the following results (a total of <b> {{ max_recs }} </b>).'
    _scrape_next_submit = '<input class="rgPageNext" name="{{ next_submit }}">'
    _scrape_data_block = """
    <div id="contenttext"> {{ block|html }} </div>
    """
    _scrape_min_data = """
    <input name="ctl00$ctl00$MainContent$MainContent$txtAppNo" value="{{ reference }}" />
    <textarea name="ctl00$ctl00$MainContent$MainContent$txtLocation"> {{ address }} </textarea>
    <textarea name="ctl00$ctl00$MainContent$MainContent$txtProposal"> {{ description }} </textarea>
    <input name="ctl00$ctl00$MainContent$MainContent$txtReceivedDate" value="{{ date_received }}" />
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<input name="ctl00$ctl00$MainContent$MainContent$txtValidDate" value="{{ date_validated }}" />',
    '<input name="ctl00$ctl00$MainContent$MainContent$txtParish" value="{{ parish }}" />',
    '<input name="ctl00$ctl00$MainContent$MainContent$txtEasting" value="{{ easting }}" />',
    '<input name="ctl00$ctl00$MainContent$MainContent$txtNorthing" value="{{ northing }}" />',
    '<input name="ctl00$ctl00$MainContent$MainContent$txtStatus" value="{{ status }}" />',
    '<input name="ctl00$ctl00$MainContent$MainContent$txtDecisionDate" value="{{ decision_date }}" />',
    '<input name="ctl00$ctl00$MainContent$MainContent$txtCommitteeDate" value="{{ meeting_date }}" />',
    '<input name="ctl00$ctl00$MainContent$MainContent$txtExpiryDate" value="{{ application_expires_date }}" />',
    '<input name="ctl00$ctl00$MainContent$MainContent$txtType" value="{{ application_type }}" />',
    '<input name="ctl00$ctl00$MainContent$MainContent$txtCaseOfficer" value="{{ case_officer }}" />',
    '<input name="ctl00$ctl00$MainContent$MainContent$txtAgentName" value="{{ agent_name }}" />',
    '<input name="ctl00$ctl00$MainContent$MainContent$txtAppName" value="{{ applicant_name }}" />',
    '<textarea name="ctl00$ctl00$MainContent$MainContent$txtAgentsAddress"> {{ agent_address }} </textarea>',
    '<textarea name="ctl00$ctl00$MainContent$MainContent$txtApplicantsAddress"> {{ applicant_address }} </textarea>',
    '<input name="ctl00$ctl00$MainContent$MainContent$txtAgentTelephone" value="{{ agent_tel }}" />',
    '<input name="ctl00$ctl00$MainContent$MainContent$txtDecisionLevel" value="{{ decided_by }}" />',
    '<input name="ctl00$ctl00$MainContent$MainContent$txtDecisionDate2" value="{{ decision_date }}" />',
    '<input name="ctl00$ctl00$MainContent$MainContent$txtDecision" value="{{ decision }}" />',
    '<input name="ctl00$ctl00$MainContent$MainContent$txtApplicationCategory" value="{{ development_type }}" />',
    '<input name="ctl00$ctl00$MainContent$MainContent$txtPublicNoticeDate" value="{{ consultation_start_date }}" />',
    '<input name="ctl00$ctl00$MainContent$MainContent$txtPublicNoticeExpiryDate" value="{{ consultation_end_date }}" />',
    '<input name="ctl00$ctl00$MainContent$MainContent$txtNeighbourLetterDate" value="{{ neighbour_consultation_start_date }}" />',
    '<input name="ctl00$ctl00$MainContent$MainContent$txtNeighbourLetterExpiryDate" value="{{ neighbour_consultation_end_date }}" />',
    '<input name="ctl00$ctl00$MainContent$MainContent$txtSiteNoticeDisplayDate" value="{{ site_notice_start_date }}" />',
    '<input name="ctl00$ctl00$MainContent$MainContent$txtSiteNoticeExpiryDate" value="{{ site_notice_end_date }}" />',
    '<input name="ctl00$ctl00$MainContent$MainContent$listAppeals$ctl00$DefTextBox2" value="{{ appeal_type }}" />',
    '<input name="ctl00$ctl00$MainContent$MainContent$listAppeals$ctl00$DefTextBox1" value="{{ appeal_date }}" />',
    '<input name="ctl00$ctl00$MainContent$MainContent$listAppeals$ctl00$TextBox4" value="{{ appeal_result }}" />',
    '<input name="ctl00$ctl00$MainContent$MainContent$listAppeals$ctl00$TextBox5" value="{{ appeal_decision_date }}" />',
    
    ]
    detail_tests = [
        { 'uid': 'S/2011/1043/CAC', 'len': 27 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 21 },
        { 'from': '15/08/2012', 'to': '15/08/2012', 'len': 4 } ]
    
    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        
        fields = {}
        fields.update(self._search_fields)
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._search_submit)
        html = response.read()
        
        try:
            result = scrapemark.scrape(self._scrape_max_recs, html)
            max_recs = int(result['max_recs'])
        except:
            max_recs = 0
        
        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        while html and len(final_result) < max_recs and page_count < max_pages:
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
                result = scrapemark.scrape(self._scrape_next_submit, html, url)
                scrapeutils.setup_form(self.br, self._search_form)
                self.logger.debug("ID next form: %s", str(self.br.form))
                response = scrapeutils.submit_form(self.br, result['next_submit'])
                html = response.read()
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next form after %d pages", page_count)
                break
        
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
        
        return final_result
        
    def get_html_from_uid (self, uid):
        response = self.br.open(self._search_url)
        #self.logger.debug("ID detail start html: %s", response.read())
        fields = {}
        fields.update(self._search_fields)
        fields[self._ref_field] = uid
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("Get UID form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._search_submit)
        html, url = self._get_html(response)
        result = scrapemark.scrape(self._scrape_ids, html, url)
        if result and result.get('records'):
            self._clean_ids(result['records'])
            for rr in result['records']:
                if rr.get('uid', '') == uid and rr.get('url'):
                    return self.get_html_from_url(rr['url'])
        return None, None 
        

