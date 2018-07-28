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
from datetime import date
import urllib, urlparse
import re

# active Ashford scraper is this ListScraper version
# date query results filled out using JQuery/AJAX - not accessible?
# so works from the sequence of systemkey record numbers 

# also see Ribble Valley, Rossendale, Purbeck, Isle of Wight

class AshfordScraper(base.ListScraper):

    data_start_target = 72150 # gathering back to this record number
    min_id_goal = 200 # min target for application ids to fetch in one go
    current_span = 50 # min number of records to get when gathering current ids
    batch_size = 100 # batch size for each scrape - number of applications requested to produce at least one result each time  
    
    _authority_name = 'Ashford'
    _uid_num_sequence = True # uid is numeric sequence number not the local authority reference
    _start_point = 99798 # default start if no other indication = see base.py
    _handler = 'etree'
    _search_url= 'http://planning.ashford.gov.uk/Planning/Default.aspx?new=true'
    _applic_url = 'http://planning.ashford.gov.uk/Planning/Details.aspx'
    _uid_regex = re.compile(r'systemkey=(\d+)\s*$')
    _cookies = [ { 'name': 'ABCPLANNINGTERMS', 
        'value': '22 Feb 2027 08:21:18 AM', 
        'domain': 'planning.ashford.gov.uk', 'path': '/' } ]
    _scrape_ids = """
    <div id="sideMenu"> <div> Most Popular </div> <ul>
    {* <li> <a href="{{ [records].url|abs }}"> {{ [records].reference }} </a> </li> *}
    </ul> </div>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <div id="contents"> {{ block|html }} </div>
    """
    # the minimum acceptable valid dataset on an application page
    # note overwrites uid to correct value
    _scrape_min_data = """
    <th> Application Ref </th> <td> {{ reference }} </td>
    <th> Site Address </th> <td> {{ address }} </td>
    <th> Description </th> <td> {{ description }} </td>
    <th> Date Received </th> <td> {{ date_received }} </td>
    <th> Date Registered </th> <td> {{ date_validated }} </td>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<th> Application Type </th> <td> {{ application_type }} </td>',
    '<th> Status </th> <td> {{ status }} </td>',
    '<th> Council Decision </th> <td> {{ decision }} </td>',
    '<th> Ward </th> <td> {{ ward_name }} </td>',
    '<th> Parish </th> <td> {{ parish }} </td>',
    '<th> Officer Name </th> <td> {{ case_officer }} </td>',
    '<th> Applicant </th> <td> {{ applicant_address }} </td>',
    '<th> Agent </th> <td> {{ agent_address }} </td>',
    '<th> Grid Reference </th> <td> {{ easting }} / {{ northing }} </td>',
    """<th> Target Decision Date </th> <td> {{ target_decision_date }} </td>
    <th> Decision Date </th> <td> {{ decision_date }} </td>""",
    '<th> Committee Date </th> <td> {{ meeting_date }} </td>',
    '<th> Comments By </th> <td> {{ comment_date }} </td>',
    '<th> Start of Consultation </th> <td> {{ consultation_start_date }} </td>',
    '<th> End of Consultation </th> <td> {{ consultation_end_date }} </td>',
    '<th> Decision Level </th> <td> {{ decided_by }} </td>',
    ]
    detail_tests = [
        #{ 'uid': '11/00200/AS', 'len': 21 },
        { 'uid': '89589', 'len': 19 } ] 
    batch_tests = [ 
        { 'from': '95506', 'to': '95536', 'len': 20 }, ]

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

    # note max_sequence here is not exact
    @property
    def max_sequence (self):
        # guess = estimate 2000 per year starting in 2000
        return self.min_sequence + ((date.today().year - 1999) * 2000)
        
    """ note this does not work because values on Web page only filled by internal AJAX calls
    @property
    def max_sequence (self):
        max_recs = None
        response = self.br.open(self._search_url) 
        html = response.read()
        url = response.geturl()
        self.logger.debug('Max page html: %s' % html)
        result = scrapemark.scrape(self._scrape_ids, html, url)
        if result and result.get('records'):
            self._clean_ids(result['records'])
            num_recs = 0
            for i in result['records']:
                print i
                try:
                    num = int(i['uid'])
                    if num > num_recs: 
                        num_recs = num
                except:
                    pass
            self.logger.debug('Number of records %d' % num_recs)
            if num_recs > 0:
                max_recs = num_recs
        return max_recs"""
        
    # post process a set of uid/url records: gets the uid from the url
    def _clean_record(self, record):
        super(AshfordScraper, self)._clean_record(record)
        if record.get('url'):
            uid_match = self._uid_regex.search(record['url'])
            if uid_match and uid_match.group(1):
                record['uid'] = uid_match.group(1)

    def get_html_from_uid(self, uid):
        url = self._applic_url + '?systemkey=' + urllib.quote_plus(uid)
        return self.get_html_from_url(url)
        
