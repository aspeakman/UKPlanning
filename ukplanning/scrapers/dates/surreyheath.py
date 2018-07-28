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
import urllib
import re

# also see Elmbridge and Astun

class SurreyHeathScraper(base.DateScraper):

    min_id_goal = 300 # min target for application ids to fetch in one go
    
    _authority_name = 'SurreyHeath'
    _search_url = 'http://isharemaps.surreyheath.gov.uk/ishare54/custom/planning/?template=DevelopmentControlSearchAdvanced.tmplt&requestType=parseTemplate'
    #_page_url = "http://isharemaps.surreyheath.gov.uk/ishare54/custom/planning/?requesttype=parsetemplate&template=DevelopmentControlResults.tmplt&filter=%%5eREGDATE%%5e+between+%%27%s%%27+AND+%%27%s%%27%%5e&pagerecs=10&useSearch=true&order=REGDATE:DESCENDING&pageno=%d&maxrecords=300&basepage=default.aspx&backurl=%%3Ftemplate%%3DDevelopmentControlSearchAdvanced.tmplt%%26requestType%%3DparseTemplate"
    _page_url = "http://isharemaps.surreyheath.gov.uk/ishare54/custom/planning/?pageno=%d&pagerecs=10&maxrecords=300&template=DevelopmentControlResults.tmplt&requestType=parseTemplate&usesearch=true&order=REGDATE%%3ADESCENDING&q%%3ALIKE=&APPNTYPE%%3ASRCH=&WARDNAME%%3ASRCH=&REGDATE%%3AFROM%%3ADATE=%s&REGDATE%%3ATO%%3ADATE=%s&DCNDATE%%3AFROM%%3ADATE=&DCNDATE%%3ATO%%3ADATE=&APLSTARTDATE%%3AFROM%%3ADATE=&APLSTARTDATE%%3ATO%%3ADATE=&APLDCNDATE%%3AFROM%%3ADATE=&APLDCNDATE%%3ATO%%3ADATE="
    _ref_url = "http://isharemaps.surreyheath.gov.uk/ishare54/custom/planning?pageno=1&pagerecs=10&maxrecords=100&template=DevelopmentControlResults.tmplt&requestType=parseTemplate&usesearch=true&order=REGDATE%%3ADESCENDING&q%%3ALIKE=%s&APPNTYPE%%3ASRCH=&WARDNAME%%3ASRCH=&REGDATE%%3AFROM%%3ADATE=&REGDATE%%3ATO%%3ADATE=&DCNDATE%%3AFROM%%3ADATE=&DCNDATE%%3ATO%%3ADATE=&APLSTARTDATE%%3AFROM%%3ADATE=&APLSTARTDATE%%3ATO%%3ADATE=&APLDCNDATE%%3AFROM%%3ADATE=&APLDCNDATE%%3ATO%%3ADATE="
    _action_url = 'http://isharemaps.surreyheath.gov.uk/ishare54/custom/planning'
    
    _handler = 'etree' 
    _date_from_field = 'REGDATE:FROM:DATE'
    _date_to_field = 'REGDATE:TO:DATE'
    _search_form = '1'
    _scrape_ids = """
    <h2> Search Results </h2>
    {* <div>
    <a href="{{ [records].url|abs }}"> {{ [records].uid }} - </a> 
    </div> *}
    <strong> Pages: </strong>
    """
    _next_page = 'Next &gt;'
    _scrape_next = '<div class="atPageNextPrev"> Previous <a href="{{ next_link }}"> Next </a> </div>'
    _ref_field = 'q:LIKE'
    
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <div id="dcDetails"> {{ block|html }} </div>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <dt> Application Reference: </dt> <dd> {{ reference }} </dd>
    <dt> Address: </dt> <dd> {{ address }} </dd>
    <dt> Proposal: </dt> <dd> {{ description }} </dd>
    <dt> Date received: </dt> <dd> {{ date_received }} </dd>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<dt> Registration </dt> <dd> {{ date_validated }} </dd>',
    '<dt> Planning Portal Reference </dt> <dd> {{ planning_portal_id }} </dd>',
    "<dt> Type of Application </dt> <dd> {{ application_type }} </dd>",
    "<dt> Statutory Start </dt> <dd> {{ date_validated }} </dd>",
    "<dt> Case Officer </dt> <dd> {{ case_officer }} </dd>",
    "<dt> Decision Level </dt> <dd> {{ decided_by }} </dd>",
    "<dt> Appeal Received Date </dt> <dd> {{ appeal_date }} </dd>",
    "<dt> Target Date for Decision </dt> <dd> {{ target_decision_date }} </dd>",
    "<dt> Appeal Decision: </dt> <dd> {{ appeal_result }} </dd>",
    "<dt> Earliest Decision Date </dt> <dd> {{ consultation_end_date }} </dd>",
    "<dt> Consultation Period Expires </dt> <dd> {{ consultation_end_date }} </dd>",
    "<dt> Consultation Period Ends </dt> <dd> {{ consultation_end_date }} </dd>",
    "<dt> Status </dt> <dd> {{ status }} </dd>",
    "<dt> Parish </dt> <dd> {{ parish }} </dd>",
    "<dt> Ward </dt> <dd> {{ ward_name }} </dd>",
    "<h3> Decision </h3> <dt> Decision: </dt> <dd> {{ decision }} </dd>",
    "<dt> Comments </dt> <dd> {{ comment_date }} </dd>",
    "<dt> Consultation Start Date </dt> <dd> {{ consultation_start_date }} </dd>",
    "<dt> Consultation Period Starts </dt> <dd> {{ consultation_start_date }} </dd>",
    "<dt> Date from when comments </dt> <dd> {{ consultation_start_date }} </dd>",
    "<dt> Site Notice Date </dt> <dd> {{ site_notice_start_date }} </dd>",
    "<dt> Date Decision Made </dt> <dd> {{ decision_date }} </dd>",
    "<dt> Date Decision Despatched </dt> <dd> {{ decision_issued_date }} </dd>",
    "<dt> Decision Issued </dt> <dd> {{ decision_issued_date }} </dd>",
    "<dt> Meeting Date </dt> <dd> {{ meeting_date }} </dd>",
    "<dt> Appeal Received Date </dt> <dd> {{ appeal_date }} </dd>",
    "<dt> Easting/Northing </dt> <dd> {{ easting }}/{{ northing }} </dd>",
    "<dt> Agent: </dt> <dd> <span> {{ agent_name}} </span> {* <span> {{ [agent_address] }} </span> *} </dd>",
    "<dt> Applicant: </dt> <dd> <span> {{ applicant_name}} </span> {* <span> {{ [applicant_address] }} </span> *} </dd>",
    ]
    detail_tests = [
        { 'uid': '12/0607', 'len': 20 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 15 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        #response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s", response.read())

        #fields = {}
        #fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        #fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        #scrapeutils.setup_form(self.br, self._search_form, fields)
        #self.logger.debug("ID batch form: %s", str(self.br.form))
        #response = scrapeutils.submit_form(self.br)
        
        page_count = 0
        
        dfrom = urllib.quote_plus(date_from.strftime(self._request_date_format))
        dto = urllib.quote_plus(date_to.strftime(self._request_date_format))
        url = self._page_url % (page_count + 1, dfrom, dto)
        self.logger.debug("URL: %s", url)
        response = self.br.open(url)
        
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
                url = self._page_url % (page_count + 1, dfrom, dto)
                response = self.br.open(url)
                """result = scrapemark.scrape(self._scrape_next, html, url)
                print result
                if result:
                    response = self.br.open(result['next_link'])
                else:
                    response = self.br.follow_link(text=self._next_page)"""
            except: # failure to find next page link at end of page sequence here
                self.logger.debug("No next link after %d pages", page_count)
                break
                
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
               
        return final_result

    def get_html_from_uid (self, uid):
        response = self.br.open(self._search_url)
        #self.logger.debug("ID detail start html: %s", response.read())
        fields = {  self._ref_field: uid }
        scrapeutils.setup_form(self.br, self._search_form, fields, self._action_url)
        response = scrapeutils.submit_form(self.br)
        #url = self._ref_url % urllib.quote_plus(uid)
        #response = self.br.open(url)
        html, url = self._get_html(response)
        result = scrapemark.scrape(self._scrape_ids, html, url)
        if result and result.get('records'):
            self._clean_ids(result['records'])
            for r in result['records']:
                if r.get('uid', '') == uid and r.get('url'):
                    url = r['url'].replace('/custom/planning/custom/planning', '/custom/planning')
                    self.logger.debug("Scraped url: %s", url)
                    return self.get_html_from_url(url)
        return None, None
            

