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

# also see Stevenage

class CeredigionScraper(base.DateScraper):
    
    min_id_goal = 300 # min target for application ids to fetch in one go
    
    _uid_only = True # this can only access applications via uid not url
    _headers = {
    'User-Agent': 'Mozilla/5.0 (Windows; U; MSIE 7.0; Windows NT 6.0; en-US)',
    'Accept-Charset': 'UTF-8,*',
    'Accept': 'text/html',
    'Accept-Language': 'en-gb,en',
    }
    _authority_name = 'Ceredigion'
    _handler = 'soup'
    _date_from_field = 'CTRL:61:_:A'
    _date_to_field = 'CTRL:62:_:A'
    _appno_field = 'CTRL:49:_:A'
    _search_form = 'RW'
    _submit_control = 'CTRL:303:_'
    _next_control = 'CTRL:307:_:E.h'
    _scrape_next = """<a href="javascript:com.ebasetech.ufs.Main.inputSubmit('CTRL:307:_:E.h');"> {{ next }} </a>"""
    _date_search = { 'CTRL:515:_.h': 'By date' }
    _date_page = { 'PAGE:F': 'CTID-515-_' }
    _ref_search = { 'CTRL:507:_.h': 'By application reference number' }
    _ref_page = { 'PAGE:F': 'CTID-507-_' }
    _search_url = 'http://forms.ceredigion.gov.uk/ufs/ufsmain?formid=DESH_PLANNING_APPS&LANGUAGE=EN'
    _scrape_invalid_format = '<div> No details were found by this search. {{ invalid_format }} </div>'
    _first_search = True
    _scrape_ids_ref = """
    Search Results
    {* Application Reference Number 
    <a href="javascript:com.ebasetech.ufs.Main.inputSubmit('{{[records].control}}');"> {{[records].uid}} </a> 
    *} """
    _scrape_ids = """
    Search Results
    {* Application Reference Number 
    <a> {{[records].uid}} </a> 
    Type: <td> {{[records].application_type}} </td>
    Community: <td> {{[records].parish}} </td>
    Postcode: <td> {{[records].postcode}} </td> *}
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <body> Application Details {{ block|html }} </body>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <div id="CTID-412-_-A"> {{ reference }} </div>
    <div id="CTID-424-_-A"> {{ description }} </div>
    <div id="CTID-415-_-A"> {{ address }} </div>
    <div id="CTID-418-_-A"> {{ date_received }} </div>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<div id="CTID-419-_-A"> {{ date_validated }} </div>',
    '<div id="CTID-414-_-A"> {{ application_type }} </div>', 
    '<div id="CTID-416-_-A"> {{ decision }} </div>',
    '<div id="CTID-411-_-A"> {{ agent_name }} </div>',
    '<div id="CTID-423-_-A"> {{ agent_company }} </div>',
    '<div id="CTID-413-_-A"> {{ applicant_name }} </div>',
    '<div id="CTID-422-_-A"> {{ ward_name }} </div>',
    '<div id="CTID-417-_-A"> {{ case_officer }} </div>',
    '<div id="CTID-420-_-A"> {{ meeting_date }} </div>',
    '<div id="CTID-421-_-A"> {{ decision_date }} </div>',
    '<div id="CTID-399-_-A"> {{ easting }}, {{ northing }} </div>',
    ]
    detail_tests = [
        { 'uid': 'A120698', 'len': 14 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 53 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 4 } ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        if self._first_search: # launch search facility page with button appears only on first opening of this url
            scrapeutils.setup_form(self.br)
            response = scrapeutils.submit_form(self.br)
            self._first_search = False
        #self.logger.debug("Start html: %s", response.read())

        fields = {}
        fields.update(self._date_search)
        fields.update(self._date_page)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        #self.logger.debug("Choose search form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        
        fields = {}
        fields.update(self._date_page)
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._submit_control)
            
        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        while response and page_count < max_pages:
            html = response.read()
            #self.logger.debug("ids html: %s", html)
            url = response.geturl()
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                page_count += 1
                self._clean_ids(result['records'])
                for r in result['records']:
                    if r.get('control'):
                        del r['control']
                final_result.extend(result['records'])
            else:
                self.logger.debug("Empty result after %d pages", page_count)
                break
            try:
                result = scrapemark.scrape(self._scrape_next, html, url)
                if result:
                    fields = { self._next_control: '>' }
                    scrapeutils.setup_form(self.br, self._search_form, fields)
                    #self.logger.debug("ID next form: %s", str(self.br.form))
                    response = scrapeutils.submit_form(self.br)
                else: 
                    self.logger.debug("No next link after %d pages", page_count)
                    break
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next form after %d pages", page_count)
                break
        
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
            
        return final_result
        
    def get_html_from_uid (self, uid):
        response = self.br.open(self._search_url)
        if self._first_search: # launch search facility page with button appears only on first opening of this url
            scrapeutils.setup_form(self.br)
            response = scrapeutils.submit_form(self.br)
            self._first_search = False
        #self.logger.debug("Start html: %s", response.read())
        
        fields = {}
        fields.update(self._ref_search)
        fields.update(self._ref_page)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        #self.logger.debug("Choose search form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        
        fields = {}
        fields.update(self._ref_page)
        fields[self._appno_field] = uid
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("Appno form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._submit_control)
        html, url = self._get_html(response)
        #self.logger.debug("Result html: %s", html)
        result = scrapemark.scrape(self._scrape_ids_ref, html, url)
        if result and result.get('records'):
            self._clean_ids(result['records'])
            for r in result['records']:
                if r.get('uid', '') == uid and r.get('control'):
                    self.logger.debug("Scraped control: %s", r['control'])
                    fields = { r['control']: uid }
                    scrapeutils.setup_form(self.br, self._search_form, fields) 
                    #self.logger.debug("Detail form: %s", str(self.br.form))
                    response = scrapeutils.submit_form(self.br)
                    return self._get_html(response)
        return None, None
        

