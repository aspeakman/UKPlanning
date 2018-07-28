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
from .. import base
try:
    from ukplanning import scrapeutils
except ImportError:
    import scrapeutils
import urllib, urlparse

class SouthDerbyshireScraper(base.DateScraper):

    min_id_goal = 250 # min target for application ids to fetch in one go

    _authority_name = 'SouthDerbyshire'
    _search_url = 'http://www.planning.south-derbys.gov.uk/'
    _applic_url = 'http://www.planning.south-derbys.gov.uk/ApplicationDetail.aspx?Ref='
    _date_from_field = {
        'day': 'ctl00$Mainpage$FromDay',
        'month': 'ctl00$Mainpage$FromMonth',
        'year': 'ctl00$Mainpage$FromYear',
        }
    _date_to_field = {
        'day': 'ctl00$Mainpage$ToDay',
        'month': 'ctl00$Mainpage$ToMonth',
        'year': 'ctl00$Mainpage$ToYear',
        }
    _search_fields = {
        'ctl00$Mainpage$Selectdate': 'optValid',
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        }
    _next_target = 'ctl00$Mainpage$gridMain'
    _request_date_format = '%d/%b/%Y'
    _search_form = 'aspnetForm'
    _search_submit = 'ctl00$Mainpage$cmdSetDates'
    _scrape_ids = """
    <table id="ctl00_Mainpage_gridMain"> <tr />
    {* <tr> <td> {{ [records].uid }} </td>
    <td /> <td /> <td /> <td />
    </tr> *}
    </table>
    """
    _scrape_max_pages = '<tr> <td colspan="8"> {{ max_pages }} </td> </tr>'
    _scrape_data_block = """
    <table id="ctl00_Mainpage_detailPlanning"> {{ block|html }} </table>
    """
    _scrape_min_data = """
    <tr> <td> Reference </td> <td> {{ reference }} </td> </tr>
    <tr> <td> Development </td> <td> {{ description }} </td> </tr>
    <tr> <td> Location </td> <td> {{ address }} </td> </tr>
    <tr> <td> Date Received </td> <td> {{ date_received }} </td> </tr>
    <tr> <td> Date Valid </td> <td> {{ date_validated }} </td> </tr>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<tr> <td> Postcode </td> <td> {{ postcode }} </td> </tr>',
    '<tr> <td> Easting </td> <td> {{ easting }} </td> </tr>',
    '<tr> <td> Northing </td> <td> {{ northing }} </td> </tr>',
    '<tr> <td> Consultation Start Date </td> <td> {{ consultation_start_date }} </td> </tr>',
    '<tr> <td> Consultation End Date </td> <td> {{ consultation_end_date }} </td> </tr>',
    '<tr> <td> Target Date </td> <td> {{ target_decision_date }} </td> </tr>',
    '<tr> <td> Delegated </td> <td> {{ decided_by }} </td> </tr>',
    '<tr> <td> Date of Committee </td> <td> {{ meeting_date }} </td> </tr>',
    """<tr> <td> Case Officer </td> <td> {{ case_officer }} </td> </tr>
    <tr> <td> Decision </td> <td> {{ decision }} </td> </tr>""",
    '<tr> <td> Date of Decision </td> <td> {{ decision_date }} </td> </tr>',
    ]
    detail_tests = [
        { 'uid': '9/2012/0665', 'len': 16 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 32 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        
        fields = {}
        fields.update(self._search_fields)
        date_from = date_from.strftime(self._request_date_format)
        date_parts = date_from.split('/')
        fields [self._date_from_field['day']] = date_parts[0]
        fields [self._date_from_field['month']] = date_parts[1]
        fields [self._date_from_field['year']] = date_parts[2]
        date_to = date_to.strftime(self._request_date_format)
        date_parts = date_to.split('/')
        fields [self._date_to_field['day']] = date_parts[0]
        fields [self._date_to_field['month']] = date_parts[1]
        fields [self._date_to_field['year']] = date_parts[2]
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._search_submit)
        
        html = response.read()
        #self.logger.debug("ID batch page html: %s", html)
        try:
            result = scrapemark.scrape(self._scrape_max_pages, html)
            page_list = result['max_pages'].split()
            max_pages = int(page_list[-1]) # can be a space separated list, so take the last value
        except:
            max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        self.logger.debug("Max pages: %s", str(max_pages))
        
        page_count = 0
        while response and page_count < max_pages:
            url = response.geturl()
            #self.logger.debug("Batch html: %s" % html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                for rec in result['records']:
                    rec['url'] = self._applic_url + urllib.quote_plus(rec['uid'])
                page_count += 1
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            else:
                self.logger.debug("Empty result after %d pages", page_count)
                break
            if page_count >= max_pages: break
            try:
                fields = { '__EVENTTARGET': self._next_target,  '__EVENTARGUMENT': 'Page$' + str(page_count+1) }
                scrapeutils.setup_form(self.br, self._search_form, fields)
                for control in self.br.form.controls:
                    if control.type == "submit":
                        control.disabled = True
                #self.logger.debug("Next page form: %s", str(self.br.form))
                response = scrapeutils.submit_form(self.br)
                html = response.read()
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next form after %d pages", page_count)
                break
        
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
            
        return final_result

    def get_html_from_uid(self, uid): 
        url = self._applic_url + urllib.quote_plus(uid)
        return self.get_html_from_url(url) 

        

