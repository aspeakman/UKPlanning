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
try:
    from ukplanning import scrapeutils
except ImportError:
    import scrapeutils
from .. import base
from datetime import date, timedelta
import urllib, urlparse
import re

# works from the sequence of record numbers 
# date box is not for searching, only limits it to records received since a date - default = 1 year ago

# also see DorsetForYou

class PurbeckScraper(base.ListScraper):

    data_start_target = 24500 # gathering back to this record number (around end of 1999)
    min_id_goal = 200 # min target for application ids to fetch in one go
    current_span = 60 # min number of records to get when gathering current ids
    
    _authority_name = 'Purbeck'
    _uid_num_sequence = True # uid is numeric sequence number not the local authority reference
    _start_point = 42500 # default start if no other indication = see base.py
    _handler = 'etree'
    _search_form = '1'
    _date_field = 'ctl00$MainContent$dpReceivedSince$dateInput'
    _request_date_format = '%Y-%m-%d-00-00-00'
    _ref_field = 'ctl00$MainContent$txtAppNum'
    _search_url = 'https://planningsearch.purbeck-dc.gov.uk/PlanAppSrch.aspx'
    _applic_url = 'https://planningsearch.purbeck-dc.gov.uk/PlanAppDisp.aspx'
    _uid_regex = re.compile(r'recno=(\d+)\s*$')
    _scrape_ids = """
    <div id="news_results_list">
    {* <table> <tr>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].reference }} </a> </td>
    </tr> </table> *}
    </div>
    """
    _next_button = 'ctl00$MainContent$lvResults$pager$ctl02$NextButton'
    _scrape_max_recs = """
    <strong> search returned the following results (a total of {{ max_recs }} ).  </strong>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <form id="form1"> {{ block|html }} </form>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <input id="MainContent_txtApplNum" value="{{ reference }}" />
    <textarea id="MainContent_txtLocation"> {{ address }} </textarea>
    <textarea id="MainContent_txtProposal"> {{ description }} </textarea>
    <input id="MainContent_txtRegDate" value="{{ date_validated }}" />
    <input id="MainContent_txtReceivedDate" value="{{ date_received }}" />
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<input id="MainContent_txtCurrentStatus" value="{{ status }}" />',
    '<input id="MainContent_txtEasting" value="{{ easting }}" />',
    '<input id="MainContent_txtNorthing" value="{{ northing }}" />',
    '<input id="MainContent_txtApplName" value="{{ applicant_name }}" />',
    '<input id="MainContent_txtAgentsName" value="{{ agent_name }}" />',
    '<textarea id="MainContent_txtApplicantsAddr"> {{ applicant_address }} </textarea>',
    '<textarea id="MainContent_txtAgentsAddress"> {{ agent_address }} </textarea>',
    '<input id="MainContent_txtDecisionDueBy" value="{{ target_decision_date }}" />',
    '<input id="MainContent_txtApplType" value="{{ application_type }}" />',
    '<input id="MainContent_txtParish" value="{{ parish }}" />',
    '<input id="MainContent_txtNeighbourLettersSent" value="{{ neighbour_consultation_start_date }}" />',
    '<input id="MainContent_txtNeighbourConsultationCloses" value="{{ neighbour_consultation_end_date }}" />',
    '<input id="MainContent_txtDescisionOnApp" value="{{ decision }}" />',
    '<input id="MainContent_txtDecisionDate" value="{{ decision_date }}" />',
    '<textarea id="MainContent_txtDealtWithBy"> {{ case_officer }} </textarea>',
    '<input id="MainContent_txtPlanningBoardDate" value="{{ meeting_date }}" />',
    ]
    detail_tests = [
        { 'uid': '6/2000/0015', 'len': 19 },
        { 'uid': '24661', 'len': 19 } ] 
    batch_tests = [ 
        { 'from': '25006', 'to': '25036', 'len': 31 }, ]

    def get_id_records (self, request_from, request_to, max_recs):
        if not request_from or not request_to or not max_recs:
            return [], None, None # if any parameter invalid - try again next time
        final_result = []
        from_rec = int(request_from)
        to_rec = int(request_to)
        num_recs = int(max_recs)
        if from_rec < 1:
            if to_rec < 1: # both too small
                return [], None, None
            from_rec = 1
        if to_rec > num_recs:
            if from_rec > num_recs: # both too large
                return [], None, None
            to_rec = num_recs
            
        rfrom = None; rto = None
        for i in range(from_rec, to_rec + 1):
            uid = str(i)
            html, url = self.get_html_from_uid(uid)
            result = scrapemark.scrape(self._scrape_min_data, html)
            if result and result.get('reference'):
                final_result.append( { 'url': url, 'uid': uid } )
                if rfrom is None:
                    rfrom = i
                rto = i
            else:
                self.logger.debug("No valid record for uid %s", uid)
                
        if final_result:
            return final_result, rfrom, rto
        else:
            return [], None, None # list scraper - so empty result is always invalid

    @property
    def max_sequence (self):
        max_recs = None
        response = self.br.open(self._search_url)
        to_date = date.today() - timedelta(days=14)
        fields = { self._ref_field: '', self._date_field: to_date.strftime(self._request_date_format) }
        scrapeutils.setup_form(self.br, self._search_form, fields)
        response = scrapeutils.submit_form(self.br)
        html, url = self._get_html(response)
        result = scrapemark.scrape(self._scrape_ids, html, url)
        if result and result.get('records'):
            self._clean_ids(result['records'])
            num_recs = 0
            for i in result['records']:
                try:
                    num = int(i['uid'])
                    if num > num_recs: 
                        num_recs = num
                except:
                    pass
            self.logger.debug('Number of records %d' % num_recs)
            if num_recs > 0:
                max_recs = num_recs
        return max_recs
        
    # post process a set of uid/url records: gets the uid from the url
    def _clean_record(self, record):
        super(PurbeckScraper, self)._clean_record(record)
        if record.get('url'):
            uid_match = self._uid_regex.search(record['url'])
            if uid_match and uid_match.group(1):
                record['uid'] = uid_match.group(1)

    def get_html_from_uid(self, uid):
        if uid.isdigit():
            url = self._applic_url + '?recno=' + urllib.quote_plus(uid)
            return self.get_html_from_url(url)
        else:
            response = self.br.open(self._search_url)
            fields = { self._ref_field: uid, self._date_field: '' }
            scrapeutils.setup_form(self.br, self._search_form, fields)
            response = scrapeutils.submit_form(self.br)
            html, url = self._get_html(response)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                self._clean_ids(result['records'])
                for r in result['records']:
                    if r.get('reference', '') == uid and r.get('url'):
                        self.logger.debug("Scraped url: %s", r['url'])
                        return self.get_html_from_url(r['url'])
            return None, None
        
