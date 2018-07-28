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
from .. import base

class KensingtonScraper(base.PeriodScraper):

    min_id_goal = 300 # min target for application ids to fetch in one go

    _authority_name = 'Kensington'
    _handler = 'etree'
    _period_type = 'Friday'
    _date_field = 'WeekEndDate'
    _query_fields = {  'submit': 'search', 'order': 'Received Date' }
    #_query_fields2 = {  'order': 'Received Date' }
    #_search_form = 'weeklyresults'
    #request_date_format = '%-d/%-m/%Y' only works on linux
    _search_url = 'https://www.rbkc.gov.uk/Planning/searches/default.aspx'
    _weekly_url = 'https://www.rbkc.gov.uk/planning/scripts/weeklyform.asp'
    _results_url = 'https://www.rbkc.gov.uk/Planning/scripts/weeklyresults.asp'
    _applic_url = 'https://www.rbkc.gov.uk/planning/searches/details.aspx?batch=20&type=&tab='
    _scrape_ids = """
    <table summary="Planning Application search results table">
    {* 
    <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> 
    *}
    </table>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <form id="recordDetailsPage"> {{ block|html }} </form>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <table id="property-details">
    <tr> Case reference: {{ reference }} </tr>
    <tr> Address: {{ address }} </tr>
    </table>
    <table id="proposal-details">
    <tr> Proposed development  {{ description }} </tr>
    <tr> Date received: {{ date_received }} </tr>
    <tr> <th> Registration date: </th> {{ date_validated }} </tr>
    </table>"""
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    "<tr> Applicant's name: {{ applicant_name }} </tr>",
    "<tr> Contact name: {{ agent_name }} </tr>", # note bug was agent_address
    "<tr> Contact address: {{ agent_address }} </tr>",
    "<tr> Contact telephone: {{ agent_tel }} </tr>",
    '<tr> Public consultation ends: {{ consultation_end_date }} </tr>',
    '<tr> Planning case officer: {{ case_officer }} </tr>',
    '<tr> <th> Target date for decision: </th> {{ target_decision_date }} </tr>',
    '<tr> <th> Decision date: </th> {{ decision_date }} </tr>',
    '<table id="decision-details"> <tr> <th> Decision: </th> {{ decision }} </tr> </table>',
    '<tr> Application type: {{ application_type }} </tr>',
    '<tr> Application status: {{ status }} </tr>',
    '<tr> Ward: {{ ward_name }} </tr>',
    '<tr> Polling district: {{ parish }} </tr>',
    '<tr> Conservation area: {{ district }} </tr>',
    '<tr> <th> Appeal start date: </th> {{ appeal_date }} </tr>',
    '<tr> <th> Appeal decision: </th> {{ appeal_result }} </tr> <tr> <th> Appeal decision date: </th> {{ appeal_decision_date }} </tr>',
    ]
    detail_tests = [
        { 'uid': 'CA/12/00942', 'len': 14 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'date': '13/09/2012', 'len': 68 }, 
        { 'date': '10/10/2014', 'len': 188 } ]

    def get_id_period (self, this_date):

        final_result = []
        
        #response = self.br.open(self._weekly_url)    
        
        from_dt, to_dt = scrapeutils.inc_dt(this_date, self._period_type)
        date_to = to_dt.strftime('X%d/X%m/%Y').replace('X0','X').replace('X','')
       
        fields = {}
        fields.update(self._query_fields)
        fields[self._date_field] = date_to
        response = self.br.open(self._results_url, urllib.urlencode(fields))
        #scrapeutils.setup_form(self.br, self._search_form, fields)
        #self.logger.debug("ID batch form: %s", str(self.br.form))
        #response = scrapeutils.submit_form(self.br)

        if response:
            html = response.read()
            url = response.geturl()
            #self.logger.debug("ID batch page html: %s", html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
        else:
            return [], None, None
                 
        return final_result, from_dt, to_dt # note weekly result can be legitimately empty
        
    def get_html_from_uid (self, uid):
        url = self._applic_url + '&id=' + urllib.quote_plus(uid)
        return self.get_html_from_url(url)



    
