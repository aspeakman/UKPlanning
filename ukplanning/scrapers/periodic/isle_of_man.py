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
from datetime import timedelta
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
from .. import base

class IsleOfManScraper(base.PeriodScraper):

    min_id_goal = 200 # min target for application ids to fetch in one go
    current_span = 28 # start this number of days ago when gathering current ids

    _authority_name = 'IsleOfMan'
    _period_type = 'Friday'
    _search_form = '0'
    _date_field = 'PressListDate'
    _query_fields =  { 'SearchField': 'PressListDate' }
    _ref_field = 'ctl00$mainContent$appnum'
    _request_date_format = '%Y-%m-%dT00:00:00.000'
    _detail_submit = 'ctl00$mainContent$butAppnum'
    _search_url = 'https://www.gov.im/planningapplication/services/planning/search.iom'
    _detail_page = 'planningapplicationdetails.iom'
    _results_page = 'applicationsearchresults.iom'
    _scrape_next_link = '<div class="pagesearchbuttons"> | <a href="{{ next_link }}"> Next </a> </div>'
    _junk_regex = re.compile(r'&#xD;|&#xA;') 
    _space_regex = re.compile(r'\s+', re.U) 
    _scrape_ids = """
    <table class="results"> <tr />
    {* <tr>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td> </tr>
    <tr /> *}
    </table>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <div class="subsection"> {{ block|html }} </div>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <h2> Planning Application: {{ reference }} ( </h2>
    <th> Address </th> <td> {{ address }} </td>
    <th> Proposal </th> <td> {{ description }} </td>
    <th> Application Date </th> <td> {{ date_received }} </td>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<th> Parish </th> <td> {{ parish }} </td>',
    '<th> Status </th> <td> {{ status }} </td>',
    '<th> Date the decision was issued </th> <td> {{ decision_issued_date }} </td>',
    '<th> Status of the appeal </th> <td> {{ appeal_status }} </td>',
    '<th> Date an appeal was lodged </th> <td> {{ appeal_date }} </td>',
    '<th> Date the appeal was determined </th> <td> {{ appeal_decision_date }} </td>',
    ]
    detail_tests = [
        { 'uid': '11/00581/B', 'len': 8 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'date': '13/09/2012', 'len': 29 }, 
        { 'date': '10/10/2014', 'len': 24 } ]

    def get_id_period (self, this_date):

        final_result = []
        from_dt, to_dt = scrapeutils.inc_dt(this_date, self._period_type)
        do_dt = to_dt # the date being tested - can change
        rurl = urlparse.urljoin(self._search_url, self._results_page)

        for i in range(5): # note works backwards through all 5 possible week days as some lists are not published exactly on a Friday
    
            fields = {}
            fields.update(self._query_fields)
            fields[self._date_field] = do_dt.strftime(self._request_date_format)
            response = self.br.open(rurl + '?' + urllib.urlencode(fields))
    
            page_count = 0
            max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
            while response and page_count < max_pages:
                html = response.read()
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
                try:
                    new_html = self._junk_regex.sub('', html) # remove internal junk characters
                    result = scrapemark.scrape(self._scrape_next_link, new_html, url)
                    next_link = self._space_regex.sub('', result['next_link']) # remove all spaces
                    response = self.br.open(next_link)
                except:
                    self.logger.debug("No next link after %d pages", page_count)
                    break
            do_dt = do_dt - timedelta(days=1) # try again with a different date

        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
            
        return final_result, from_dt, to_dt # note weekly result can be legitimately empty
        
    def get_html_from_uid (self, uid):
        url = urlparse.urljoin(self._search_url, self._detail_page) + '?ApplicationReferenceNumber=' + urllib.quote_plus(uid)
        return self.get_html_from_url(url)



    
