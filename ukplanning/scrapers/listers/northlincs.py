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
import re
from datetime import date, datetime, timedelta
import json
from annuallist import AnnualListScraper
import httplib

# Date search form was removed in April 2016
# so this now works via a JSON API 
# and from the sequence of application numbers (in PA/YYYY/NNNN or NNN or NN format)
# note not all start with PA/ some start with WD/ or MIN/

class NorthLincsScraper(AnnualListScraper): # note annual list scraper is disabled by default
    
    min_id_goal = 150
    batch_size = 30 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 30 # start this number of days ago when gathering current ids

    _disabled = False
    _authority_name = 'NorthLincs'
    _comment = 'Was date scraper up to April 2016'
    _max_index = 2300 # maximum records per year
    _headers = {
    'User-Agent': 'Mozilla/5.0 (Windows; U; MSIE 7.0; Windows NT 6.0; en-US)',
    'Accept-Charset': 'UTF-8,*',
    'Accept': 'text/html',
    'Accept-Language': 'en-gb,en',
    }
    _index_digits = 4
    _ref_field = 'refNo'
    _search_fields = { 'view': 'compactsearch' }
    _search_form = '0'
    _search_url = 'http://www.planning.northlincs.gov.uk/plan/search/'
    _applic_url = 'http://www.planning.northlincs.gov.uk/api/Cached/PlanningWeb'
    
    _scrape_ids = """
    <table class="tbresults">
    {* 
    <tr onclick="document.location = '{{ [records].url|abs }}';">
    <td> <strong> {{ [records].uid }} </strong> </td> </tr>
     *}
    </table>
    """
    _scrape_no_records = '{"Count":0,"msg":"No Records"}'
        
    # specifies JSON dict (sub) element encompassing all fields to be gathered
    _scrape_data_block = [ "Results", 0 ]
    # specifies JSON dict (sub) element whose existence indicates JSON return 
    # has known format but no appropriate data
    _scrape_invalid_format = [ 'msg' ]
    
    # In the following keys can be scrapemark markup to extract values within fields
    # e.g. 'Pre {{ value }} Suff' would return { 'value': '2' } from 'Pre 2 Suff'
    # also values can be arrays to get values within dict tree structure
    # eg [ 'a', 'c' ] would return 'val2' from { 'a': { 'b': 'val1', 'c': 'val2' } }
    # eg [ 'a', 2 ]  would return 'val2' from { 'a': [ 'val0', 'val1', 'val2' ] }
    
    # the minimum acceptable valid dataset in the data block
    _scrape_min_data = { 
        'reference': 'Name',
        'date_received': 'ReceivedDate__c',
        'address': 'SiteAddressAsText_TEMP__c', # NL_Print_Address__c ?
        'description': 'Proposal__c'
    }
    # other optional parameters that can appear in a data block
    _scrape_optional_data = {
        'date_validated': 'Validation_Date__c',
        'status': 'Status__c',
        'ward_name': 'Wards__c',
        'comment_date': 'CommentsUntil__c',
        'meeting_date': 'DateOfCommittee__c',
        'decision': 'Last_Decision__c',
        'decided_by': 'DeterminationLevel__c',
        'decision_issued_date': 'Decision_Notice_Sent_Date__c',
        'case_officer': 'NL_Officer_Name__c',
        'applicant_name': 'NL_Applicant_Short_Details__c',
        'applicant_address': 'NL_Applicant_Details__c',
        ', {{ applicant_address }}': 'NL_Applicant_Details__c',
        'parish': 'Parishes__c',
        'easting': 'x',
        'northing': 'y',
        '{{ agent_name }} , {{ agent_address }}': 'NL_Agent_Details__c',
        'decision_date': 'Last_Decision_Date__c',
        'target_decision_date': 'Earliest_Decision_Date__c',
        'uprn': 'UPRN__c',
        'application_type': 'Application_PS_Stats_PS_Type__c'
    }
    detail_tests = [
        { 'uid': 'PA/2005/0887', 'len': 22 },
        { 'uid': 'PA/2012/0584', 'len': 22 },
        { 'uid': '/2012/0584', 'len': 22 }, ]
        #{ 'uid': '20120584', 'len': 22 } ]
    batch_tests = [ 
        { 'from': '20120506', 'to': '20120516', 'len': 10 },
        { 'from': '20169998', 'to': '20170018', 'len': 6 },
        { 'from': '20162281', 'to': '20162310', 'len': 1 }, ]
        #{ 'from': '20119998', 'to': '20120008', 'len': 5 },
        #{ 'from': '20122490', 'to': '20122510', 'len': 8 }, ]
        
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
            try:
                html, url = self.get_html_from_uid(testuid)
            except httplib.BadStatusLine as e: # catches random mechanize error - BadStatusLine
                html = None; url = None
            if html and html == self._scrape_no_records:
                if index < 1000: # try alternative form of uid if suffix is <= 3 digits
                    testuid =  self.get_altuid(index, year) 
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
            if result and result.get('Name'):
                uid = result['Name']
                url = self._applic_url + '?ReqType=F&Refno=' + urllib.quote_plus(uid)
                final_result.append( { 'url': url, 'uid': uid } )
            else:
                result = self._scrape_lookup(json_dict, self._scrape_invalid_format)
                if result:
                    self.logger.debug("No valid record for uid %s after lookup" % testuid)
                    # skip on to test next record
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
        uid = '/' + str(year) + '/' + str(index).zfill(self._index_digits)
        return uid 
        
    def get_altuid(self, index, year):
        # create a uid from year and index integer values
        # some uids have no leading zeroes 
        uid = '/' + str(year) + '/' + str(index)
        return uid 
        
    def get_html_from_uid(self, uid):
        #if uid.isdigit(): 
        #    uid = '/' + str(uid)[0:4] + '/' + str(uid)[4:8]
        if uid.startswith('/'):
            response = self.br.open(self._search_url)
            #self.logger.debug("Start html: %s" % response.read())
            fields = {}
            fields.update(self._search_fields)
            fields[self._ref_field] = uid
            scrapeutils.setup_form(self.br, self._search_form, fields)
            #self.logger.debug("ID ref form: %s" % str(self.br.form))
            response = scrapeutils.submit_form(self.br)
            html, url = self._get_html(response)
            #self.logger.debug("Uid html: %s" % html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                #print result['records']
                self._clean_ids(result['records'])
                for r in result['records']:
                    if r.get('uid', '').endswith(uid) and r.get('url'):
                        self.logger.debug("Scraped url: %s" % r['url'])
                        return self.get_html_from_url(r['url'])
        url = self._applic_url + '?ReqType=F&Refno=' + urllib.quote_plus(uid)
        return self.get_html_from_url(url)
        
    def get_html_from_url(self, url):
        if 'format=html' in url:
            url = url.replace('format=html', 'format=json')
        elif 'format=json' not in url:
            url = url + '&format=json'
        return super(NorthLincsScraper, self).get_html_from_url(url)

    def _get_details(self, html, this_url):
        """ Scrapes detailed information for one record given html and url 
        - this is an optional hook to allow e.g. data from multiple linked pages to be merged
        OR to interpolate a JSON decoder """
        #self.logger.debug("Html to scrape: %s" % html)
        json_dict = json.loads(html)
        return self._get_detail_json(json_dict, this_url)
        
        


