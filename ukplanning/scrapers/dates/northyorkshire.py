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

# also see Surrey, Lancashire, Norfolk

class NorthYorkshireScraper(base.DateScraper):

    data_start_target = '2000-02-01'
    batch_size = 32 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 32 # start this number of days ago when gathering current ids
    min_id_goal = 200 # min target for application ids to fetch in one go
    
    _authority_name = 'NorthYorkshire'
    _search_url = 'https://onlineplanningregister.northyorks.gov.uk/register/PlanAppSrch.aspx'
    _date_from_field = 'ctl00$MainContent$txtValidatedDateFrom$dateInput'
    _date_to_field = 'ctl00$MainContent$txtValidatedDateTo$dateInput'
    _scrape_next_submit = '<input class="rdpPageNext" name="{{ next_submit }}" />'
    _ref_field = 'ctl00$MainContent$txtApplNum'
    _request_date_format = '%Y-%m-%d-00-00-00'
    _search_form = '0'
    _scrape_max_recs = '<h2> Search returned the following results (a total of {{ max_recs }} ). </h2>'
    _scrape_ids = """
    <div id="news_results_list">
    {* <div>
    <td> Application Number: <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    </div> *}
    </div>
    """
    _scrape_data_block = """
    <body> {{ block|html }} </body>
    """
    _scrape_min_data = """
    <input name="ctl00$MainContent$txtApplNum" value="{{ reference }}" />
    <textarea name="ctl00$MainContent$txtLocation"> {{ address }} </textarea>
    <textarea name="ctl00$MainContent$txtProposal"> {{ description }} </textarea>
    <input name="ctl00$MainContent$txtReceivedDate" value="{{ date_received }}" />
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<input name="ctl00$MainContent$txtCurrentStatus" value="{{ status }}" />',
    '<input name="ctl00$MainContent$txtDistrict" value="{{ district }}" />',
    '<input name="ctl00$MainContent$txtParish" value="{{ parish }}" />',
    '<input name="ctl00$MainContent$txtElecDiv" value="{{ ward_name }}" />',
    '<input name="ctl00$MainContent$txtEasting" value="{{ easting }}" />',
    '<input name="ctl00$MainContent$txtNorthing" value="{{ northing }}" />',
    '<input name="ctl00$MainContent$txtApplName" value="{{ applicant_name }}" />',
    '<input name="ctl00$MainContent$txtAgentsName" value="{{ agent_name }}" />',
    '<textarea name="ctl00$MainContent$txtApplicantsAddr"> {{ applicant_address }} </textarea>',
    '<textarea name="ctl00$MainContent$txtAgentsAddress"> {{ agent_address }} </textarea>',
    '<input name="ctl00$MainContent$txtSiteNoticeDate" value="{{ site_notice_start_date }}" />',
    '<input name="ctl00$MainContent$txtTargetDecisionDate" value="{{ target_decision_date }}" />',
    '<input name="ctl00$MainContent$txtPressNoticeDate" value="{{ consultation_start_date }}" />',
    '<a id="MainContent_hypComment" href="{{ comment_url|abs }}" />',
    '<input name="ctl00$MainContent$txtDelegatedTo" value="{{ decided_by }}" />',
    '<input name="ctl00$MainContent$txtCommitteeDate" value="{{ meeting_date }}" />',
    '<input name="ctl00$MainContent$txtDecisionDate" value="{{ decision_date }}" />',
    '<input name="ctl00$MainContent$txtDecision" value="{{ decision }}" />',
    '<input name="ctl00$MainContent$txtAppealDate" value="{{ appeal_date }}" />',
    '<input name="ctl00$MainContent$txtAppealDecision" value="{{ appeal_result }}" />',
    '<textarea name="ctl00$MainContent$txtPlanningOfficer"> {{ case_officer }}" </textarea>',
    ]
    detail_tests = [
        { 'uid': 'NY/2011/0305/A30', 'len': 20 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '07/03/2001', 'to': '02/05/2001', 'len': 5 }, 
        { 'from': '03/09/2012', 'to': '10/10/2012', 'len': 16 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 1 } ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s", response.read())

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
                result = scrapemark.scrape(self._scrape_next_submit, html)
                next_submit = result['next_submit']
                scrapeutils.setup_form(self.br, self._search_form)
                self.logger.debug("ID next form: %s", str(self.br.form))
                response = scrapeutils.submit_form(self.br, next_submit)
                html = response.read()
            except: # failure to find next page link at end of page sequence here
                self.logger.debug("No next form link after %d pages", page_count)
                break
                
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
               
        return final_result
        
    def get_html_from_uid (self, uid):
        response = self.br.open(self._search_url)
        #self.logger.debug("ID detail start html: %s", response.read())
        fields = {  self._ref_field: uid }
        scrapeutils.setup_form(self.br, self._search_form, fields)
        response = scrapeutils.submit_form(self.br)
        html, url = self._get_html(response)
        result = scrapemark.scrape(self._scrape_ids, html, url)
        if result and result.get('records'):
            self._clean_ids(result['records'])
            for r in result['records']:
                if r.get('uid', '') == uid and r.get('url'):
                    self.logger.debug("Scraped url: %s", r['url'])
                    return self.get_html_from_url(r['url'])
        return None, None
            

