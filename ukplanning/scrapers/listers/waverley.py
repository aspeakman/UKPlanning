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
#from .. import base
from datetime import date
import urllib, urlparse
from annuallist import AnnualListScraper
import re
import mechanize

# works from the sequence of application numbers (in WA/YYYY/NNNN format) - no date or list query

class WaverleyScraper(AnnualListScraper):

    data_start_target = 20030001 # gathering back to this sequence number (in YYYYNNNN format derived from the application number in this format = WA/YYYY/NNNN)
    min_id_goal = 250 # min target for application ids to fetch in one go
    current_span = 60 # min number of records to get when gathering current ids
    
    _disabled = False
    _authority_name = 'Waverley'
    _handler = 'etree' # note even after this html is badly formed
    _applic_url = 'http://planning.waverley.gov.uk/live/wbc/pwl.nsf/(RefNoLU)/%s?OpenDocument'
    _search_url = 'http://planning.waverley.gov.uk/live/wbc/pwl.nsf/webdisplaypubliclist?openform'
    _applic_url2 = 'http://planning.waverley.gov.uk/live/wbc/PWL.nsf/Weekly%%20List%%20New?SearchView&Query=FIELD+ref_no+CONTAINS+%s+OR+FIELD+ref_no+CONTAINS+%s&count=20&start=1'
    _max_url = 'http://planning.waverley.gov.uk/live/wbc/pwl.nsf/webdisplaypubliclist?OpenForm&Seq=1#_RefreshKW_showmeby'
    _search_form = '0'
    _max_index = 3000 # maximum records per year
    _max_fields = { 'showmeby': 'R', '__Click': '$Refresh' }
    _response_date_format = '%d-%b-%y'
    _non_digit = re.compile(r'[^\d]')
    _scrape_ids = """
    <font> This is a list of the 100 most recent applications </font>
    {* <a> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </a>
    *}
    <font> If you wish to see officer reports on applications, </font>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <form action=""> {{ block|html }} </form>
    """
    # the minimum acceptable valid dataset on an application page 
    _scrape_min_data = """
    <tr> Application Record : {{ reference }} </tr>
    <font> Location </font> <font> {{ address }} </font> 
    <font> Proposal </font> <font> {{ description }} </font>
    <font> Received Date </font> <font> {{ date_received }} </font>
    <font> Valid Date </font> <font> {{ date_validated }} </font>  
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<font> Grid Ref </font> <font> {{ easting }} </font> <font> {{ northing }} </font>', 
    '<font> Latest date for comments: </font> <font> {{ comment_date }} </font>',
    """<font> Decision Target </font> 
    <font> Decision </font> <font> {{ decision }} </font>
    <font> Decision Date </font> <font> {{ decision_date }} </font>""",
    '<font> Decision Target </font> <font> {{ target_decision_date }} </font>',
    '<font> Ward </font> <font> {{ ward_name }} </font>',
    '<font> Parish </font> <font> {{ parish }} </font>',
    """<font> Applicant Company </font> 
    <font> Applicant </font> <font> {{ applicant_name }} </font>""",
    '<font> Agent </font> <font> {{ agent_name }} </font>',
    ]
    detail_tests = [
        { 'uid': 'WA/2011/1959', 'len': 15 },
        { 'uid': '20111959', 'len': 15 } ] 
    batch_tests = [ 
        { 'from': '20121506', 'to': '20121516', 'len': 11 },
        { 'from': '20119998', 'to': '20120008', 'len': 8 },
        { 'from': '20122990', 'to': '20123010', 'len': 10 }, ]

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
            uid =  self.get_uid(index, year)
            try:
                html, url = self.get_html_from_uid(uid) 
                result = scrapemark.scrape(self._scrape_min_data, html)
                if result and result.get('reference'):
                    final_result.append( { 'url': url, 'uid': uid } )
                else:
                    return [], None, None # not recognised as valid data - something is wrong - exit
            except (mechanize.HTTPError, mechanize.URLError) as e:
                # note use uid unless it throws a 404 error because uid page does not exist
                self.logger.debug("No valid record for uid %s", uid)      
                
        if not in_current_year or final_result:
            return final_result, rfrom, rto
        else:
            return [], None, None # empty result is invalid if any of the results are in the current year
                
    @property
    def max_sequence (self):
        max_recs = None
        response = self.br.open(self._search_url) 
        scrapeutils.setup_form(self.br, self._search_form, self._max_fields)
        self.logger.debug("Max form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        html = response.read()
        url = response.geturl()
        #self.logger.debug("Start html: %s", html)
        result = scrapemark.scrape(self._scrape_ids, html, url)
        if result and result.get('records'):
            self._clean_ids(result['records'])
            try:
                uid = result['records'][0]['uid']
                uid_num = self._non_digit.sub('', uid)
                max_recs = int(uid_num)
                self.logger.debug("Max recs: %d", max_recs)
            except:
                max_recs = None
        return max_recs
        
    def get_uid(self, index, year):
        # create a uid from year and index integer values
        uid = 'WA/' + str(year) + '/' + str(index).zfill(self._index_digits)
        return uid  
        
    def get_html_from_uid(self, uid):
        if uid.isdigit():
            uid = 'WA' + str(uid)
        else:
            uid = uid.replace('/', '')
        url = self._applic_url % uid
        return self.get_html_from_url(url)
