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
from .. import base
try:
    from ukplanning import scrapeutils
except ImportError:
    import scrapeutils
import urllib

class BostonScraper(base.DateScraper):

    min_id_goal = 300 # min target for application ids to fetch in one go

    _authority_name = 'Boston'
    _comment = 'Was SwiftLG before Sep 2014'
    _search_url = 'http://www.boston.gov.uk/index.aspx?articleid=6207&ShowAdvancedSearch=true'
    _applic_url = 'http://www.boston.gov.uk/index.aspx?articleid=6208&ApplicationNumber='
    _search_form = '1'
    _search_submit = 'searchFilter'
    _date_from_field = 'DateStart'
    _date_to_field = 'DateEnd'
    _search_fields = { 'ApplicationState': 'ReceivedDate', 
        'DatePresets': 'None', 'ViewName': 'ViewList', 'ResultSize': '10', }
    _next_submit = 'searchResults_Page'
    _scrape_ids = """
    <form class="cmxform">
    {* <div class="PlanningApplication"> <h4> <a href="{{ [records].url|abs }}"> {{ [records].uid }} - </a> </h4> </div>  *}
    </form>
    """
    _scrape_max_recs = '<h1> Search results </h1> <strong> {{ max_recs }} </strong> results found.'

    _scrape_data_block = '<div id="content"> {{ block|html }} </div>'
    _scrape_min_data = """
    <tr> <td> Reference </td> <td> {{ reference }} </td> </tr>
    <tr> <td> Location </td> <td> {{ address }} </td> </tr>
    <tr> <td> Proposal </td> <td> {{ description }} </td> </tr>
    <tr> <td> Received </td> <td> {{ date_received }} </td> </tr>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<tr> <td> Type </td> <td> {{ application_type }} </td> </tr>',
    """<tr> <td> Decision </td> <td> {{ decision }} </td> </tr>
    <tr> <td> Decision made </td> <td> {{ decision_date }} </td> </tr>""",
    '<tr> <td> Applicant </td> <td> {{ applicant_name }} </td> </tr>',
    '<tr> <td> Agent </td> <td> {{ agent_name }} </td> </tr>',
    '<tr> <td> Parish </td> <td> {{ parish }} </td> </tr>',
    ]
    detail_tests = [
        { 'uid': 'B/13/0337', 'len': 11 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 14 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 5 } ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s", response.read())

        fields = {}
        fields.update(self._search_fields)
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._search_submit)
        
        html = response.read()
        #self.logger.debug("ID batch page html: %s", html)
        try:
            result = scrapemark.scrape(self._scrape_max_recs, html)
            max_recs = int(result['max_recs'])
        except:
            max_recs = 0
        
        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        while response and len(final_result) < max_recs and page_count < max_pages:
            url = response.geturl()
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                page_count += 1
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            else:
                self.logger.debug("Empty result after %d pages", page_count)
                break
            if len(final_result) >= max_recs: break
            try:
                fields = { self._next_submit: str(page_count+1) }
                scrapeutils.setup_form(self.br, self._search_form, fields)
                for control in self.br.form.controls:
                    if control.type == "submit" and (control.name <> self._next_submit or control.value <> str(page_count+1)):
                        control.disabled = True
                self.logger.debug("ID next form: %s", str(self.br.form))
                response = scrapeutils.submit_form(self.br)
                html = response.read()
                #self.logger.debug("ID next page html: %s", html)
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next form after %d pages", page_count)
                break
        
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
            
        return final_result
        
    def get_html_from_uid(self, uid):
        url = self._applic_url + urllib.quote_plus(uid)
        return self.get_html_from_url(url) 
        
        

