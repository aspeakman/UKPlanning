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

# Note due to website limitations this scraper does a kludgy date search 
# it finds applications decided between the specified dates
# it then adds from the full list of all undecided applications
# those that were validated between the specified dates

#also see Ribble Valley, Burnley, Wyre, Rossendale, Walsall

class DerbyshireScraper(base.DateScraper):

    min_id_goal = 350 # min target for application ids to fetch in one go
    
    _handler = 'etree'
    _authority_name = 'Derbyshire'
    _applic_url = 'https://www.derbyshire.gov.uk/environment/planning/planning_applications/current_applications/application_details/app-details.asp'
    _search_url = 'https://www.derbyshire.gov.uk/environment/planning/planning_applications/default.asp'
    _pending_url = 'https://www.derbyshire.gov.uk/environment/planning/planning_applications/current_applications/default.asp'
    _decided_url = 'https://www.derbyshire.gov.uk/environment/planning/planning_applications/recent_decisions/default.asp'
    _date_from_field = 'DateFrom'
    _date_to_field = 'DateTo'
    _search_form = 'findCaseByDate'
    _scrape_ids = """
    <table id="AutoNumber1"> <tr />
    {* <tr> <td> {{ [records].decision_date }} </td>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    <td> {{ [records].address }} </td> <td /> <td> {{ [records].decision }} </td>
    </tr> *}
    </table>
    """
    _scrape_pending_ids = """
    <table id="AutoNumber1"> <tr />
    {* <tr> <td> {{ [records].date_validated }} </td>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    <td> {{ [records].address }} </td> <td /> <td> {{ [records].status }} </td>
    </tr> *}
    </table>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <div id="contentWrapOne"> {{ block|html }} </div>
    """
    _min_fields = [ 'reference', 'description' ] # min fields list used in testing only
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <h1> Case file for {{ reference }} </h1>
    <h2> Description </h2> <p> {{ description }} </p>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<h3> Received </h3> <p> {{ date_received }} </p>',
    '<h3> Validated </h3> <p> {{ date_validated }} </p>',
    '<h2> Application Type </h2> <p> {{ application_type }} </p>',
    '<h2> Officer </h2> <p> {{ case_officer }} </p>',
    '<h2> Applicant </h2> {{ applicant_name }} <h3> Address </h3> <p> {{ applicant_address|html }} </p>',
    '<h2> Agent </h2> {{ agent_name }} <h3> Address </h3> <p> {{ agent_address|html }} </p>',
    '<h3> Public Consultation </h3> <p> From {{ consultation_start_date }} to {{ consultation_end_date }} </p>',
    '<h3> Committee Date </h3> <p> {{ meeting_date }} </p>',
    '<h3> Committee or Delegated </h3> <p> {{ decided_by }} </p>',
    """<h3> Decision date </h3> <p> {{ decision_date }} </p>
    <h3> Decision </h3> <p> {{ decision }} </p>""",
    '<h2> Ward / Parish </h2> <p> {{ ward_name }} </p>',
    '<h2> Ward / Parish </h2> <p> {{ parish }} </p>',
    '<a href="{{ comment_url|abs }}"> Comment on this application </a>'
    ]
    detail_tests = [
        { 'uid': 'CW4/1209/176', 'len': 14 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 11 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 1 } ]
            
    def get_id_batch (self, date_from, date_to): 

        final_result = []
        response = self.br.open(self._decided_url)
        #self.logger.debug("Start html: %s", response.read())

        fields = {}
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
            
        if response:
            html = response.read()
            url = response.geturl()
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
                        
        # now we add in all the system undecided applications (>50) which are scraped separately
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
                final_result.extend(result['records'])
                        
        return final_result

    def get_html_from_uid (self, uid):
        # note apptype 1 is a decision (with decision fields) 
        # whereas apptype 2 is the case file (with date received fields)
        url = self._applic_url + '?AppType=2&AppCode=' + urllib.quote_plus(uid)
        return self.get_html_from_url(url)
        
    def _get_details(self, html, this_url):
        """ Scrapes detailed information for one record given html and url 
        - this is an optional hook to allow data from multiple linked pages to be merged """
        result = self._get_detail(html, this_url)
        if 'scrape_error' in result:
            return result
        if 'AppType=1' in this_url:
            next_url = this_url.replace('AppType=1', 'AppType=2')
        elif 'AppType=2' in this_url:
            next_url = this_url.replace('AppType=2', 'AppType=1')
        else:
            return result
        try:
            self.logger.debug("Second url: %s", next_url)
            response = self.br.open(next_url)
            html, url = self._get_html(response)
        except:
            self.logger.warning("No link to other data page found")
        else:
            result2 = self._get_detail(html, url)
            if 'scrape_error' not in result2:
                result.update(result2)
            else:
                self.logger.warning("No information found on other data page")
        return result
        


 
