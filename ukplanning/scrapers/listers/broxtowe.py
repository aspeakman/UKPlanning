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
import urllib, urlparse
import re
try:
    from ukplanning import scrapemark
except ImportError:
    import scrapemark
try:
    from ukplanning import scrapeutils
except ImportError:
    import scrapeutils
#from .. import base
from annuallist import AnnualListScraper
try:
    from ukplanning import myutils
except ImportError:
    import myutils
from datetime import date
import json
import httplib

# works from the sequence of application numbers (in YY/NNNNN format)
# now works via a JSON API 

class BroxtoweScraper(AnnualListScraper):

    min_id_goal = 100 # min target for application ids to fetch in one go
    data_start_target = 200000001
    batch_size = 30 # batch size for each scrape - number of applications requested to produce at least one result each time
    current_span = 30 # min number of records to get when gathering current ids
    
    _disabled = False
    _authority_name = 'Broxtowe'
    _uid_regex = re.compile(r'\d\d/\d\d\d\d\d/\w+')
    _uid2_regex = re.compile(r'\d\d/\d\d\d\d\d/*')
    _max_index = 1000 # maximum records per year
    _index_digits = 5 # digits in sequence for index value
    _start_point = (date.today().year * 100000) + 1 # default start if no other indication = see base.py
    _search_url = 'http://planning.broxtowe.gov.uk/ApplicationSearch'
    _detail_page = 'api/ApplicationDetailApi'
    _find_page = 'api/ApplicationHistorySummary/Data'

    _scrape_invalid_format = '<Error><Message>An error has occurred.</Message></Error>'
    _scrape_ids = """
    "Applications":[
    {*     "AppRefVal":" {{ [records].uid }} "    *}
    ]
    """
    # specifies JSON dict (sub) element encompassing all fields to be gathered
    _scrape_data_block = [ ]
    # specifies XMLA message when JSON API no appropriate data
    _scrape_no_records = '{"RefVal":null,"Address":null,"Applications":[]}'
    
    # In the following keys can be scrapemark markup to extract values within fields
    # e.g. 'Pre {{ value }} Suff' would return { 'value': '2' } from 'Pre 2 Suff'
    # also values can be arrays to get values within dict tree structure
    # eg [ 'a', 'c' ] would return 'val2' from { 'a': { 'b': 'val1', 'c': 'val2' } }
    # eg [ 'a', 2 ]  would return 'val2' from { 'a': [ 'val0', 'val1', 'val2' ] }
    
    _min_fields = [ 'address', 'description', 'date_received' ] # min fields list used in testing only
    # the minimum acceptable valid dataset in the data block
    _scrape_min_data = { 
        'address': 'ApplicationSiteAddress', 
        'description': 'ApplicationProposal',
        'date_received': 'ApplicationProgressDateReceived',
    }
    # other optional parameters that can appear in a data block
    _scrape_optional_data = {
        'date_validated': 'ApplicationProgressDateValidated',
        'status': 'ApplicationProgressStatus',
        'case_officer': 'ApplicationProgressOfficerDealing',
        'applicant_name': 'ApplicationApplicant',
        'agent_name': 'AgentName',
        'agent_address': 'AgentAddress',
        'agent_tel': 'AgentTelephoneNumber',
        'decision_date': 'ApplicationProgressDecisionDate',
        'consultation_start_date': 'ConsultationPeriodConsulteesStartDate',
        'consultation_end_date': 'ConsultationPeriodConsulteesEndDate',
        'neighbour_consultation_start_date': 'ConsultationPeriodNeighboursStartDate',
        'neighbour_consultation_end_date': 'ConsultationPeriodNeighboursEndDate',
        'last_advertised_date': 'ConsultationPeriodPressAdvertStartDate',
        'latest_advertisement_expiry_date': 'ConsultationPeriodPressAdvertEndDate',
        'appeal_status': 'AppealDetailStatus',
        'appeal_date': 'AppealDetailDateLodged',
        'appeal_decision_date': 'AppealDetailDecisionDate',
        'comment_url': 'CommentUrl',
    }
    detail_tests = [
        { 'uid': '12/00445/FUL', 'len': 16 },
        { 'uid': '12/00445', 'len': 16 },
        { 'uid': '201200445', 'len': 16 } ]
    batch_tests = [ 
        { 'from': '201200506', 'to': '201200516', 'len': 11 },
        { 'from': '201199998', 'to': '201200008', 'len': 7 },
        { 'from': '201200990', 'to': '201201010', 'len': 8 }, ]
        
    def get_id_records (self, request_from, request_to, max_recs):
        if not request_from or not request_to or not max_recs:
            return [], None, None # if any parameter invalid - try again next time
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
        
        final_result = []
        rfrom = None; rto = None
        n = to_rec - from_rec + 1
        if self.over_sequence(to_rec): # at max sequence and gathering forward
            ii, yy, from_rec = self.split_sequence(from_rec, True)
        else: 
            ii, yy, from_rec = self.split_sequence(from_rec, False)
        to_rec = from_rec + n - 1
        in_current_year = False
        this_year = date.today().year
        for i in range(from_rec, to_rec + 1):
            index, year, new_seq = self.split_sequence(i)
            if year == this_year and index > 0:
                in_current_year = True
            if rfrom is None:
                rfrom = i
            rto = new_seq
            testuid =  self.get_uid(index, year)
            #print testuid
            try:
                html, url = self.get_html_from_uid(testuid)
            except httplib.BadStatusLine as e: # catches random mechanize error - BadStatusLine
                html = None; url = None
            if html and html == self._scrape_no_records:
                self.logger.debug("No valid record for uid %s" % testuid)
                continue # skip on to test next record
            if not html:
                self.logger.debug("No json from uid %s" % testuid)
                return [], None, None # no html to work on - something is wrong - exit
            json_dict = json.loads(html)
            result = self._scrape_lookup(json_dict, self._scrape_data_block)
            uid_index = url.find('?RefVal=')
            if result and result.get('ApplicationSiteAddress') and uid_index > 7:
                uid = urllib.unquote_plus(url[uid_index+8:])
                final_result.append( { 'url': url, 'uid': uid } )
            else:
                self.logger.error("Unrecognised record for uid %s : %s" % (testuid, html))
                return [], None, None # not recognised as bad data - something is wrong - exit
            
        #print final_result
        if not in_current_year or final_result:
            return final_result, rfrom, rto
        else:
            return [], None, None # empty result is invalid if any of the results are in the current year
            
    def get_uid(self, index, year):
        # create a uid from year and index integer values
        uid = str(year)[2:4] + '/' + str(index).zfill(self._index_digits)
        return uid 
        
    def get_html_from_uid(self, uid):
        uid = myutils.GAPS_REGEX.sub('', uid) # NB removes spaces
        uid_match = self._uid_regex.search(uid)
        if uid_match:
            url = urlparse.urljoin(self._search_url, self._detail_page) + '?RefVal=' + urllib.quote_plus(uid)
            return self.get_html_from_url(url) 
        refid = None
        if uid.isdigit() and len(uid) == 9: 
            year = str(uid)[2:4]
            refno = str(uid)[4:9]
            refid = year + '/' + refno + '/'
        else:
            uid_match2 = self._uid2_regex.search(uid)
            if uid_match2:
                refid = uid
                if not refid.endswith('/'):
                    refid = refid + '/'
        if refid:
            url = urlparse.urljoin(self._search_url, self._find_page) + '?RefVal=' + refid
            response = self.br.open(url)
            html, url = self._get_html(response)
            self.logger.debug("Ref list html: %s", html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                self._clean_ids(result['records'])
                for r in result['records']:
                    if r.get('uid', '').startswith(refid):
                        url = urlparse.urljoin(self._search_url, self._detail_page) + '?RefVal=' + urllib.quote_plus(r['uid'])
                        self.logger.debug("Scraped url: %s", url)
                        return self.get_html_from_url(url)
            return html, url
        url = urlparse.urljoin(self._search_url, self._detail_page) + '?RefVal=' + urllib.quote_plus(uid)
        return self.get_html_from_url(url) 
               
    def _get_details(self, html, this_url):
        """ Scrapes detailed information for one record given html and url 
        - this is an optional hook to allow e.g. data from multiple linked pages to be merged
        OR to interpolate a JSON decoder """
        #self.logger.debug("Html to scrape: %s" % html)
        if html == self._scrape_invalid_format:
            return { 'scrape_error': self.errors[self.INVALID_FORMAT] } 
        json_dict = json.loads(html)
        return self._get_detail_json(json_dict, this_url)

    
