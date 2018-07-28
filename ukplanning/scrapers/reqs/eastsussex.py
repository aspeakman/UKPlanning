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
from .. import basereq
try:
    from ukplanning import scrapeutils
except ImportError:
    import scrapeutils
import urllib, urlparse
import requests

# SSL error on this site when using normal python 2.7.6/mechanize/urllib2 interface
# so re-engineered to use requests[security] and hence urllib3

class EastSussexScraper(basereq.DateReqScraper):

    batch_size = 50 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 50 # start this number of days ago when gathering current ids
    min_id_goal = 200 # min target for application ids to fetch in one go
    
    _authority_name = 'EastSussex'
    #_date_from_field = { 'day': 'ctl00$content$fromDay', 'month': 'ctl00$content$fromMonth', 'year': 'ctl00$content$fromYear', }
    #_date_to_field = { 'day': 'ctl00$content$toDay', 'month': 'ctl00$content$toMonth', 'year': 'ctl00$content$toYear', }
    #_search_form = '1'
    #_search_fields = { 'ctl00$content$search': 'byDate' }
    #_submit_control = 'ctl00$content$btnSearch'
    
    _date_from_field = 'sd'
    _date_to_field = 'ed'
    _search_fields = { 'typ': 'dmw_planning' }
    #_link_next = 'Next >'
    _search_url = 'https://apps.eastsussex.gov.uk/environment/planning/applications/register/Search.aspx'
    _results_page = 'Results.aspx'
    _detail_page = 'Detail.aspx'
    _scrape_max_recs = '<div class="pagingResultsInContext"> <span /> of {{ max_recs }} applications </div>'
    _scrape_ids = """
    <section>
        {* <dl class="itemDetail"> 
            <dt> Reference: </dt> <dd > 
            <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </dd> 
            <dt> Date: </dt> <dd> {{ [records].date_received }} </dd>
          </dl>
        *}
    </section>
    """
    _scrape_oneid = """
    <article>
        <span id="ctl00_content_lblRefNo"> {{ uid }} </span>
    </article>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <article> {{ block|html }} </article>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <span id="ctl00_content_lblRefNo"> {{ reference }} </span>
    <span id="ctl00_content_lblAddress"> {{ address }} </span>
    <span id="ctl00_content_lblProposal"> {{ description }} </span>
    <span id="ctl00_content_lblRecievedDate"> {{ date_validated }} </span>
    """ # note spelling mistake and that the 'recieved' date is actually the date_validated (after date received)
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<h2 id="ctl00_content_typeTitle"> {{ application_type }} </h2>',
    '<span id="ctl00_content_lblParish"> {{ parish }} </span>',
    '<span id="ctl00_content_lblDistrict"> {{ district }} </span>',
    '<span id="ctl00_content_lblElectoralDivision"> {{ ward_name }} </span>',
    '<span id="ctl00_content_lblConsultationStart"> {{ consultation_start_date }} </span>', 
    '<span id="ctl00_content_lblConsultationEnd"> {{ consultation_end_date }} </span>',
    '<span id="ctl00_content_lblApplicant"> {{ applicant_name }} </span>',
    '<span id="ctl00_content_lblAgent"> {{ agent_name }} </span>',
    '<span id="ctl00_content_lblStatus"> {{ status }} </span>',
    '<span id="ctl00_content_lblContactOfficer"> {{ case_officer }} </span>',
    '<span id="ctl00_content_lblDecisionDate"> {{ decision_date }} </span>',
    '<span id="ctl00_content_lblDecision"> {{ decision }} </span>',
    '<a id="ctl00_content_hlComment" href="{{ comment_url|abs }}"> </a>',
    ]
    detail_tests = [
        { 'uid': 'LW/684/CM', 'len': 16 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '03/09/2012', 'to': '23/10/2012', 'len': 16 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 },
        { 'from': '12/07/2012', 'to': '12/07/2012', 'len': 1 },
    ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        
        #response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s", response.read())
        
        fields = {}
        fields.update(self._search_fields)
        #dfrom = date_from.strftime('X%d/X%m/%Y').replace('X0','X').replace('X','')
        #date_parts = dfrom.split('/')
        #fields[self._date_from_field['day']] = [ date_parts[0] ]
        #fields[self._date_from_field['month']] = [ date_parts[1] ]
        #fields[self._date_from_field['year']] = [ date_parts[2] ]
        #dto = date_to.strftime('X%d/X%m/%Y').replace('X0','X').replace('X','')
        #date_parts = dto.split('/')
        #fields[self._date_to_field['day']] = [ date_parts[0] ]
        #fields[self._date_to_field['month']] = [ date_parts[1] ]
        #fields[self._date_to_field['year']] = [ date_parts[2] ]
        #scrapeutils.setup_form(self.br, self._search_form, fields)
        #self.logger.debug("ID batch form: %s", str(self.br.form))
        #response = scrapeutils.submit_form(self.br, self._submit_control)
        
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        self.logger.debug("ID batch fields: %s", str(fields))
        result_url = urlparse.urljoin(self._search_url, self._results_page)
        response = self.rs.get(result_url + '?' + urllib.urlencode(fields), timeout=self._timeout) 
        
        html = response.text
        #self.logger.debug("ID batch page html: %s", html)
        try:
            result = scrapemark.scrape(self._scrape_max_recs, html)
            if result:
                max_recs = int(result['max_recs'])
            else:
                max_recs = 1
        except:
            max_recs = 1
        
        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        while response and len(final_result) < max_recs and page_count < max_pages:
            url = response.url
            #self.logger.debug("ID batch page html: %s", html)
            result = scrapemark.scrape(self._scrape_ids, html, url) 
            if result and result.get('records'):
                page_count += 1
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            else:
                result = scrapemark.scrape(self._scrape_oneid, html, url) # note can sometimes return just a single full application
                if result and result.get('uid'):
                    page_count += 1
                    result['url'] = url
                    result = [ result ]
                    self._clean_ids(result)
                    final_result.extend(result)
                else:
                    self.logger.debug("Empty result after %d pages", page_count)
                    break
            if len(final_result) >= max_recs: break
            try:
                #response = self.br.follow_link(text=self._link_next)
                fields['page'] = str(page_count+1)
                response = self.rs.get(result_url + '?' + urllib.urlencode(fields), timeout=self._timeout)
                #html = response.read()
                html = response.text
            except: # failure to find next page link at end of page sequence here
                self.logger.debug("No next link after %d pages", page_count)
                break
                
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
               
        return final_result
        
    def get_html_from_uid (self, uid):
        url = urlparse.urljoin(self._search_url, self._detail_page) + '?typ=dmw_planning&appno=' + urllib.quote_plus(uid)
        return self.get_html_from_url(url)
        

