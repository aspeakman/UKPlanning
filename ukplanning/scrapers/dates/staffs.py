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
from datetime import datetime, timedelta
import urllib

# note the uid for this authority can have significant space(s) in it which we replace with underscore(s) in results

class StaffordshireScraper(base.DateScraper):

    min_id_goal = 250
    batch_size = 21 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 21 # start this number of days ago when gathering current ids
    #data_start_target = 681
    
    _authority_name = 'Staffordshire'
    _search_url = 'http://apps.staffordshire.gov.uk/CPLand/Search.aspx'
    
    #_date_from_field = 'ctl00$ContentPlaceHolder1$pcSearchControls$dteReceivedDateFrom'
    _date_from_field = 'ctl00_ContentPlaceHolder1_pcSearchControls_dteReceivedDateFrom_Raw'
    #_date_to_field = 'ctl00$ContentPlaceHolder1$pcSearchControls$dteReceivedDateTo'
    _date_to_field = 'ctl00_ContentPlaceHolder1_pcSearchControls_dteReceivedDateTo_Raw'
    _ref_field = 'ctl00$ContentPlaceHolder1$pcSearchControls$txtApplicationNo'
    _search_fields = { '__EVENTTARGET': '', '__EVENTARGUMENT': '',
         #'ctl00$ContentPlaceHolder1$cbResultsPerPage$DDD$L': '30',
         #'ctl00$ContentPlaceHolder1$pcSearchControls$btnSubmitAdvancedSearch': 'Search',
         #'ctl00$ContentPlaceHolder1$pcSearchControls$cbCategory': 'All',
         #'ctl00$ContentPlaceHolder1$sm': 'ctl00$ContentPlaceHolder1$upnlSearch|ctl00$ContentPlaceHolder1$pcSearchControls$btnSubmitAdvancedSearch',  
         #'ctl00_ContentPlaceHolder1_pcSearchControls_dteDecisionDateFrom_Raw': 'N',
         #'ctl00_ContentPlaceHolder1_pcSearchControls_dteDecisionDateTo_Raw': 'N',
         #'ctl00_ContentPlaceHolder1_pcSearchControlsATI': '1',
         #'ctl00_ContentPlaceHolder1_pcSearchControls_cbCategory_VI': '',
         #'ctl00_ContentPlaceHolder1_pcSearchControls_cbDistanceFromPostCode_VI': '1',
         #'ctl00_ContentPlaceHolder1_pcSearchControls_cbResultsPerPage_VI': '30',
    }
    _search_form = 'aspnetForm'
    _search_submit = 'ctl00$ContentPlaceHolder1$pcSearchControls$btnSubmitAdvancedSearch'
    _next_fields = { '__EVENTTARGET': '', '__EVENTARGUMENT': '',
        #'ctl00$ContentPlaceHolder1$sm': 'tctl00$ContentPlaceHolder1$upnlSearch',
        #'ctl00$ContentPlaceHolder1$sm': 'ctl00$ContentPlaceHolder1$upnlSearch|ctl00$ContentPlaceHolder1$imgButtonNext',
        #'ctl00$ContentPlaceHolder1$imgButtonNext.x': '11',
        #'ctl00$ContentPlaceHolder1$imgButtonNext.y': '10',
    }
    _next_submit = 'ctl00$ContentPlaceHolder1$imgButtonNext'
    _request_date_format = '%s'
    _rec_limit = 5
    _scrape_state = """
        <input id="__VIEWSTATE" value="{{ viewstate }}" />
        <input id="__EVENTVALIDATION" value="{{ eventvalidation }}" />
    """
    
    _scrape_ids = """
    <div id="ctl00_ContentPlaceHolder1_pnlResultRows">
    {* <div class="resultsrow"> <p> Application No: {{ [records].uid }} | </p>
    <a href="{{ [records].url|abs }}" /> </div> *}
    </div>
    """
    _scrape_max_recs = '<strong> Total matches for search: {{ max_recs }} </strong>'
    #_scrape_next_submit = '<input class="rgPageNext" name="{{ next_submit }}">'
    _scrape_data_block = """
    <form id="aspnetForm"> {{ block|html }} </form>
    """
    _scrape_min_data = """
    <tr> <td> Application No. </td> <td> {{ reference }} </td> </tr>
    <tr> <td> Location </td> <td> {{ address }} </td> </tr>
    <tr> <td> Proposal </td> <td> {{ description }} </td> </tr>
    <tr> <td> Received </td> <td> {{ date_received }} </td> </tr>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<tr> <td> Status </td> <td> {{ status }} </td> </tr>',
    '<tr> <td> Type </td> <td> {{ application_type }} </td> </tr>',
    '<tr> <td> Case Officer </td> <td> {{ case_officer }} </td> </tr>',
    '<tr> <td> Applicant </td> <td> {{ applicant_address }} </td> </tr>',
    '<tr> <td> Agent </td> <td> {{ agent_address }} </td> </tr>',
    '<tr> <td> Target </td> <td> {{ target_decision_date }} </td> </tr>',
    """<tr> Decision and Date </tr>
    <tr> <td> Committee Decision </td> <td> {{ [decision] }} </td> </tr>
    <tr> <td> Delegated Decision </td> <td> {{ [decision] }} </td> </tr>
    <tr> <td> Decision Date </td> <td> {{ decision_date }} </td> </tr>
    <tr> County Decisions </tr>""",
    '<a href="https://apps2.staffordshire.gov.uk/web/OnTheMap/planning?x={{easting}}&amp;amp;y={{northing}}&amp;amp;sr=27700&amp;amp;scale=10000"> View Map </a>',
    '<tr> <td> Site Notice Posted </td> <td> {{ site_notice_start_date }} </td> </tr>',
    '<tr> <td> Comments By </td> <td> {{ comment_date }} </td> </tr>',
    '<tr> <td> Press Advert Pub </td> <td> {{ last_advertised_date }} </td> </tr>',
    '<tr> <td> Committee Date </td> <td> {{ meeting_date }} </td> </tr>',
    '<tr> <td> Appeal Type </td> <td> {{ appeal_type }} </td> </tr>',
    '<tr> <td> Appeal Decision </td> <td> {{ appeal_result }} </td> </tr>',
    """<tr> <td> Appeal Hearing Date </td> <td> {{ appeal_date }} </td> </tr>
    <tr> <td> Received </td> <td> {{ appeal_date }} </td> </tr>
    <tr> <td> Date of Decision </td> <td> {{ appeal_decision_date }} </td> </tr>""",
    ]
    detail_tests = [
        { 'uid': 'N.12/08', 'len': 15 },
        { 'uid': 'ES.12/12_D2', 'len': 15 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 1 },
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 7 },
         ]
    
    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        html = response.read()
        url = response.geturl()
        #self.logger.debug("Start html: %s", html)
        
        #result = scrapemark.scrape(self._scrape_state, html)
        
        fields = {}
        fields.update(self._search_fields)
        #fields['__VIEWSTATE'] = result.get('viewstate', '')
        #fields['__EVENTVALIDATION'] = result.get('eventvalidation', '')
        fromstamp = (datetime(date_from.year, date_from.month, date_from.day) - datetime(1970,1,1)).total_seconds()
        self.logger.debug("Timestamp from: %f" % fromstamp)
        fields[self._date_from_field] = str(int(fromstamp*1000))
        tostamp = (datetime(date_to.year, date_to.month, date_to.day) - datetime(1970,1,1)).total_seconds()
        self.logger.debug("Timestamp to: %f" % tostamp)
        fields[self._date_to_field] = str(int(tostamp*1000))
        #fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        #fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._search_submit)
        #self.logger.debug("Form fields: %s", str(fields))
        #response = self.br.open(url, urllib.urlencode(fields))
        html = response.read()
        
        try:
            result = scrapemark.scrape(self._scrape_max_recs, html)
            max_recs = int(result['max_recs'])
        except:
            max_recs = 0
            
        if max_recs > self._rec_limit: # limit of 5 records is the max, so if we hit it then split things up
            if date_to > date_from:
                half_days = int((date_to - date_from).days / 2) # rounds toward zero
                mid_date = date_from + timedelta(days=half_days)
                result1 = self.get_id_batch(date_from, mid_date)
                result2 = self.get_id_batch(mid_date + timedelta(days=1), date_to)
                result1.extend(result2)
                return result1
            else:
                self.logger.warning("%d records (>max %d) returned on %s - missed data" % (max_recs, self._rec_limit, date_from.isoformat()))
        
        #page_count = 0
        #max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        while html and len(final_result) < max_recs:
            url = response.geturl()
            #self.logger.debug("Batch html: %s" % html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                #page_count += 1
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            """ commented out because next page functionality does not work via mechanize when doing date search
            else:
                self.logger.debug("Empty result after %d pages", page_count)
                break
            if len(final_result) >= max_recs: break
            try:
                scrapeutils.setup_form(self.br, self._search_form, self._next_fields)
                for control in self.br.form.controls:
                    if (control.type == "submit" or control.type == "image") and control.name <> self._next_submit:
                        control.disabled = True
                self.logger.debug("ID next form: %s", str(self.br.form))
                response = scrapeutils.submit_form(self.br, self._next_submit)
                html = response.read()
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next form after %d pages", page_count)
                break"""
        
        #if page_count >= max_pages:
        #    self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
        
        return final_result
        
    # post process a set of uid/url records: gets the uid from the url
    def _clean_record(self, record):
        if record.get('uid'):    
            record['uid'] = record['uid'].strip().replace(' ', '_')
        super(StaffordshireScraper, self)._clean_record(record)
        
    def get_html_from_uid (self, uid):
        response = self.br.open(self._search_url)
        #self.logger.debug("ID detail start html: %s", response.read())
        fields = {}
        fields.update(self._search_fields)
        fields[self._ref_field] = uid.replace('_', ' ')
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("Get UID form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._search_submit)
        html, url = self._get_html(response)
        #self.logger.debug("Ref html: %s", html)
        result = scrapemark.scrape(self._scrape_ids, html, url)
        if result and result.get('records'):
            self._clean_ids(result['records'])
            for rr in result['records']:
                if rr.get('uid', '') == uid and rr.get('url'):
                    return self.get_html_from_url(rr['url'])
        return None, None 
        

