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
from .. import basereq
from datetime import date, timedelta
import urllib, urlparse
import re
import requests

# also see Wyre, Rossendale, Burnley, Walsall
# SSL error on this site when using python 2.7.6/mechanize/urllib2 interface
# [Errno 1] _ssl.c:510: error:1409442E:SSL routines:SSL3_READ_BYTES:tlsv1 alert protocol version
# So re-engineered to use requests[security] and hence urllib3

class RibbleValleyScraper(basereq.ListReqScraper):

    data_start_target = 1 # gathering back to this record number (around end of 1999)
    min_id_goal = 200 # min target for application ids to fetch in one go
    current_span = 60 # min number of records to get when gathering current ids
    
    _authority_name = 'RibbleValley'
    _uid_num_sequence = True # uid is numeric sequence number not the local authority reference
    _start_point = 25500 # default start if no other indication = see base.py
    #_handler = 'etree' no effect now
    _search_url= 'https://www.ribblevalley.gov.uk/planningApplication/search/advanced'
    _applic_url = 'https://www.ribblevalley.gov.uk/site/scripts/planx_details.php'
    _direct_url = 'https://www.ribblevalley.gov.uk/planningApplication'
    _result_url = 'https://www.ribblevalley.gov.uk/planningApplication/search/results'
    _uid_regex = re.compile(r'planningApplication/(\d+)\s*$')
    _search_fields = { 'location': '', 'applicant': '', 'developmentDescription': '', 'decisionType': '', 'decisionDate': '', 'advancedSearch': 'Search' }
    _no_results = 'https://www.ribblevalley.gov.uk/planningApplication/search/no_results'
    _scrape_ids = """
    <article> <tr />
        {* <tr> <td> <a href="{{ [records].url|abs }}"> {{ [records].reference }} </a> </td> <td /> </tr> *}
    </article>"""
    _scrape_max_recs = '<h2> {{ max_recs }} results for </h2>'
    _scrape_invalid_format = '<h2 class="warning"> No results were {{ invalid_format }} for your search </h2>'
    _scrape_one_id = """
    <article>
        <h1> Application {{ uid }} </h1>
    </article>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <article> {{ block|html }} </article>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <h1> Application {{ reference }} </h1>
    <p class="first">  <br/> {{ description }} </p>
    <table> 
    <tr> <td> Development address </td> <td> <strong> {{ address }} </strong> </td> </tr>
    <tr> <td> Key dates </td> <td> <strong> Received </strong> : {{ date_received }} <br> </td> </tr>
    </table>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<tr> <td> Key dates </td> <td> <strong> Valid </strong> : {{ date_validated }} <br> </td> </tr>',
    '<p class="first"> <strong> {{ application_type }} </strong> </p>',
    '<tr> <td> Development address </td> <td> <strong> Ward </strong> : {{ ward_name }} <br /> </td> </tr>',
    '<tr> <td> Development address </td> <td> <strong> Parish </strong> : {{ parish }} </td> </tr>',
    '<tr> <td> Officer </td> <td> <strong> {{ case_officer }} </strong> </td> </tr>',
    '<tr> <td> Applicant </td> <td> <strong> {{ applicant_name }} </strong> {{ applicant_address }} </td> </tr>',
    '<tr> <td> Agent </td> <td> <strong> {{ agent_name }}</strong> {{ agent_address }} </td> </tr>',
    '<tr> <td> Planning Status </td> <td> {{ status }} </td> </tr>',
    '<tr> <td> Decision </td> <td> <strong> {{ decision }} </strong> Date : {{ decision_date }} </td> </tr>',
    '<tr> <td> Key dates </td> <td> <strong> Committee </strong> : {{ meeting_date }} </td> </tr>',
    ]
    detail_tests = [
        { 'uid': '3/2010/0068', 'len': 18 }, 
        { 'uid': '20524', 'len': 18 }, 
        { 'uid': '26869', 'len': 18 },
        { 'uid': '3/2016/0011', 'len': 18 },
        { 'uid': '27329', 'len': 18 },
        { 'uid': '3/2016/0478', 'len': 18 }, ] 
    batch_tests = [ 
        { 'from': '2506', 'to': '2536', 'len': 31 }, ]

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
            
        for i in range(from_rec, to_rec + 1):
            #final_result.append( { 'url': self._applic_url + '?appID=' + str(i), 'uid': str(i) } )
            final_result.append( { 'url': self._direct_url + '/' + str(i), 'uid': str(i) } )
        
        if final_result:
            return final_result, from_rec, to_rec
        else:
            return [], None, None # list scraper - so empty result is always invalid

    # note max_sequence here is not exact
    @property
    def max_sequence (self):
        """ kludge - we arbitarily define the max sequence as the highest numeric id of 
        the latest decided applications + half min_id_goal """
        date_to = date.today()
        date_from = date_to - timedelta(days=14)
        result = self.get_id_batch(date_from, date_to)
        max_recs = None
        for r in result:
            if r.get('uid') and r['uid'].isdigit():
                uid = r['uid']
            else:
                uid = r['url'].replace(self._direct_url + '/', '')
            if uid.isdigit():
                uid = int(uid)
                if max_recs is None or uid > max_recs:
                    max_recs = uid
        if max_recs is not None:
            return max_recs + int(self.min_id_goal / 2)
        else:
            return max_recs
        
    def get_id_batch(self, date_from, date_to):

        final_result = []
        
        fields = {}
        fields.update(self._search_fields)
        fields['lowerLimit'] = '0'
        fields['fromDay'] = str(date_from.day)
        fields['fromMonth'] = str(date_from.month)
        fields['fromYear'] = str(date_from.year)
        fields['toDay'] = str(date_to.day)
        fields['toMonth'] = str(date_to.month)
        fields['toYear'] = str(date_to.year)
        #response = self.br.open(self._result_url + '?' + urllib.urlencode(fields))
        response = self.rs.get(self._result_url + '?' + urllib.urlencode(fields), timeout=self._timeout) 
        
        #html = response.read()
        html = response.text
        #self.logger.debug("ID batch page html: %s", html)
        try:
            result = scrapemark.scrape(self._scrape_max_recs, html)
            max_recs = int(result['max_recs'])
        except:
            max_recs = 0
        
        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        while response and len(final_result) < max_recs and page_count < max_pages:
            #url = response.geturl()
            url = response.url
            #self.logger.debug("Batch html: %s" % html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                page_count += 1
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            elif not final_result: # is it a single record?
                single_result = scrapemark.scrape(self._scrape_one_id, html, url)
                if single_result:
                    single_result['url'] = url
                    self._clean_record(single_result)
                    return [ single_result ]
            else:
                self.logger.debug("Empty result after %d pages", page_count)
                break
            if len(final_result) >= max_recs: break
            try:
                rec_count = len(final_result)
                fields['lowerLimit'] = str(rec_count)
                #response = self.br.open(self._result_url + '?' + urllib.urlencode(fields))
                response = self.rs.get(self._result_url + '?' + urllib.urlencode(fields), timeout=self._timeout)
                #html = response.read()
                html = response.text
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next link after %d pages", page_count)
                break
        
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)

        return final_result
        
    # post process a set of uid/url records: note uses a numeric uid from the url not the reference
    def _clean_record(self, record):
        super(RibbleValleyScraper, self)._clean_record(record)
        if record.get('url'):
            uid_match = self._uid_regex.search(record['url'])
            if uid_match and uid_match.group(1):
                record['uid'] = uid_match.group(1)
        if record.get('description') and record['description'].startswith('Comment on this application '):
            record['description'] = record['description'].replace('Comment on this application ', '')

    def get_html_from_uid(self, uid):
        if uid.isdigit():
            url = self._direct_url + '/' + urllib.quote_plus(uid)
            return self.get_html_from_url(url)
        else:
            url = self._applic_url + '?appNumber=' + urllib.quote_plus(uid)
            return self.get_html_from_url(url)
            