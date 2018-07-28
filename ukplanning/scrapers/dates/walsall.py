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
try:
    from ukplanning import scrapeutils
except ImportError:
    import scrapeutils
from .. import base
from datetime import date
import urllib

# Note no longer in use - now SwiftLG

# Note due to website limitations this scraper does a kludgy date search 
# it finds applications decided between the specified dates
# it then adds from the full list of all undecided applications
# those that were validated between the specified dates

#also see Ribble Valley, Burnley, Wyre, Rossendale

class WalsallOldScraper(base.DateScraper):

    min_id_goal = 350 # min target for application ids to fetch in one go
    
    _disabled = True
    _uid_only = True # this can only access applications via uid not url
    _handler = 'etree'
    _authority_name = 'WalsallOld'
    _applic_url = 'http://www2.walsall.gov.uk/dcaccess/headway/planningAppdrillDown.asp'
    _search_url = 'http://www2.walsall.gov.uk/dcaccess/headway/Applicationsearch.asp'
    _pending_url = 'http://www2.walsall.gov.uk/dcaccess/headway/appspendingdecision.asp'
    _decided_url = 'http://www2.walsall.gov.uk/dcaccess/headway/appswithadecision.asp'
    _date_from_field = 'DateFrom'
    _date_to_field = 'DateTo'
    _ref_field = 'AppNo'
    _search_form = 'NumberSearch'
    _decided_form = 'f2'
    _scrape_ids = """
    <p class="MISheader"> Application Search Results </p>
        {* <form> 
                <input name="AppNumber" type="HIDDEN" value="{{[records].uid}}">
                <input name="AppID" type="HIDDEN" value="{{[records].reference}}">
            </form> *}
    <div id="footerenvironment" />
    """
    _scrape_id = """
    <h1> Planning Application History </h1>
        {* <form> 
                <input name="AppNumber" type="HIDDEN" value="{{[records].uid}}">
                <input name="AppID" type="HIDDEN" value="{{[records].reference}}">
            </form> *}
    <h3> Disclaimer </h3>
    """
    _scrape_pending_ids = """
    <h1> Applications Pending Decision </h1> <tr class="resultcolumnbackground" />
        {* <tr> <input name="AppNumber" type="HIDDEN" value="{{[records].uid}}">
                <input name="AppID" type="HIDDEN" value="{{[records].reference}}"> 
                {{[records].rest}}
             </tr>
             *}
    <div id="footer" />
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <div id="content"> {{ block|html }} </div>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <tr> <td> DATE RECEIVED </td> <td> {{ date_received }} </td> </tr>
    <tr> <td> DATE VALID </td> <td> {{ date_validated }} </td> </tr>
    <tr> <td> DESCRIPTION </td> <td> {{ description }} </td> </tr>
    <tr> <td> ADDRESS </td> <td> {{ address }} </td> </tr>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<tr> <td> APPLICATION TYPE </td> <td> {{ application_type }} </td> </tr>',
    '<tr> <td> DECISION DATE </td> <td> {{ decision_date }} </td> </tr>',
    '<tr> <td> OFFICER </td> <td> {{ case_officer }} </td> </tr>',
    '<tr> <td> WARD </td> <td> {{ ward_name }} </td> </tr>',
    '<tr> <td> DECISION DETAIL </td> <td> {{ decision }} </td> </tr>',
    '<tr> <td> EASTING </td> <td> {{ easting }} </td> </tr>',
    '<tr> <td> NORTHING </td> <td> {{ northing }} </td> </tr>',
    '<a href="{{ comment_url|abs }}">Click here to comment on this application</a>'
    ]
    detail_tests = [
        { 'uid': '12/0002/DOC', 'len': 13 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 26 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 } ]
        
    def get_id_batch (self, date_from, date_to): 

        final_result = []
        response = self.br.open(self._decided_url)
        #self.logger.debug("Start html: %s", response.read())

        fields = {}
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._decided_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
            
        if response:
            html = response.read()
            url = response.geturl()
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                self._clean_ids(result['records'])
                keys = set()
                for r in result['records']: # usually returns several duplicates, so weed them out
                    if r['reference'] not in keys:
                        final_result.append(r)
                        keys.add(r['reference'])
                        
        # now we add in all the system undecided applications (>750) which are scraped separately
        # we filter them to check if their date validated is within the from/to date range
        undecided = self._get_pending_ids()
        self.logger.debug("Found %d undecided applications", len(undecided))
        added = 0
        for r in undecided:
            if r.get('date_validated') and r['date_validated'] >= date_from.isoformat() and r['date_validated'] <= date_to.isoformat():
                final_result.append(r)
                added += 1
        self.logger.debug("Added %d undecided applications with dates validated in range", added)
            
        return final_result
            
    def _get_pending_ids (self):
        
        final_result = []
        response = self.br.open(self._pending_url) # one fixed page of records
        
        if response:
            html = response.read()
            #self.logger.debug("Pending html: %s", html)
            url = response.geturl()
            result = scrapemark.scrape(self._scrape_pending_ids, html, url)
            if result and result.get('records'):
                self._clean_ids(result['records'])
                keys = set()
                for r in result['records']: # usually returns several duplicates, so weed them out
                    if r['reference'] not in keys:
                        final_result.append(r)
                        keys.add(r['reference'])
                        
        return final_result
    
    """@property not used for DateScraper = today's date, only ListScraper
    def max_sequence (self):
        p_list = self._get_pending_ids() 
        max_sequence = 0
        for p in p_list:
            try:
                val = int(p['reference'])
                if val > max_sequence:
                    max_sequence = val
            except:
                continue
        if max_sequence:
            return max_sequence
        else:
            return None"""

    def get_html_from_uid (self, uid):
        response = self.br.open(self._search_url)
        #self.logger.debug("ID detail start html: %s", response.read())
        fields = { self._ref_field: uid }
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID detail form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        return self._get_html(response)
        
    def _get_details(self, html, this_url):
        """ Scrapes detailed information for one record given html and url 
        - this is an optional hook to allow data from multiple linked pages to be merged """
        r = scrapemark.scrape(self._scrape_id, html, this_url)
        if r and r.get('records'):
            self._clean_ids(r['records'])
            #for r in r['records']:
            #    if r.get('uid', '') == uid:
            result = r['records'][0]
            data = { 'AppNumber': result['uid'],
                'AppID': result['reference'] }
            response = self.br.open(self._applic_url, urllib.urlencode(data))
            html, url = self._get_html(response)
            result2 = self._get_detail(html, url) 
            if 'scrape_error' not in result2:
                result.update(result2)
                return result
            else:
                self.logger.warning("No information found on applic page")
                return result2 # ie return error message
        self.logger.warning("Error when getting detail from %s: %s" % (this_url, self.errors[self.NO_DATA]))
        return { 'scrape_error': self.errors[self.NO_DATA] }
        
    # post process a set of uid/url records: gets the uid from the url
    def _clean_record(self, record):
        if record.get('rest'):
            fields = record['rest'].split()
            record['date_validated'] = fields[-4:-3]
            record.pop('rest', None)
        super(WalsallScraper, self)._clean_record(record)


 
