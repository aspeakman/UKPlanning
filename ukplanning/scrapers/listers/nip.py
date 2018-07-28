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
try:
    from ukplanning import myutils
except ImportError:
    import myutils
import re

class NIPScraper(base.ListScraper):
    
    current_span = 10 # min number of records to get when gathering current ids

    _authority_name = 'NIP'
    _comment = 'National Infrastructure Planning (England and Wales)'
    _applic_url = 'https://infrastructure.planninginspectorate.gov.uk/projects/'
    _old_applic_url = 'https://infrastructure.planningportal.gov.uk/projects/'
    _search_url = 'https://infrastructure.planninginspectorate.gov.uk/projects/register-of-applications/'
    _html_subs = { r'<em>\s*by ': r'<em>', r'zoom=\d+">*': r'zoom=" ',
        r'http://www.openstreetmap.org/\?' : r' xxOPENSTREETMAPxx ',
        r'/wp-content/ipc/maps/' : r' xxIPCMAPxx ' }
    _scrape_ids = """
    <table> <tr /> 
    {* <tr> <td> <a href="{{ [records].url|abs }}"> {{ [records].description }} </a> </td>
    <td> {{ [records].address }} </td>
    <td> {{ [records].applicant_company }} </td>
    <td> {{ [records].date_received }} </td>
    <td> {{ [records].date_validated }} </td>
    <td> {{ [records].status }} </td>
    </tr> *}
    </table>
    """
    _scrape_ids_withdrawn = """
    <table> <tr /> 
    {* <tr> <td> {{ [records].description }} </td>
    <td> {{ [records].address }} </td>
    <td> {{ [records].applicant_company }} </td>
    <td> {{ [records].date_received }} </td>
    <td> {{ [records].date_validated }} </td>
    <td> Withdrawn. This case has been archived </td>
    </tr> *}
    </table>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <div id="page"> {{ block|html }} </div>
    """
    _min_fields = [ 'address', 'description' ] # min fields list used in testing only
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <div id="projecthead"> <h1> {{ description }} </h1> </div>
    <h3> Location </h3> <div class="textwidget"> {{ address }} <div /> </div>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<h3> About this project </h3> <div class="showhide"> {{ details }} </div> ',
    '<h3> Next action </h3> <div class="textwidget"> {{ status }} </div> ',
    '<h1 /> <em> {{ applicant_company }} </em>',
    '<p> Developer: <a> {{ applicant_name }} </a> </p>',
    '<h2>Dates for your diary</h2> <td> <strong> {{ consultation_end_date }} </strong> </td>',
    'xxOPENSTREETMAPxx lat={{ latitude }}&amp;lon={{ longitude }}&amp;zoom="',
    'xxIPCMAPxx {{ latitude }}-{{ longitude }}-national-pinned.png',
    "make_small_mapid('map', new Array({lat: {{ latitude }}, lon: {{ longitude}}})",
    ]
    detail_tests = [
        { 'uid': 'north-west/whitemoss-landfill-western-extension', 'len': 7 } ]
    batch_tests = [ 
        { 'from': '6', 'to': '36', 'len': 31 }, ]

    def get_id_records (self, request_from, request_to, max_recs):
        if not request_from or not request_to or not max_recs:
            return [], None, None # if any parameter invalid - try again next time
        final_result = []
        from_rec = int(request_from)
        to_rec = int(request_to)
        this_max = int(max_recs)
        if from_rec < 1:
            if to_rec < 1: # both too small
                return [], None, None
            from_rec = 1
        if to_rec > this_max:
            if from_rec > this_max: # both too large
                return [], None, None
            to_rec = this_max
        
        response = self.br.open(self._search_url) # one fixed page of records
        html = response.read()
        url = response.geturl()
        #self.logger.debug("ID batch page html: %s", html)
        result = scrapemark.scrape(self._scrape_ids, html, url)
        if result and result.get('records'):
            for r in result['records']:
                r['uid'] = r['url'].replace(self._applic_url, '')
                r['uid'] = r['uid'].replace(self._old_applic_url, '')
                if r['uid'].endswith('/'):
                    r['uid'] = r['uid'][:-1]
            final_result.extend(result['records'])
        result = scrapemark.scrape(self._scrape_ids_withdrawn, html, url)
        if result and result.get('records'):
            for r in result['records']:
                r['url'] = self._search_url
                r['uid'] = re.sub(r'[\W]+', r'-', r['description'].lower(), 0, re.U|re.I)
                r['status'] = 'Withdrawn'
            final_result.extend(result['records'])
        for r in final_result:
            try:
                dt = myutils.get_dt(r['date_received'])
                r['date_received'] = dt.isoformat()
            except:
                if r.get('date_received'):
                    del r['date_received'] # badly formatted dates are removed
            try:
                dt = myutils.get_dt(r['date_validated'])
                r['date_validated'] = dt.isoformat()
            except:
                if r.get('date_validated'):
                    del r['date_validated'] # badly formatted dates are removed
            if r.get('date_received') and r.get('date_validated'):
                if r['date_received'] < r['date_validated']:
                    r['start_date'] = r['date_received']
                else:
                    r['start_date'] = r['date_validated']
            elif r.get('date_received'):
                r['start_date'] = r['date_received']
            elif r.get('date_validated'):
                r['start_date'] = r['date_validated']
        
        if final_result:
            self._clean_ids(final_result)
            fret = sorted(final_result, key=lambda k: k.get('start_date'))
            return fret[from_rec-1:to_rec], from_rec, to_rec
        else:
            return [], None, None # list scraper - so empty result is always invalid
        
    @property
    def max_sequence (self):
        response = self.br.open(self._search_url) # one fixed page of records
        html = response.read()
        url = response.geturl()
        result1 = scrapemark.scrape(self._scrape_ids, html, url)
        result2 = scrapemark.scrape(self._scrape_ids_withdrawn, html, url) # no longer listed
        total = 0
        if result1 and result1.get('records'):
            total += len(result1['records'])
        if result2 and result2.get('records'):
            total += len(result2['records'])
        return total if total else None
        
    def get_html_from_uid (self, uid):
        url = self._applic_url + uid
        return self.get_html_from_url(url)
        
    def _adjust_html(self, html):
        """ Hook to adjust application html of an application if necessary before scraping """
        for k, v in self._html_subs.items(): # adjust html to make match
            html = re.sub(k, v, html, 0, re.U|re.S|re.I) # unicode|dot matches new line|ignore case
        return html
        
    """def _get_details(self, html, this_url):
        "" Scrapes detailed information for one record given html and url 
        - this is an optional hook to allow data from multiple linked pages to be merged ""
        result = self._get_detail(html, this_url)
        if 'scrape_error' in result or result.get('details') is None or result.get('description') is None:
            return result
        result['description'] = result['description'] + ' ' + result['details']
        del result['details']
        return result"""
        
    def _clean_record(self, record):
        super(NIPScraper, self)._clean_record(record) 
        if record.get('details'):
            if record.get('description'):
                record['description'] = record['description'] + '. ' + record['details']
            else:
                record['description'] = record['details']
            del record['details']
        
  

            

