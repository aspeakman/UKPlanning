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

# also see South Northamptonshire and Bournemouth

class WealdenScraper(base.DateScraper):

    min_id_goal = 250
    
    _authority_name = 'Wealden'
    _search_url = 'http://www.planning.wealden.gov.uk/disclaimer.aspx?returnURL=%2fadvsearch.aspx'
    _date_from_field = 'ctl00$ContentPlaceHolder1$txtDateReceivedFrom$dateInput'
    _date_to_field = 'ctl00$ContentPlaceHolder1$txtDateReceivedTo$dateInput'
    _ref_field = 'ctl00$ContentPlaceHolder1$txtAppNumber'
    _ref_submit = 'ctl00$ContentPlaceHolder1$btnSearch2'
    _search_submit = 'ctl00$ContentPlaceHolder1$btnSearch3'
    _search_fields =  { '__EVENTTARGET': '', '__EVENTARGUMENT': '' }
    _next_submit = 'ctl00$ContentPlaceHolder1$lvResults$RadDataPager1$ctl02$NextButton'
    _request_date_format = '%Y-%m-%d-00-00-00'
    _search_form = 'aspnetForm'
    _scrape_max_pages = '<div class="rdpWrap"> of {{ max_pages }} </div>'

    _scrape_ids = """
    <div id="news_results_list">
    {* <div>
    <h2> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </h2>
    </div> *}
    </div>
    """
    _scrape_data_block = """
    <div id="page-content"> {{ block|html }} </div>
    """
    _scrape_min_data = """
    <span class="applabel"> Application No </span> <p> {{ reference }} </p>
    <span class="applabel"> Proposal </span> <p> {{ description }} </p>
    <span class="applabel"> Received Date </span> <p> {{ date_received }} </p>
    <span class="applabel"> Address </span> <p> {{ address }} </p>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<span class="applabel"> Valid Date </span> <p> {{ date_validated }} </p>',
    '<span class="applabel"> Type </span> <p> {{ application_type }} </p>',
    '<span class="applabel"> Case Officer </span> <p> {{ case_officer }} </p>',
    '<span class="applabel"> Status </span> <p> {{ status }} </p>',
    """<span class="applabel"> Delegated </span> <p> {{ decided_by }} </p>
    <span class="applabel"> Delegated Date </span> <p> {{ meeting_date }} </p>""",
    '<span class="applabel"> Decision Date </span> <p> {{ decision_date }} </p>',
    '<span class="applabel"> Advert Expiry </span> <p> {{ latest_advertisement_expiry_date }} </p>',
    '<span class="applabel"> Neighbour Expiry </span> <p> {{ neighbour_consultation_end_date }} </p>',
    """<span class="applabel"> Site Notice Expiry </span> <p> {{ site_notice_end_date }} </p>
    <span class="applabel"> Decision </span> <p> {{ decision }} </p>""",
    '<span class="applabel"> Issue Date </span> <p> {{ decision_issued_date }} </p>',
    '<span class="applabel"> Ward </span> <p> {{ ward_name }} </p>',
    '<span class="applabel"> Parish </span> <p> {{ parish }} </p>',
    '<span class="applabel"> UPRN </span> <p> {{ uprn }} </p>',
    '<span class="applabel"> Easting </span> <p> {{ easting }} </p>',
    '<span class="applabel"> Northing </span> <p> {{ northing }} </p>',
    ]
    detail_tests = [
        { 'uid': 'WD/2011/1512/LDP', 'len': 18 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 46 },
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 14 } ]
    
    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        
        scrapeutils.setup_form(self.br, self._search_form)
        self.logger.debug("Start form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        
        fields = {}
        fields.update(self._search_fields)
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._search_submit)
        html = response.read()
        
        runaway_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        try:
            result = scrapemark.scrape(self._scrape_max_pages, html)
            max_pages = int(result['max_pages'])
        except:
            max_pages = runaway_pages
            
        page_count = 0
        while html and page_count < max_pages:
            url = response.geturl()
            #self.logger.debug("Batch html: %s" % html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                page_count += 1
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            else:
                self.logger.debug("Empty result after %d pages", page_count)
                break
            if page_count >= max_pages: break
            try:
                scrapeutils.setup_form(self.br, self._search_form)
                self.logger.debug("ID next form: %s", str(self.br.form))
                response = scrapeutils.submit_form(self.br, self._next_submit)
                html = response.read()
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next form after %d pages", page_count)
                break
        
        if page_count >= runaway_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
        
        return final_result
        
    def get_html_from_uid (self, uid):
        response = self.br.open(self._search_url)
        scrapeutils.setup_form(self.br, self._search_form)
        self.logger.debug("Start form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        #self.logger.debug("ID detail start html: %s", response.read())
        fields = { self._ref_field: uid }
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("Get UID form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._ref_submit)
        html, url = self._get_html(response)
        result = scrapemark.scrape(self._scrape_ids, html, url)
        if result and result.get('records'):
            self._clean_ids(result['records'])
            for rr in result['records']:
                if rr.get('uid', '') == uid and rr.get('url'):
                    return self.get_html_from_url(rr['url'])
        return None, None 
        

