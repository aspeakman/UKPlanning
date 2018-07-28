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

# also see South Northamptonshire and Wealden

class BournemouthScraper(base.DateScraper):

    min_id_goal = 250
    
    _authority_name = 'Bournemouth'
    _search_url = 'http://planning.bournemouth.gov.uk/RealTimeRegister/planappsrch.aspx'
    _date_from_field = 'ctl00$MainContent$txtDateReceivedFrom'
    _date_to_field = 'ctl00$MainContent$txtDateReceivedTo'
    _search_submit = 'ctl00$MainContent$btnSearch'
    _search_form = '0'
    _scrape_max_recs = '<div> Your search returned the following results (a total of <b> {{ max_recs }} </b> </div>'
    _scrape_next_submit = '<input type="submit" name="{{ next_submit }}" title="Next Page" />'
    _ref_field = 'ctl00$MainContent$txtAppNumber'
    _scrape_ids_pager = """
    <table id="ctl00_MainContent_grdResults_ctl00"> <tfoot /> <tbody>
    {* <tr> <td class="rgSorted" /> <td> <a href="{{ [records].url|abs }}">
    {{ [records].uid }} </a> </td>  </tr> *}
    </tbody> </table>
    """
    _scrape_ids_no_pager = """
    <table id="ctl00_MainContent_grdResults_ctl00"> <tbody>
    {* <tr> <td class="rgSorted" /> <td> <a href="{{ [records].url|abs }}">
    {{ [records].uid }} </a> </td>  </tr> *}
    </tbody> </table>
    """

    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <div id="contenttext"> {{ block|html }} </div>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <input name="ctl00$MainContent$txtAppNo" value="{{ reference }}" />
    <textarea name="ctl00$MainContent$txtProposal"> {{ description }} </textarea>
    <input name="ctl00$MainContent$txtReceivedDate" value="{{ date_received }}" />
    <textarea name="ctl00$MainContent$txtLocation"> {{ address }} </textarea>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<input value="{{ date_validated }}" name="ctl00$MainContent$txtValidDate" />',
    '<input value="{{ application_type }}" name="ctl00$MainContent$txtType" />',
    '<input value="{{ case_officer }}" name="ctl00$MainContent$txtCaseOfficer" />',
    '<input value="{{ decided_by }}" name="ctl00$MainContent$txtCommitteeDelegated" />',
    '<input value="{{ meeting_date }}" name="ctl00$MainContent$txtCommitteeDelegatedDate" />',
    '<input value="{{ latest_advertisement_expiry_date }}" name="ctl00$MainContent$txtAdvertExpiry" />',
    '<input value="{{ neighbour_consultation_end_date }}" name="ctl00$MainContent$txtNeighbourExpiry" />',
    '<input value="{{ site_notice_end_date }}" name="ctl00$MainContent$txtSiteNoticeExpiry" />',
    '<input value="{{ decision_issued_date }}" name="ctl00$MainContent$txtIssueDate" />',
    '<input value="{{ decision }}" name="ctl00$MainContent$txtDecision" />',
    '<input value="{{ decision_date }}" name="ctl00$MainContent$txtDecisionDate" />',
    '<input value="{{ ward_name }}" name="ctl00$MainContent$txtWard" />',
    '<input value="{{ parish }}" name="ctl00$MainContent$txtParish" />',
    '<input value="{{ uprn }}" name="ctl00$MainContent$txtUprn" />',
    '<input value="{{ easting }}" name="ctl00$MainContent$txtEasting" />',
    '<input value="{{ northing }}" name="ctl00$MainContent$txtNorthing" />',
    '<td id="MainContent_tdCommentsWelcomeBy"> Comments Welcome By {{ consultation_end_date }} </td>',
    '<td id="MainContent_tdApplicationStatus"> {{ status }} </td>',
    '<input value="{{ appeal_type }}" name="ctl00$MainContent$listAppeals$ctl00$txtAppealMethod" />',
    '<input value="{{ appeal_date }}" name="ctl00$MainContent$listAppeals$ctl00$txtAppealStartDate" />',
    '<input value="{{ appeal_result }}" name="ctl00$MainContent$listAppeals$ctl00$TextBox4" />',
    '<input value="{{ appeal_decision_date }}" name="ctl00$MainContent$listAppeals$ctl00$TextBox5" />',
    ]
    detail_tests = [
        { 'uid': '7-2012-24945', 'len': 18 },
        { 'uid': '7-2008-2117-H', 'len': 19 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 42 },
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 4 } ]
    
    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        
        fields = {}
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._search_submit)
        html = response.read()
        #self.logger.debug("Batch html: %s" % html)
            
        try:
            result = scrapemark.scrape(self._scrape_max_recs, html)
            max_recs = int(result['max_recs'])
        except:
            max_recs = 0
        
        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        while html and len(final_result) < max_recs and page_count < max_pages:
            url = response.geturl()
            result = scrapemark.scrape(self._scrape_ids_pager, html, url)
            if not result or not result.get('records'):
                result = scrapemark.scrape(self._scrape_ids_no_pager, html, url)
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
        fields = { self._ref_field: uid }
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("Get UID form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._search_submit)
        html, url = self._get_html(response)
        result = scrapemark.scrape(self._scrape_ids_no_pager, html, url)
        if result and result.get('records'):
            self._clean_ids(result['records'])
            for rr in result['records']:
                if rr.get('uid', '') == uid and rr.get('url'):
                    return self.get_html_from_url(rr['url'])
        return None, None 
        

