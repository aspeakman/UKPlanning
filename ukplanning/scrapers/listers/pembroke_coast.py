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
import urllib

# Note records are scraped from one paged table of all results
# each is given a notional record number 
# which is the max_recs value minus the offset within the table

# also see Hampshire

class PembrokeCoastScraper(base.ListScraper):

    data_start_target = 6500 # gathering back to this record number (around year 2000)
    min_id_goal = 250 # min target for application ids to fetch in one go
    
    _handler = 'etree'
    _start_point = 15200 # default start if no other indication = see base.py
    _page_size = 20
    _authority_name = 'PembrokeCoast'
    _search_url = 'http://www.pembrokeshirecoast.org.uk/default.asp?PID=243'
    _applic_url = 'http://www.pembrokeshirecoast.org.uk/default.asp?PID=243&APASID='
    _scrape_ids = """
    <div id="page_content"> <table> <tr />
    {* <tr /> <tr>
    <td> <a href="{{ [records].url|abs }}">
    {{ [records].uid }} </a> </td>
    </tr> *}
    </table> </div>
    """
    _scrape_max_recs = "<tr> 1 to 20 of {{ max_recs }} <a /> </tr>"
    _scrape_data_block = """
    <div id="page_content"> {{ block|html }} </div>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <tr> <td> Application </td> <td /> <td> {{ reference }} - received on {{ date_received }} </td> </tr>
    <tr> <td> Proposal </td> <td /> <td> {{ description }} </td> </tr>
    <tr> <td> Location </td> <td /> <td> {{ address|html }} </td> </tr>
    <tr> <td> Registered Date </td> <td /> <td> {{ date_validated }} </td> </tr>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<tr> <td> Applicant </td> <td /> <td> {{ applicant_name|html }} </td> </tr>',
    '<tr> <td> Agent </td> <td /> <td> {{ agent_name|html }} </td> </tr>',
    '<tr> <td> Case Officer </td> <td /> <td> {{ case_officer }} </td> </tr>',
    '<tr> <td> Current Stage </td> <td /> <td> {{ status }} </td> </tr>',
    '<tr> <td> 8 Week Date </td> <td /> <td> {{ application_expires_date }} </td> </tr>',
    '<tr> <td> Level Of Decision </td> <td /> <td> {{ decided_by }} </td> </tr> <tr> <td> Decision </td> <td /> <td> {{ decision }} </td> </tr>',
    ]
    detail_tests = [
        { 'uid': 'NP/14/0388', 'len': 13 } ]
    batch_tests = [ 
        { 'from': '15006', 'to': '15036', 'len': 31 }, ]

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

        start_page = int((num_recs - from_rec) / self._page_size) # max = descending
        end_page = int((num_recs - to_rec) / self._page_size)
        page = start_page
        while page >= 0 and page >= end_page:
            records, r_from, r_to = self._get_id_page (page, self._page_size, num_recs)
            if records:
                if r_from < from_rec:
                    r_start = from_rec - r_from
                else:
                    r_start = 0
                if r_to > to_rec:
                    r_end = len(records) - (r_to - to_rec)
                else:
                    r_end = len(records)
                final_result.extend(records[r_start:r_end])
                page -= 1
            else:
                break
                
        if final_result and len(final_result) == to_rec-from_rec+1:
            #self.logger.debug("From: %d To: %d" % (from_rec, to_rec))
            return final_result, from_rec, to_rec
        else:
            return [], None, None # list scraper - so empty result is always invalid
            
    def _get_id_page (self, page_num, page_size, num_recs):
        # get a result page (numbered from 0) and work out the sequence numbers of the records on it
        # note sequence numbers start from 1
        offset = page_num * page_size
        url = self._search_url + '&offset=' + str(offset)
        response = self.br.open(url)
        html = response.read()
        url = response.geturl()
        result = scrapemark.scrape(self._scrape_ids, html, url)
        if result and result.get('records'):
            this_result = list(reversed(result['records']))
            if len(this_result) <> page_size:
                return [], None, None
            to_rec = num_recs - offset
            from_rec = to_rec - page_size + 1
            #self.logger.debug("Scraped ids: %s" % result)
            self._clean_ids(this_result)
            return this_result, from_rec, to_rec
        else:
            return [], None, None
    
    @property
    def max_sequence (self):
        response = self.br.open(self._search_url) # one fixed page of records
        html = response.read()
        try:
            result = scrapemark.scrape(self._scrape_max_recs, html)
            return int(result['max_recs'])
        except:
            pass
        return None

    def get_html_from_uid (self, uid):
        url = self._applic_url + urllib.quote_plus(uid)
        html, url = self.get_html_from_url(url)
        result = scrapemark.scrape(self._scrape_min_data, html, url)
        if uid.startswith('NP/') or result:
            return html, url
        else:
            url = self._applic_url + urllib.quote_plus('NP/' + uid)
            return self.get_html_from_url(url)


