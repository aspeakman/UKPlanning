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

# also see Ceredigion

# stops working after 30/8/15 - now Idox

"""class StevenageScraper(base.PeriodScraper):

    data_start_target = '2005-12-01' # gathers id data by working backwards from the current date towards this one
    min_id_goal = 200 # min target for application ids to fetch in one go
    
    _headers = {
    'User-Agent': 'Mozilla/5.0 (Windows; U; MSIE 7.0; Windows NT 6.0; en-US)',
    'Accept-Charset': 'UTF-8,*',
    'Accept': 'text/html',
    'Accept-Language': 'en-gb,en',
    }
    _authority_name = 'Stevenage'
    _comment = 'Inactive from end Aug 2015 - now Idox'
    _uid_only = True # these can only access applications via uid not url
    _period_type = 'Sunday'
    _handler = 'soup'
    _search_form = 'RW'
    _weekly_fields = {  'CTRL:110:_:A': 'WEEKLYLIST' }
    _ref_fields = {  'CTRL:110:_:A': 'REFERENCE' }
    _start_submit = 'CTRL:111:_:B'
    _search_fields = { 'CTRL:122:_:A': 'RECEIVED' }
    _search_date_submit = 'CTRL:123:_:B'
    _search_ref_submit = 'CTRL:118:_:B'
    _page_size = 10
    _next_control = 'CTRL:124:_:E.h'
    _next_fields = { 'CTRL:111:_:B': None, 'CTRL:123:_:B': None, 'CTRL:124:_:E.h': '>'}
    _search_url = 'https://eforms.stevenage.gov.uk/ufs/ufsmain?formid=REGISTER_OF_PLANNING_APPLICATIONS'
    _scrape_max_recs = ""
    <span class="eb-124-tableNavRowInfo"> of {{ max_recs }} records</span>
    ""
    _scrape_ids = ""
    <table class="eb-124-tableContent"> <tr />
        {* <tr>
        <td> <input value="{{ [records].uid }}"> </td>
        </tr> *}
    </table>
    ""
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = ""
    <table class="eb-1-VerticalBoxLayoutSurround"> {{ block|html }} </table>
    ""
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = ""
    <div id="CTID:6:_:A"> {{ reference }} </div>
    <div id="CTID:7:_:A"> {{ address|html }} </div>
    <div id="CTID:9:_:A"> {{ description }} </div>
    <div id="CTID:31:_:A"> {{ date_received }} </div>
    <div id="CTID:35:_:A> {{ date_validated }} </div>
    ""
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<div id="CTID:10:_:A"> {{ application_type }} </div>',
    '<div id="CTID:64:_:A"> {{ decision }} </div>',
    '<div id="CTID:65:_:A"> {{ decided_by }} </div>',
    '<div id="CTID:8:_:A"> {{ ward_name }} </div>',
    '<div id="CTID:11:_:A"> {{ case_officer }} </div>',
    '<div id="CTID:38:_:A"> {{ meeting_date }} </div>',
    '<div id="CTID:66:_:A"> {{ decision_date }} </div>',
    '<div id="CTID:67:_:A"> {{ decision_issued_date }} </div>',
    '<div id="CTID:68:_:A"> {{ decision_published_date }} </div>',
    '<div id="CTID:13:_:A"> {{ status }} </div>',
    '<div id="CTID:33:_:A"> {{ target_decision_date }} </div>',
    '<div id="CTID:44:_:A"> {{ consultation_start_date }} </div>',
    '<div id="CTID:49:_:A"> {{ consultation_end_date }} </div>',
    '<div id="CTID:39:_:A"> {{ neighbour_consultation_start_date }} </div>',
    '<div id="CTID:41:_:A"> {{ neighbour_consultation_end_date }} </div>',
    '<div id="CTID:51:_:A"> {{ last_advertised_date }} </div>',
    '<div id="CTID:53:_:A"> {{ latest_advertisement_expiry_date }} </div>',
    '<div id="CTID:60:_:A"> {{ permission_expires_date }} </div>',
    '<div id="CTID:72:_:A"> {{ associated_application_uid }} </div>',
    '<div id="CTID:73:_:A"> {{ appeal_status }} </div>',
    '<div id="CTID:74:_:A"> {{ appeal_date }} </div>',
    '<div id="CTID:75:_:A"> {{ appeal_result }} </div>',
    '<div id="CTID:76:_:A"> {{ appeal_decision_date }} </div>',
    '<div id="CTID:55:_:A"> {{ site_notice_start_date }} </div>',
    '<div id="CTID:57:_:A"> {{ site_notice_end_date }} </div>',
    ]
    detail_tests = [
        { 'uid': '11/00694/FP', 'len': 22 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'date': '13/09/2012', 'len': 5 }, 
        { 'date': '15/10/2012', 'len': 12 } ]

    def get_id_period (self, this_date):

        final_result = []
        from_dt, to_dt = scrapeutils.inc_dt(this_date, self._period_type)
        
        # open with jscheck page
        response = self.br.open(self._search_url)
        html = response.get_data()
        response.set_data(html.replace('<!--', '')) # remove mismatched html comment mark
        self.br.set_response(response)
        scrapeutils.setup_form(self.br)
        response = scrapeutils.submit_form(self.br)
        
        # start page
        scrapeutils.setup_form(self.br, self._search_form, self._weekly_fields)
        self.logger.debug("Start form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._start_submit)
        
        # date select
        fields = {}
        fields.update(self._search_fields)
        from_dmy_dt = from_dt.strftime('%d/%m/%Y')
        to_dmy_dt = to_dt.strftime('%d/%m/%Y')
        fields ['CTRL:121:_:A'] = from_dmy_dt + '-' + to_dmy_dt
        response = None
        try:
            scrapeutils.setup_form(self.br, self._search_form, fields)
            self.logger.debug("ID batch form: %s", str(self.br.form))
            response = scrapeutils.submit_form(self.br, self._search_date_submit)
        except:
            pass # sometimes the most recent week is not yet available as a selectable option
        if not response: 
            return [], None, None

        html = response.read()
        #self.logger.debug("First page html: %s", html)
        result = scrapemark.scrape(self._scrape_max_recs, html)
        try:
            max_recs = int(result['max_recs'])
        except:
            max_recs = self.page_size

        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        while response and page_count < max_pages and len(final_result) < max_recs:
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
            if len(final_result) >= max_recs: break
            try:
                scrapeutils.setup_form(self.br, self._search_form)
                self.br.form.new_control('submit', self._next_control, {'value':'>'} )
                self.br.form.fixup()
                self.logger.debug("Next page form: %s" % str(self.br.form))
                response = scrapeutils.submit_form(self.br, self._next_control)
                html = response.read()
            except:
                self.logger.debug("No next form after %d pages", page_count)
                break
                
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
        
        return final_result, from_dt, to_dt # weekly scraper - so empty result can be valid

    def get_html_from_uid (self, uid):
        
        # open with jscheck page
        response = self.br.open(self._search_url)
        html = response.get_data()
        response.set_data(html.replace('<!--', '')) # remove mismatched html comment mark
        self.br.set_response(response)
        scrapeutils.setup_form(self.br)
        response = scrapeutils.submit_form(self.br)
        
        # start page
        scrapeutils.setup_form(self.br, self._search_form, self._ref_fields)
        self.logger.debug("Ref form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._start_submit)
        
        # ref search
        fields = {}
        fields ['CTRL:117:_:A'] = uid
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("uid form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._search_ref_submit)
        return self._get_html(response)"""
        
