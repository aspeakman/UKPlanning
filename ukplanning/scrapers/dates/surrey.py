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
import re
import urllib

# also see North Yorkshire, Lancashire, Norfolk

class SurreyScraper(base.DateScraper):

    data_start_target = '2004-08-01'
    batch_size = 40 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 40 # start this number of days ago when gathering current ids
    min_id_goal = 300 # min target for application ids to fetch in one go
    
    _authority_name = 'Surrey'
    _search_url = 'http://planning.surreycc.gov.uk/planappsearch.aspx'
    _applic_url = 'http://planning.surreycc.gov.uk/planappdisp.aspx?AppNo=SCC%20Ref%20'
    _date_from_field = 'ctl00$ContentPlaceHolder1$txtAppValFrom'
    _date_to_field = 'ctl00$ContentPlaceHolder1$txtAppValTo'
    _search_form = '1'
    _scrape_ids = """
    <table id="ContentPlaceHolder1_grdResults"> <tr />
    {* <tr>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    </tr> <tr> <td colspan="10" /> </tr> *}
    </table>
    """
    _next_fields = { '__EVENTARGUMENT': '', 
        '__EVENTTARGET': 'ctl00$ContentPlaceHolder1$grdResults$ctl13$ctl04', 
        'ctl00$ContentPlaceHolder1$btnNewSearch': None }
    _uid_field = 'ctl00$ContentPlaceHolder1$txtCountyRef'
    _ref_field = 'ctl00$ContentPlaceHolder1$txtAppNum'
    _uid_match = re.compile(r'^[0-9/]+$')
    _scrape_max_recs = '<p> Your search has returned {{ max_recs }} application </p>'
    
    _scrape_data_block = """
    <form id="form1"> {{ block|html }} </form>
    """
    _scrape_min_data = """
    <textarea name="ctl00$ContentPlaceHolder1$txtLocation"> {{ address }} </textarea>
    <textarea name="ctl00$ContentPlaceHolder1$txtProposal"> {{ description }} </textarea>
    <input name="ctl00$ContentPlaceHolder1$txtReceivedDate" value="{{ date_received }}" />
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<input name="ctl00$ContentPlaceHolder1$txtDistrictAppNums" value=" {{ reference }}" />',
    '<textarea name="ctl00$ContentPlaceHolder1$txtDistrictAppNums"> {{ reference }} </textarea>',
    '<input name="ctl00$ContentPlaceHolder1$txtValidDate" value="{{ date_validated }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtStatus" value="{{ status }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtDistrict" value="{{ district }}" />',
    '<textarea name="ctl00$ContentPlaceHolder1$txtDistrict"> {{ district }} </textarea>',
    '<input name="ctl00$ContentPlaceHolder1$txtParish" value="{{ parish }}" />',
    '<textarea name="ctl00$ContentPlaceHolder1$txtParish"> {{ parish }} </textarea>',
    '<input name="ctl00$ContentPlaceHolder1$txtWard" value="{{ ward_name }}" />',
    '<textarea name="ctl00$ContentPlaceHolder1$txtWard"> {{ ward_name }} </textarea>',
    '<input name="ctl00$ContentPlaceHolder1$txtEasting" value="{{ easting }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtNorthing" value="{{ northing }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtAppName" value="{{ applicant_name }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtAgtName" value="{{ agent_name }}" />',
    '<textarea name="ctl00$ContentPlaceHolder1$txtAppAddress"> {{ applicant_address }} </textarea>',
    '<textarea name="ctl00$ContentPlaceHolder1$txtAgtAddress"> {{ agent_address }} </textarea>',
    '<input name="ctl00$ContentPlaceHolder1$tbDeterminedBy" value="{{ decided_by }}" />',
    '<input name="ctl00$ContentPlaceHolder1$tbEstimatedDateToCommittee" value="{{ meeting_date }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtCommitteeDate" value="{{ meeting_date }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtNoticeDate" value="{{ decision_issued_date }}" />',
    '<input name="ctl00$ContentPlaceHolder1$txtDecision" value="{{ decision }}" />',
    '<input name="ctl00$ContentPlaceHolder1$tbAppealReceivedDate" value="{{ appeal_date }}" />',
    '<input name="ctl00$ContentPlaceHolder1$tbAppealMethod" value="{{ appeal_result }}" />', # no proper appeal result field?
    '<input name="ctl00$ContentPlaceHolder1$txtCaseOfficer" value="{{ case_officer }}" />',
    '<input name="ctl00$ContentPlaceHolder1$tbNeighbourLetterDate" value="{{ consultation_start_date }}" />',
    '<input name="ctl00$ContentPlaceHolder1$tbSiteNoticeExpiry" value="{{ consultation_end_date }}" />',
    '<input name="ctl00$ContentPlaceHolder1$tbHearingEnquiryDate" value="{{ appeal_decision_date }}" />',
    ]
    detail_tests = [
        { 'uid': '2012/0107', 'len': 22 }, 
        { 'uid': 'SP12/00828', 'len': 22 },
        { 'uid': '2013/0041', 'len': 22 },]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '03/09/2012', 'to': '29/09/2012', 'len': 14 }, 
        { 'from': '15/08/2012', 'to': '15/08/2012', 'len': 1 } ]

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
                fields = { }
                fields.update(self._next_fields)
                scrapeutils.setup_form(self.br, self._search_form, fields)
                self.logger.debug("ID next form: %s", str(self.br.form))
                response = scrapeutils.submit_form(self.br)
                html = response.read()
            except: # failure to find next page link at end of page sequence here
                self.logger.debug("No next form link after %d pages", page_count)
                break
                
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
               
        return final_result
        
    # post process a set of uid/url records: note 'SCC Ref ' prefix with spaces in it
    def _clean_record(self, record):
        if record.get('url'): # note significant spaces in query part of URL
            record['url'] = record['url'].strip().replace(' ', '%20')
        super(SurreyScraper, self)._clean_record(record)
        if record.get('uid') and record['uid'].startswith('SCCRef'):
            record['uid'] = record['uid'].replace('SCCRef', '')

    def get_html_from_uid (self, uid):
        if self._uid_match.match(uid): # all numbers or /
            #fields = {  self._uid_field: uid }
            url = self._applic_url + urllib.quote_plus(uid)
            return self.get_html_from_url(url)
        else:
            fields = {  self._ref_field: uid }
        response = self.br.open(self._search_url)
        #self.logger.debug("ID detail start html: %s", response.read())
        scrapeutils.setup_form(self.br, self._search_form, fields)
        response = scrapeutils.submit_form(self.br)
        html, url = self._get_html(response)
        result = scrapemark.scrape(self._scrape_ids, html, url)
        if result and result.get('records'):
            self._clean_ids(result['records']) 
            if len(result['records']) == 1 and result['records'][0].get('url'):
                url = result['records'][0]['url']
                self.logger.debug("Scraped url: %s", url)
                return self.get_html_from_url(url)
            else:
                for r in result['records']:
                    if r.get('uid', '') == uid and r.get('url'):
                        url = r['url']
                        self.logger.debug("Scraped url: %s", url)
                        return self.get_html_from_url(url)
        return None, None
            

