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
from datetime import timedelta
import urllib, urlparse

# also see Surrey, Lancashire, North Yorkshire
# no dates in result, so we search on "Complete" date one day at a time and add the dates on each iteration

class NorfolkScraper(base.DateScraper):

    min_id_goal = 150 # min target for application ids to fetch in one go
    
    _authority_name = 'Norfolk'
    _search_url = 'http://eplanning.norfolk.gov.uk/PlanAppSearch.aspx'
    _detail_page = 'PlanAppDisp.aspx'
    _date_from_field = 'ctl00$ContentPlaceHolder1$txtCompleteDateFrom$dateInput'
    _date_to_field = 'ctl00$ContentPlaceHolder1$txtCompleteDateTo$dateInput'
    _scrape_next_submit = '<input class="rgPageNext" name="{{ next_submit }}" />'
    _request_date_format = '%Y-%m-%d-00-00-00'
    _search_form = 'aspnetForm'
    _scrape_max_recs = 'Back to Search Page {{ max_recs }} record(s) found.'
    _date_type = 'date_validated'

    _scrape_ids = """
    <table id="ctl00_ContentPlaceHolder1_gridResults_ctl00"> <tbody>
    {* <tr>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td> 
    <td> {{ [records].site_notice_start_date }} </td> 
    <td> {{ [records].consultation_end_date }} </td> 
    </tr> *}
    </tbody> </table>
    """
    _scrape_data_block = """
    <div id="formContent"> {{ block|html }} </div>
    """
    _scrape_min_data = """
    <input name="ctl00$ContentPlaceHolder1$txtAppNumber" value="{{ reference }}" />
    <textarea name="ctl00$ContentPlaceHolder1$txtLocation"> {{ address }} </textarea>
    <textarea name="ctl00$ContentPlaceHolder1$txtProposal"> {{ description }} </textarea>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<input name="ctl00$ContentPlaceHolder1$txtStatus" value="{{ status }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtDistrict" value="{{ district }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtParish" value="{{ parish }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtElecDiv" value="{{ ward_name }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtEasting" value="{{ easting }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtNorthing" value="{{ northing }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtApplicantsName" value="{{ applicant_name }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtAgentsName" value="{{ agent_name }}" />',
    '<textarea name="ctl00$ContentPlaceHolder1$txtApplicantsAddress"> {{ applicant_address }} </textarea>',
    '<textarea name="ctl00$ContentPlaceHolder1$txtAgentAddress"> {{ agent_address }} </textarea>',
    '<input name="ctl00$ContentPlaceHolder1$txtCommitteDeleagated" value="{{ decided_by }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtCommitteeDate" value="{{ meeting_date }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtDecisionDate" value="{{ decision_date }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtDecision" value="{{ decision }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtAppealDate" value="{{ appeal_date }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtAppealDecision" value="{{ appeal_result }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtPlanningOfficer" value="{{ case_officer }}" />',
    ]
    detail_tests = [
        { 'uid': 'C/7/2011/7006', 'len': 14 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '03/09/2012', 'to': '29/09/2012', 'len': 17 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 } ]

    def get_id_batch (self, date_from, date_to):

        this_dt = date_from
        final_result = []
        
        while this_dt <= date_to:
            
            response = self.br.open(self._search_url)
            #self.logger.debug("Start html: %s", response.read())
    
            fields = {}
            fields[self._date_from_field] = this_dt.strftime(self._request_date_format)
            fields[self._date_to_field] = this_dt.strftime(self._request_date_format)
            scrapeutils.setup_form(self.br, self._search_form, fields)
            #self.logger.debug("ID batch form: %s", str(self.br.form))
            response = scrapeutils.submit_form(self.br)
            
            html = response.read()
            #self.logger.debug("ID batch page html: %s", html)
            try:
                result = scrapemark.scrape(self._scrape_max_recs, html)
                max_recs = int(result['max_recs'])
            except:
                max_recs = 0
            
            interim_result = []
            page_count = 0
            max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
            while response and len(interim_result) < max_recs and page_count < max_pages:
                url = response.geturl()
                #self.logger.debug("ID batch page html: %s", html)
                result = scrapemark.scrape(self._scrape_ids, html, url)
                if result and result.get('records'):
                    page_count += 1
                    for rec in result['records']:
                        rec[self._date_type] = fields[self._date_to_field]
                    self._clean_ids(result['records'])
                    interim_result.extend(result['records'])
                else:
                    self.logger.debug("Empty result after %d pages", page_count)
                    break
                if len(interim_result) >= max_recs: break
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
            
            final_result.extend(interim_result)
            this_dt += timedelta(days=1)
            
        return final_result
        
    def get_html_from_uid(self, uid):
        url = urlparse.urljoin(self._search_url, self._detail_page) + '?AppNo=' + urllib.quote_plus(uid)    
        return self.get_html_from_url(url)
            

