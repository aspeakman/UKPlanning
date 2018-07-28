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
import urllib
from datetime import date

class SouthKestevenScraper(base.PeriodScraper):

    min_id_goal = 250 # min target for application ids to fetch in one go
    
    _authority_name = 'SouthKesteven'
    _period_type = 'Month'
    _search_fields = { 'applicationType': 'Validated', 'listingType': 'Monthly' }
    _search_url = 'http://www.southkesteven.gov.uk/index.aspx?articleid=9229'
    _applic_url = 'http://www.southkesteven.gov.uk/index.aspx?articleid=8170&application='
    #_applic_url = 'http://www.southkesteven.gov.uk/index.aspx?articleid=8170#/application/'
    
    _scrape_ids = """
    <main class="article">
    {* <li class="search-result"> <a href="{{ [records].url|abs }}"> 
    <h1> {{ [records].uid }} - </h1> </a> </li> *}
    </main>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <main class="article planning"> {{ block|html }} </main>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <p class="intro"> <strong> Proposal </strong> {{ description }} </p>
    <dt> Reference </dt> <dd> {{ reference }} </dd>
    <dt> Location </dt> <dd> {{ address }} </dd>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<dt> Received </dt> <dd> {{ date_received }} </dd>',
    '<dt> Validated </dt> <dd> {{ date_validated }} </dd>',
    #'<dt> Reference </dt> <dd> - {{ applicant_name }} </dd>',
    '<dt> Type </dt> <dd> {{ application_type }} </dd>',
    '<dt> Decision </dt> <dd> {{ decision }} </dd>',
    """<dt> Decision </dt> <dd> {{ decision }} </dd>
    <dt> Decision date </dt> <dd> {{ decision_date }} </dd>""",
    '<dt> Agent </dt> <dd> {{ agent_name }} </dd>',
    '<dt> Applicant </dt> <dd> {{ applicant_name }} </dd>',
    '<dt> Case officer </dt> <dd> {{ case_officer }} </dd>',
    ]
    detail_tests = [
        { 'uid': 'S16/0568', 'len': 12 },
        { 'uid': 'S12/2384', 'len': 12 }, ]
    batch_tests = [ # note date ranges should not overlap
        { 'date': '01/09/2015', 'len': 147 }, 
        { 'date': '13/09/2012', 'len': 142 }, 
        { 'date': '13/08/2012', 'len': 132 } ] 

    def get_id_period (self, this_date):

        final_result = []
        month = this_date.month
        year = this_date.year
        from_dt, to_dt = scrapeutils.inc_dt(this_date, self._period_type) # date range of month
        """ this kludge no longer required
        # note this is not calendar month = 
        # = from Monday of the first week fully in the month
        # = to Sunday of the last week of the month (can be in the next month)
        first_dt, last_dt = scrapeutils.inc_dt(this_date, self._period_type) # date range of month  
        dummy1, from_dt = scrapeutils.inc_dt(first_dt, 'Monday') # window starts at first Monday within month
        if this_date < from_dt: # use preceding month, if target date before window start
            month = month - 1
            if month < 1:
                month = 12
                year = year - 1
            new_date = date(year, month, 1) # first day of preceding month
            first_dt, last_dt = scrapeutils.inc_dt(new_date, self._period_type) # date range of preceding month
            dummy1, from_dt = scrapeutils.inc_dt(first_dt, 'Monday') # first Monday within month
        dummy2, to_dt = scrapeutils.inc_dt(last_dt, 'Sunday') # last Sunday (can be in next month)
        self.logger.debug("Month date extent: %s %s" % (from_dt.isoformat(), to_dt.isoformat()))"""
        
        response = self.br.open(self._search_url)
        
        fields = {}
        fields.update(self._search_fields)
        fields ['month'] = str(month)
        fields ['year'] = str(year)
        
        #scrapeutils.setup_form(self.br, self._search_form, fields)
        #self.logger.debug("ID batch form: %s", str(self.br.form))
        #response = scrapeutils.submit_form(self.br)
        
        response = self.br.open(self._search_url, urllib.urlencode(fields))
            
        if response: 
            html = response.read()
            url = response.geturl()
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            
        if final_result:
            return final_result, from_dt, to_dt
        else:
            return [], None, None # monthly scraper - so empty result is always invalid

    def get_html_from_uid(self, uid):
        url = self._applic_url + urllib.quote_plus(uid) 
        return self.get_html_from_url(url)


