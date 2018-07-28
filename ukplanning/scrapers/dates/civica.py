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
from datetime import timedelta
import urllib, urlparse 

# also see Waltham Forest in separate module - using requests library for SSL
# also see Erewash in separate module - different date selection mechanism

class CivicaScraper(base.DateScraper):

    min_id_goal = 350 # min target for application ids to fetch in one go
    
    _scraper_type = 'Civica'
    _uid_only = True # these can only access applications via uid not url
    _headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 5.1; rv:8.0) Gecko/20100101 Firefox/8.0',
    'Accept-Charset': 'UTF-8,*',
    'Accept': 'text/html',
    'Accept-Language': 'en-gb,en',
    }
    _page_limit = 10
    _search_form = '0'
    _next_form = '0'
    _ref_form = None
    _ref_submit = None
    _alt_ref_field = None # see Waltham Forest
    _search_fields = {}
    _start_url = ''
    _scrape_max_pages = '<table class="scroller"> {* <a> {{ [max_pages] }} </a> *} </table>'

    _scrape_ids = """
    <table title="List of planning applications"> <tbody>
    {* <tr> <td> <input value="{{ [records].uid }}" /> </td> </tr> *}
    </tbody> </table>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <div id="content"> {{ block|html }} </div>"
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = ""
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<tr> <td> L A Ref </td> <td> {{ alt_reference }} </td> </tr>',
    '<tr> <td> Historic Application Reference </td> <td> {{ alt_reference }} </td> </tr>',
    '<tr> <td> Application Reference ERE/ </td> <td> {{ alt_reference }} </td> </tr>',
    '<tr> <td> Postcode </td> <td> {{ postcode }} </td> </tr>',
    '<tr> <td> Officer </td> <td> {{ case_officer }} </td> </tr>',
    '<tr> <td> Case Officer </td> <td> {{ case_officer }} </td> </tr>',
    '<tr> <td> Decision Type </td> <td> {{ decided_by }} </td> </tr>',
    '<tr> <td> Decision Level </td> <td> {{ decided_by }} </td> </tr>',
    '<tr> <td> Decision Date </td> <td> {{ decision_date }} </td> </tr>',
    '<tr> <td> Decision Due Date </td> <td> {{ target_decision_date }} </td> </tr>',
    '<tr> <td> Target Date </td> <td> {{ target_decision_date }} </td> </tr>',
    '<tr> <td> 8 Week Determination Date </td> <td> {{ target_decision_date }} </td> </tr>',
    '<tr> <td> Community </td> <td> {{ parish }} </td> </tr>',
    '<tr> <td> UPRN </td> <td> {{ uprn }} </td> </tr>',
    '<tr> <td> Planning Portal Reference </td> <td> {{ planning_portal_id }} </td> </tr>',
    '<tr> <td> Parish </td> <td> {{ parish }} </td> </tr>',
    '<tr> <td> Ward </td> <td> {{ ward_name }} </td> </tr>',
    '<tr> <td> Case Type </td> <td> {{ application_type }} </td> </tr>',
    '<tr> <td> Application Type </td> <td> {{ application_type }} </td> </tr>',
    '<tr> <td> Status </td> <td> {{ status }} </td> </tr>',
    '<tr> <td> Development Type </td> <td> {{ development_type }} </td> </tr>',
    '<tr> <td> Applicant Name </td> <td> {{ applicant_name }} </td> </tr>',
    '<tr> <td> Agent Name </td> <td> {{ agent_name }} </td> </tr>',
    '<tr> <td> Agent Address </td> <td> {{ agent_address }} </td> </tr>',
    '<tr> <td> Committee Date </td> <td> {{ meeting_date }} </td> </tr>',
    '<tr> <td> Consultation End Date </td> <td> {{ consultation_end_date }} </td> </tr>',
    '<tr> <td> Consultee Finish Date </td> <td> {{ consultation_end_date }} </td> </tr>',
    '<tr> <td> Appeal Date </td> <td> {{ appeal_date }} </td> </tr>',
    '<tr> <td> Appeal Lodged Date </td> <td> {{ appeal_date }} </td> </tr>',
    '<tr> <td> Appeal Start Date </td> <td> {{ appeal_date }} </td> </tr>',
    '<tr> <td> Appeal Decision Date </td> <td> {{ appeal_decision_date }} </td> </tr>',
    '<tr> <td> Appeal Determination Date </td> <td> {{ appeal_decision_date }} </td> </tr>',
    '<tr> <td> Appeal Result </td> <td> {{ appeal_result }} </td> </tr>',
    '<tr> <td> Date Advertised </td> <td> {{ last_advertised_date }} </td> </tr>',
    'Postcode <tr> <td> Area </td> <td> {{ district }} </td> </tr>',
    'Case Officer <tr> <td> Decision </td> <td> {{ decision }} </td> </tr>',
    'Received Date <tr> <td> Decision </td> <td> {{ decision }} </td> </tr>',
    '<tr> <td> Committee </td> <td> {{ decided_by }} </td> </tr> Committee Date',
    'Appeal Lodged <tr> <td> Appeal Decision </td> <td> {{ appeal_result }} </td> </tr>',
    """Hectares <tr> <td> Applicant </td> <td> {{ applicant_name }} </td> </tr>
    <td> Agent </td> <td> {{ agent_name }} </td> </tr>""",
    'Decision Level <tr> <td> Decision </td> <td> {{ decision }} </td> </tr> Decision Date ',
    '<tr> <td> Decision </td> <td> {{ decision }} </td> </tr> <tr> Decision Date </tr> <tr> Decision Level </tr>',
    ]

    def get_id_batch (self, date_from, date_to):
        
        min_window = False
        if date_from == date_to: # note min 2 days, scraper rejects same day requests
            min_window = True
            date_to = date_to + timedelta(days=1)

        if self._start_url:
            response = self.br.open(self._start_url)
            #self.logger.debug("Start html: %s", response.read())
        response = self.br.open(self._search_url)
        #self.logger.debug("Search html: %s", response.read())
        #self.logger.debug(scrapeutils.list_forms(self.br))

        fields = {}
        fields.update(self._search_fields)
        fields [self._date_from_field] = date_from.strftime(self._request_date_format)
        fields [self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s" % str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._search_submit)
        html = response.read()

        #self.logger.debug("Batch html: %s" % html)
        try:
            result = scrapemark.scrape(self._scrape_max_pages, html)
            if isinstance(result['max_pages'], list):
                page_list = [ x for x in result['max_pages'] if x ]
            else:
                page_list = result['max_pages'].split()
            max_pages = int(page_list[-1]) # take the last value
        except:
            max_pages = 1
        self.logger.debug("max pages: %d" % max_pages)

        if self._page_limit and max_pages >= self._page_limit: # limit of 10 pages is the max, so if we hit it then split things up
            if not min_window:
                half_days = int((date_to - date_from).days / 2)
                mid_date = date_from + timedelta(days=half_days)
                result1 = self.get_id_batch(date_from, mid_date)
                result2 = self.get_id_batch(mid_date + timedelta(days=1), date_to)
                result1.extend(result2)
                return result1
            else:
                self.logger.warning("Max %d pages returned on %s - probable missed data" % (self._page_limit, date_from.isoformat()))

        #self.logger.debug(scrapeutils.list_forms(self.br))
        
        page_count = 1
        final_result = []
        while page_count <= max_pages:
            url = response.geturl()
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            else:
                self.logger.debug("Empty result after %d pages", page_count)
                break
            page_count += 1
            if page_count > max_pages:
                break
            try:
                fields = { self._next_field: 'next' }
                scrapeutils.setup_form(self.br, self._next_form, fields)
                self.logger.debug("Next page form: %s" % str(self.br.form))
                response = scrapeutils.submit_form(self.br)
                html = response.read()
            except:
                self.logger.debug("No next form after %d pages", page_count)
                break
            
        return final_result

    def _get_exact_html_from_uid (self, uid):
        if self._start_url:
            response = self.br.open(self._start_url)
        response = self.br.open(self._search_url) 
        #self.logger.debug("ID detail start html: %s", response.read())
        self.logger.debug(scrapeutils.list_forms(self.br))
        fields = {}
        fields.update(self._search_fields)
        fields[self._ref_field] = uid
        if self._ref_form:
            scrapeutils.setup_form(self.br, self._ref_form, fields)
        else:
            scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("Uid form: %s", str(self.br.form))
        if self._ref_submit:
            response = scrapeutils.submit_form(self.br, self._ref_submit)
        else:
            response = scrapeutils.submit_form(self.br, self._search_submit)
        return self._get_html(response)

    def get_html_from_uid (self, uid):
        html, url = self._get_exact_html_from_uid(uid)
        # note return here can be a single uid match page OR list of multiple matches
        result = scrapemark.scrape(self._scrape_ids, html, url)
        if result and result.get('records'):
            self._clean_ids(result['records'])
            for r in result['records']:
                if r.get('uid', '') == uid:
                    return self._get_exact_html_from_uid(r['uid'])
            return None, None
        else:
            return html, url
            
    def _clean_record(self, record):
        super(CivicaScraper, self)._clean_record(record)
        if record.get('alt_reference'):
            record['reference'] = record['alt_reference']
            del record['alt_reference']

class BroxbourneScraper(CivicaScraper): 

    data_start_target = '2001-08-14'
    
    _authority_name = 'Broxbourne'
    _start_url = 'http://planning.broxbourne.gov.uk/Planning/_javascriptDetector_?goto=/Planning/lg/GFPlanningSearch.page%3FParam=lg.Planning%26org.apache.shale.dialog.DIALOG_NAME=gfplanningsearch'
    _search_url = 'http://planning.broxbourne.gov.uk/Planning/lg/plansearch.page?org.apache.shale.dialog.DIALOG_NAME=gfplanningsearch&Param=lg.Planning'

    _date_from_field = '_id65:received_dateFrom'
    _date_to_field = '_id65:received_dateTo'
    _search_submit = '_id65:_id78'
    _ref_field = '_id65:ref_no'
    _next_field = '_id68:scroll_1'

    _scrape_min_data = """
    <td> Reference Number </td> <td> {{ reference }} </td>
    <td> Location </td> <td> {{ address }} </td>
    <td> Proposal </td> <td> {{ description }} </td>
    <td> Received Date </td> <td> {{ date_received }} </td>
    <td> Valid Date </td> <td> {{ date_validated }} </td>
    """
    detail_tests = [
        { 'uid': '07/12/0629/LDC', 'len': 9 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '24/09/2012', 'len': 33 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 9 } ]

class DarlingtonScraper(CivicaScraper): 

    _authority_name = 'Darlington'
    _start_url = 'http://msp.darlington.gov.uk/Planning/_javascriptDetector_?goto=/Planning/lg/GFPlanningSearch.page'
    _search_url = 'http://msp.darlington.gov.uk/Planning/lg/plansearch.page?org.apache.shale.dialog.DIALOG_NAME=gfplanningsearch&Param=lg.Planning'

    _date_from_field = '_id113:SDate5From'
    _date_to_field = '_id113:SDate5To'
    _search_submit = '_id113:_id160'
    _ref_field = '_id113:SDescription'
    _next_field = '_id116:scroll_1'

    _scrape_min_data = """
    <table title="Address Details"> UPRN {* <tr> <td /> <td> {{ [address] }} </td> </tr> *} Area </table>
    <table> <td> Case No </td> <td> {{ reference }} </td>
    <td> Date Received </td> <td> {{ date_received }} </td>
    <td> Date Valid </td> <td> {{ date_validated }} </td>
    <td> Proposal </td> <td> {{ description }} </td> </table>
    """
    detail_tests = [
        { 'uid': '12/00531/FUL', 'len': 15 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 17 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 4 } ]

class DenbighshireScraper(CivicaScraper):

    _authority_name = 'Denbighshire'
    #_start_url = 'http://planning.denbighshire.gov.uk/Planning/_javascriptDetector_?goto=/Planning/lg/GFPlanningWelcome.page'
    _search_url = 'http://planning.denbighshire.gov.uk/Planning/lg/plansearch.page?org.apache.shale.dialog.DIALOG_NAME=gfplanningsearch&Param=lg.Planning'
    _handler = 'etree'
    
    _search_form = '#_id241' 
    _next_form = '#_id240' 
    _date_from_field = '_id241:valid_dateFrom'
    _date_to_field = '_id241:valid_dateTo'
    _search_submit = '_id241:_id269'
    _ref_field = '_id241:ref_no'
    _ref_submit = '_id241:_id263'
    _next_field = '_id240:scroll_1'
    
    _scrape_min_data = """
    <td> Location </td> <td> {{ address }} </td>
    <td> Reference Number </td> <td> {{ reference }} </td>
    <td> Proposal </td> <td> {{ description }} </td>
    <td> Received Date </td> <td> {{ date_received }} </td>
    <td> Valid Date </td> <td> {{ date_validated }} </td>
    """
    detail_tests = [
        { 'uid': '03/2012/1039', 'len': 8 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 19 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 14 } ]

class EastbourneScraper(CivicaScraper):
    # note bad date = 5th feb 2015 = causes a fatal error
    # note bad date = 4th sep 2014 = causes a fatal error
    # also note unresolved problem with some uids returning multiple records for the same field -> fails
    # example 141538, 141612, 150033, 141395

    _authority_name = 'Eastbourne'
    #_start_url = 'http://planning.eastbourne.gov.uk/Planning/_javascriptDetector_?goto=/lg/GFPlanningSearch.page '
    _search_url = 'http://planning.eastbourne.gov.uk/lg/plansearch.page?org.apache.shale.dialog.DIALOG_NAME=gfplanningsearch&Param=APP.Planning'

    _handler = 'etree'
    _search_form = '1'
    _date_from_field = '_id336:ApplicationValidDateFrom'
    _date_to_field = '_id336:ApplicationValidDateTo'
    _search_submit = '_id336:_id397'
    _search_fields = { '_id336_SUBMIT': '1'}
    _ref_field = '_id336:KeyNo'
    _next_field = '_id336:scroll_1'

    _scrape_min_data = """
    <table title="Address Details"> {* <tr> <td /> <td> {{ [address] }} </td> </tr> *} Ward </table>
    <table> <td> Application Reference </td> <td> {{ reference }} </td> Historic
    <td> Description </td> <td> {{ description }} </td> 
    <td> Received Date </td> <td> {{ date_received }} </td>
    <td> Valid Date </td> <td> {{ date_validated }} </td>
    </table>
    """
    detail_tests = [
        { 'uid': '120699', 'len': 14 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '20/09/2012', 'len': 24 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 7 } ]
        
    def get_id_batch (self, date_from, date_to):
        
        min_window = False
        if date_from == date_to: # note min 2 days, scraper rejects same day requests
            min_window = True
            date_to = date_to + timedelta(days=1)
        if date_to.isoformat() == '2015-02-05': # bad date = 5th feb 2015 = causes a fatal error
            date_to = date_to - timedelta(days=1)
        elif date_to.isoformat() == '2014-09-04': # bad date = 4th sep 2014 = causes a fatal error
            date_to = date_to - timedelta(days=1)

        if self._start_url:
            response = self.br.open(self._start_url)
            #self.logger.debug("Start html: %s", response.read())
        response = self.br.open(self._search_url)
        #self.logger.debug("Search html: %s", response.read())
        #self.logger.debug(scrapeutils.list_forms(self.br))

        fields = {}
        fields.update(self._search_fields)
        fields [self._date_from_field] = date_from.strftime(self._request_date_format)
        fields [self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s" % str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._search_submit)
        html = response.read()

        #self.logger.debug("Batch html: %s" % html)
        try:
            result = scrapemark.scrape(self._scrape_max_pages, html)
            if isinstance(result['max_pages'], list):
                page_list = [ x for x in result['max_pages'] if x ]
            else:
                page_list = result['max_pages'].split()
            max_pages = int(page_list[-1]) # take the last value
        except:
            max_pages = 1
        self.logger.debug("max pages: %d" % max_pages)

        if self._page_limit and max_pages >= self._page_limit: # limit of 10 pages is the max, so if we hit it then split things up
            if not min_window:
                half_days = int((date_to - date_from).days / 2)
                mid_date = date_from + timedelta(days=half_days)
                result1 = self.get_id_batch(date_from, mid_date)
                result2 = self.get_id_batch(mid_date + timedelta(days=1), date_to)
                result1.extend(result2)
                return result1
            else:
                self.logger.warning("Max %d pages returned on %s - probable missed data" % (self._page_limit, date_from.isoformat()))

        #self.logger.debug(scrapeutils.list_forms(self.br))
        
        page_count = 1
        final_result = []
        while page_count <= max_pages:
            url = response.geturl()
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            else:
                self.logger.debug("Empty result after %d pages", page_count)
                break
            page_count += 1
            if page_count > max_pages:
                break
            try:
                fields = { self._next_field: 'next' }
                scrapeutils.setup_form(self.br, self._next_form, fields)
                self.logger.debug("Next page form: %s" % str(self.br.form))
                response = scrapeutils.submit_form(self.br)
                html = response.read()
            except:
                self.logger.debug("No next form after %d pages", page_count)
                break
            
        return final_result

class HarrowScraper(CivicaScraper):

    _authority_name = 'Harrow'
    _search_url = 'http://www.harrow.gov.uk/planningsearch/lg/plansearch.page?org.apache.shale.dialog.DIALOG_NAME=planningsearch&Param=lg.Planning&searchType=quick'
    
    _handler = 'etree'
    _search_form = '4'
    _ref_form = '1'
    _next_form = '0'
    _date_from_field = '_id165:SDate2From'
    _date_to_field = '_id165:SDate2To'
    _search_submit = '_id165:_id253'
    _ref_submit = '_id144:_id246'
    _ref_field = '_id144:SDescription'
    _next_field = '_id61:scroll_2'

    _scrape_max_pages = '<div class="scroller"> {{ max_pages }} </div>'

    _scrape_ids = """
    <table title="List of planning applications"> <tbody>
    {* <tr> <td> {{ [records].uid }} </td> </tr>
    *}
    </tbody> </table>"""
    _scrape_multi_ids = """
    <table title="List of planning applications"> <tbody>
    {* <tr> <td> {{ [records].uid }} </td> 
    <td/> <td/> <td/> <td/> <td/> <td/> <td/> 
    <td> {{ [records].postcode }} </td>
    <td> <input id="{{ [records].submit }}" /> </td> </tr>
    *}
    </tbody> </table>"""
    _scrape_data_block = """
    <form id="_id61"> {{ block|html }} </form>"
    """
    _scrape_min_data = """
    <table> Application Address {* <tr> <td /> <td> {{ [address] }} </td> </tr> *} Ward </table>
    <table> <td> Application Number </td> <td> {{ reference }} </td>
    <td> Date Registered </td> <td> {{ date_validated }} </td>
    <td> Proposal </td> <td> {{ description }} </td> </table>
    """
    detail_tests = [
        { 'uid': 'P/2633/12/4721', 'len': 12 },
        { 'uid': 'P/1338/05/DCO', 'len': 14 }, # two copies of the uid
        { 'uid': 'P/3270/16', 'len': 14 } ] # two copies of the uid
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 61 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 57 } ]
        
    # Harrow can return multiple matching records for one uid
    def get_html_from_uid (self, uid):
        html, url = self._get_exact_html_from_uid(uid)
        # note return here can be a single uid match page OR list of multiple matches
        result = scrapemark.scrape(self._scrape_multi_ids, html, url)
        if result and result.get('records'):
            self._clean_ids(result['records'])
            for r in result['records']:
                if r.get('uid', '') == uid and r.get('submit') and r.get('postcode'):
                    scrapeutils.setup_form(self.br, self._next_form)
                    self.logger.debug("Multi id page form: %s" % str(self.br.form))
                    response = scrapeutils.submit_form(self.br, r['submit'])
                    return self._get_html(response)
            r = result['records'][0]
            if r.get('uid', '') == uid and r.get('submit'):
                scrapeutils.setup_form(self.br, self._next_form)
                self.logger.debug("Multi id page form: %s" % str(self.br.form))
                response = scrapeutils.submit_form(self.br, r['submit'])
                return self._get_html(response)
            return None, None
        else:
            return html, url

"""class MaldonScraper(CivicaScraper): now Idox

    _authority_name = 'Maldon'
    _start_url = 'http://myplan80.maldon.gov.uk/Planning/_javascriptDetector_?goto=/Planning/lg/GFPlanningWelcome.page'
    _search_url = 'http://myplan80.maldon.gov.uk/Planning/lg/plansearch.page?org.apache.shale.dialog.DIALOG_NAME=gfplanningsearch&Param=lg.Planning'
    
    _date_from_field = '_id61:SDate1From'
    _date_to_field = '_id61:SDate1To'
    _search_submit = '_id61:_id105'
    _ref_field = '_id61:SDescription'
    _next_field = '_id60:scroll_1'

    _scrape_data_block = ""
    <div class="bodycontent"> {{ block|html }} </div>"
    ""
    _scrape_min_data = ""
    <table title="Address Details"> UPRN {* <tr> <td /> <td> {{ [address] }} </td> </tr> *} Area </table>
    <table> <td> Case No </td> <td> {{ reference }} </td>
    <td> Date Received </td> <td> {{ date_received }} </td>
    <td> Date Valid </td> <td> {{ date_validated }} </td>
    <td> Proposal </td> <td> {{ description }} </td> </table>
    ""
    detail_tests = [
        { 'uid': '12/00358/FUL', 'len': 16 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 33 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 7 } ]"""

"""class NorthamptonScraper(CivicaScraper): now JSON interface

    _authority_name = 'Northampton'
    #_start_url = 'http://planning.northamptonboroughcouncil.com/Planning/_javascriptDetector_?goto=/Planning/lg/GFPlanningSearch.page%3FParam=lg.Planning%26org.apache.shale.dialog.DIALOG_NAME=gfplanningsearch'
    _search_url = 'http://planning.northamptonboroughcouncil.com/Planning/lg/GFPlanningSearch.page?Param=lg.Planning&org.apache.shale.dialog.DIALOG_NAME=gfplanningsearch'

    _search_form = '1'
    _next_form = '1'
    _date_from_field = '_id119:received_dateFrom'
    _date_to_field = '_id119:received_dateTo'
    _search_submit = '_id119:_id212'
    _ref_field = '_id119:ref_no'
    _next_field = '_id122:scroll_1'

    _scrape_min_data = ""
    <td> Reference Number </td> <td> {{ reference }} </td>
    <td> Proposal </td> <td> {{ description }} </td>
    <td> Received Date </td> <td> {{ date_received }} </td> 
    <td> Valid Date </td> <td> {{ date_validated }} </td> 
    <td> Location </td> <td> {{ address }} </td>
    ""
    detail_tests = [
        { 'uid': 'N/2012/0791', 'len': 11 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 23 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 10 } ]"""

"""class PendleScraper(CivicaScraper): now Idox
    _authority_name = 'Pendle'
    _start_url = 'http://planning.pendle.gov.uk/Planning/lg/GFPlanningSearch.page'
    _search_url = 'http://planning.pendle.gov.uk/Planning/lg/plansearch.page?org.apache.shale.dialog.DIALOG_NAME=gfplanningsearch&Param=lg.Planning'
    
    _date_from_field = '_id96:SDate1From'
    _date_to_field = '_id96:SDate1To'
    _search_submit = '_id96:_id139'
    _ref_field = '_id96:SDescription'
    _next_field = '_id99:scroll_1'

    _scrape_min_data = ""
    <table title="Address Details"> {* <tr> <td /> <td> {{ [address] }} </td> </tr> *} </table>
    <table> <td> Case Reference </td> <td> {{ reference }} </td>
    <td> Proposal/Details </td> <td> {{ description }} </td>
    <td> Date Registered </td> <td> {{ date_validated }} </td> </table>
    ""
    detail_tests = [
        { 'uid': '13/12/0352P', 'len': 14 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 94 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 45 } ]"""

class StAlbansScraper(CivicaScraper):

    _authority_name = 'StAlbans'
    #_start_url = 'http://planning.stalbans.gov.uk/Planning/_javascriptDetector_?goto=/Planning/lg/GFPlanningWelcome.page'
    _search_url = 'http://planning.stalbans.gov.uk/Planning/lg/plansearch.page?org.apache.shale.dialog.DIALOG_NAME=gfplanningsearch&Param=lg.Planning'
    
    _date_from_field = '_id209:received_dateFrom'
    _date_to_field = '_id209:received_dateTo'
    _search_submit = '_id209:_id262'
    _ref_field = '_id209:ref_no'
    _next_field = '_id212:scroll_1'

    _scrape_min_data = """
    <td> Application Reference </td> <td> {{ reference }} </td>
    <td> Location </td> <td> {{ address }} </td>
    <td> Proposal </td> <td> {{ description }} </td>
    <td> Received Date </td> <td> {{ date_received }} </td> 
    <td> Registration Date </td> <td> {{ date_validated }} </td> 
    """
    detail_tests = [
        { 'uid': '5/2012/2091', 'len': 15 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 62 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 24 } ]

class WrexhamScraper(CivicaScraper): 

    _authority_name = 'Wrexham'
    #_start_url = 'http://planning.wrexham.gov.uk/Planning/_javascriptDetector_?goto=/Planning/lg/GFPlanningSearch.page'
    _search_url = 'http://planning.wrexham.gov.uk/Planning/lg/plansearch.page?org.apache.shale.dialog.DIALOG_NAME=gfplanningsearch&Param=lg.Planning'
    
    _date_from_field = '_id421:SDate1From'
    _date_to_field = '_id421:SDate1To'
    _search_form = '2'
    _next_form = '2'
    _search_submit = '_id421:_id432'
    _ref_field = '_id421:SDescription'
    _next_field = '_id424:scroll_1'

    _scrape_min_data = """
    <table title="Address Details"> {* <tr> <td /> <td> {{ [address] }} </td> </tr> *} Community </table>
    <table> <td> Case Number </td> <td> {{ reference }} </td>
    <td> Received Date </td> <td> {{ date_received }} </td>
    <td> Proposed development </td> <td> {{ description }} </td> </table>
    """
    detail_tests = [
        { 'uid': 'P/2011/0574', 'len': 9 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 28 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 3 } ]





    




