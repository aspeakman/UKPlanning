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
import urllib, urlparse

class OcellaScraper(base.DateScraper):

    min_id_goal = 350 # min target for application ids to fetch in one go
    current_span = 20 # start this number of days ago when gathering current ids
    
    _scraper_type = 'Ocella'
    _handler = 'etree' # note definitely need this as HTML is pretty rubbish
    _headers = {
    'Accept-Charset': 'UTF-8,*',
    'Accept': 'text/html',
    'User-Agent': 'Mozilla/5.0 (Windows NT 5.1; rv:7.0.1) Gecko/20100101 Firefox/7.0.1',
    }

    _date_from_field_suffix = '.DEFAULT.START_DATE.01'
    _date_to_field_suffix = '.DEFAULT.END_DATE.01'
    _form_object_suffix = '.DEFAULT.SUBMIT_TOP.01'
    _search_fields =  {
        'p_object_name': '',
        'p_instance': '1',
        'p_event_type': 'ON_CLICK',
        'p_user_args': '',
        }
    _ref_field_suffix = '.DEFAULT.REFERENCE.01'
    _search_form = '0'
    _next_form = '0'
    _request_date_format = '%d-%m-%Y'
    _form_name = ''

    _scrape_ids = """
    <table summary="Printing Table Headers"> <tr />
    {* <tr>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    </tr> *}
    </table>
    """
    _next_page_fields = {  '_request': 'NEXT' }
    _dates_link = 'Milestone Dates'

    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = "<body> {{ block|html }} </body>"
    _scrape_dates_block = "<body> {{ block|html }} </body>"
    # the minimum acceptable valid dataset on the details page
    _scrape_min_data = """
    <th> Application Number </th>
    <td> {{ reference }} </td> <td> {{ date_received }} </td>
    <th> Site </th> <td> {{ address }} </td>
    <th> Proposal </th> <td> {{ description }} </td>
    """
    # other optional parameters that can appear on the details page
    _scrape_optional_data = [
    "<th> Application Number </th> <td /> <td /> <td> {{ status }} </td>",
    "<th> Applicant </th> <td> {{ applicant_name }} </td> <td> {{ agent_name }} </td>",
    "<th> Applicant </th> <td /> <td /> {* <td> {{ [applicant_address] }} </td> <td /> *} <th> Officer </th>",
    "<th> Applicant </th> <td /> <td /> {* <td /> <td> {{ [agent_address] }} </td> *} <th> Officer </th>",
    "<th> Officer </th> <td> {{ case_officer }} </td> <td> {{ consultation_start_date }} </td> <td> {{ comment_date }} </td>",
    "<th> Decision </th> <td> <font> {{ decision }} </font> </td> <td> {{ decision_date }} </td>",
    "<th> Appeal Lodged </th> <td> {{ appeal_date }} </td> <td> {{ appeal_result }} </td> <td> {{ appeal_decision_date }} </td>",
    '<a href="{{ comment_url|abs }}">Comment on this application</a>' ]
    # the minimum acceptable valid dataset on the dates page
    _scrape_min_dates = """
    Received <td> {{ date_received }} </td>
    Validated <td> {{ date_validated }} </td>
    """
    # other optional parameters that can appear on the dates page
    _scrape_optional_dates = [
    "Decision due by <td> {{ target_decision_date }} </td>",
    "Standard Consultation Sent <td> {{ consultation_start_date }} </td>",
    "Advertised in Press Expiry <td> {{ latest_advertisement_expiry_date }} </td>",
    "Advertised Expiry <td> {{ latest_advertisement_expiry_date }} </td>",
    "Committee Meeting <td> {{ meeting_date }} </td>",
    "Appeal Lodged On <td> {{ appeal_date }} </td>",
    "Appeal Decided On <td> {{ appeal_decision_date }} </td>",
    "Permission Expires <td> {{ permission_expires_date }} </td>",
    "Date of Decision <td> {{ decision_date }} </td>",
    "Decision Issued Date <td> {{ decision_issued_date }} </td>",
    "Neighbour Consultations Sent <td> {{ neighbour_consultation_start_date }} </td>",
    "Neighbour Comments Due By <td> {{ neighbour_consultation_end_date }} </td>",
    ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        #self.logger.debug("ID batch start html: %s", response.read())

        fields = {}
        fields.update(self._search_fields)
        fields ['p_object_name'] = self._form_name + self._form_object_suffix
        fields[self._form_name + self._date_from_field_suffix] = date_from.strftime(self._request_date_format)
        fields[self._form_name + self._date_to_field_suffix] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s" % str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        
        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        while response and page_count < max_pages:
            html = response.read()
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
            try:
                scrapeutils.setup_form(self.br, self._next_form, self._next_page_fields)
                self.logger.debug("Next form: %s" % str(self.br.form))
                response = scrapeutils.submit_form(self.br)
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next form after %d pages", page_count)
                break
                
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
                
        return final_result

    def get_html_from_uid (self, uid):
        url = self._applic_url + "?p_arg_names=reference&p_arg_values=" + urllib.quote_plus(uid)
        return self.get_html_from_url(url) 
        
    def _get_details(self, html, this_url):
        """ Scrapes detailed information for one record given html and url 
        - this is an optional hook to allow data from multiple linked pages to be merged """
        result = self._get_detail(html, this_url)
        if 'scrape_error' in result:
            return result
        try:
            response = self.br.follow_link(text=self._dates_link)
            html, url = self._get_html(response)
        except:
            self.logger.warning("No link to dates page found")
        else:
            #self.logger.debug("Html obtained from dates url: %s" % html)
            result2 = self._get_detail(html, url, self._scrape_dates_block, self._scrape_min_dates, self._scrape_optional_dates)
            if 'scrape_error' not in result2:
                result.update(result2)
            else:
                self.logger.warning("No information found on dates page")
        return result
    
"""
class CastlePointScraper(OcellaScraper): # now Idox

    _search_url = 'http://planning.castlepoint.gov.uk/portal/page/portal/CASTLEPOINT/weekly'
    _authority_name = 'CastlePoint'
    _form_name = 'FORM_WEEKLY_LIST'
    _applic_url = 'http://planning.castlepoint.gov.uk/portal/pls/portal/CASTLEWEB.RPT_APPLICATION_DETAILS.SHOW'
    _scrape_ids = ""
    <table summary="Printing Table Headers"> <tr />
    {* <tr>
    <td> {{ [records].ward_name }} </td>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    </tr> *}
    </table>
    ""
    detail_tests = [
        { 'uid': 'CPT/659/12/FUL', 'len': 17 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 23 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]
        """
        
"""class HaveringOldScraper(OcellaScraper): # now see Havering Ocella2 below

    _authority_name = 'HaveringOld'
    _search_url = 'http://planning.havering.gov.uk/portal/page?_pageid=33,1026&_dad=portal&_schema=PORTAL'
    _form_name = 'FORM_APP_SEARCH'
    _search_form = '1'
    _next_form = '1'
    _applic_url = 'http://planning.havering.gov.uk/pls/portal/HAVERWEB.RPT_APPLICATION_DETAILS.SHOW'
    _dates_link = 'Key Application Dates'
    _scrape_ids = ""
    <table summary="Printing Table Headers"> <tr />
    {* <tr>
    <td> {{ [records].ward_name }} </td>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    <td> {{ [records].application_type }} </td>
    </tr> *}
    </table>
    ""
    _scrape_min_data = ""
    <th> Application Number </th>
    <td> {{ reference }} </td> <td> {{ date_received }} </td>
    <th> Location </th> <td> {{ address }} </td>
    <th> Proposal </th> <td> {{ description }} </td>
    ""
    _scrape_optional_data = [
    "<th> Application Number </th> <td /> <td /> <td> {{ status }} </td>",
    ""<th> Applicant </th> <td> {{ applicant_name }} <br/> {{ applicant_address|html }} </td>
    <td> {{ agent_name }} <br/> {{ agent_address|html }} </td>"",
    "<th> Officer </th> <td> {{ case_officer }} </td> <td> {{ consultation_start_date }} </td> <td> {{ comment_date }} </td>",
    "<th> Decision </th> <td> {{ decision }} <br /> </td> <td> {{ decision_date }} </td>",
    "<th> Appeal Lodged </th> <td> {{ appeal_date }} </td> <td> {{ appeal_result }} </td> <td> {{ appeal_decision_date }} </td>",
    '<a href="{{ comment_url|abs }}">Comment on this application</a>' ]
    detail_tests = [
        { 'uid': 'C0005.12', 'len': 17 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 25 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ]"""
        
"""class MiddlesbroughScraper(OcellaScraper): # now Idox

    _authority_name = 'Middlesbrough'
    _search_url = 'http://planserv.middlesbrough.gov.uk/portal/page/portal/MIDDLESBROUGH/WEEKLY'
    _form_name = 'FORM_PLANNING_LIST'
    _applic_url = 'http://planserv.middlesbrough.gov.uk/portal/pls/portal/MIDWEB.RPT_APPLICATION_DETAILS.SHOW'
    _scrape_ids = ""
    <table summary="Printing Table Headers"> <tr />
    {* <tr>
    <td> {{ [records].ward_name }} </td>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    </tr> *}
    </table> </table>
    ""
    detail_tests = [
        { 'uid': 'M/FP/0865/11/P', 'len': 19 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 11 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 } ]"""

"""class NorthEastLincsScraper(OcellaScraper): now Idox

    _authority_name = 'NorthEastLincs'
    _search_url = 'http://planning.nelincs.gov.uk/portal/page/portal/NELINCS/planning'
    _form_name = 'FORM_PLANNING_LIST'
    _search_form = '2'
    _next_form = '0'
    _applic_url = 'http://planning.nelincs.gov.uk/portal/pls/portal/NLWEB.RPT_APPLICATION_DETAILS.SHOW'
    detail_tests = [
        { 'uid': 'DC/695/11/WOL', 'len': 18 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 35 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 9 } ]"""
        
"""class RotherScraper(OcellaScraper):

    _authority_name = 'Rother'
    _search_url = 'http://ocellaweb.rother.gov.uk/portal/page/portal/rother/search'
    _form_name = 'FORM_SEARCH3'
    _search_form = '1'
    _next_form = '1'
    _applic_url = 'http://ocellaweb.rother.gov.uk/portal/pls/portal/ROTHERWEB.RPT_DETAILS.show'

    _scrape_optional_data = [
    "<th> Application Number </th> <td /> <td /> <td> {{ status }} </td>",
    "<th> Applicant </th> <td> {{ applicant_name }} </td> <td> {{ agent_name }} </td>",
    "<th> Applicant </th> <td /> <td /> {* <td> {{ [applicant_address] }} </td> <td /> *} <th> Advertised </th>",
    "<th> Applicant </th> <td /> <td /> {* <td /> <td> {{ [agent_address] }} </td> *} <th> Advertised </th>",
    "<th> Advertised </th> <td> {{ consultation_start_date }} </td> <td> {{ comment_date }} </td>",
    "<th> Decision </th> <td> <font> {{ decision }} </font> </td> <td> {{ decision_date }} </td>",
    "<th> Appeal Lodged </th> <td> {{ appeal_date }} </td> <td> {{ appeal_result }} </td> <td> {{ appeal_decision_date }} </td>",
    '<a href="{{ comment_url|abs }}">Comment on this application</a>' ]
    _scrape_min_dates = ""
    Validated <td> {{ date_validated }} </td>
    ""
    detail_tests = [
        { 'uid': 'RR/2011/1789/P', 'len': 15 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 25 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 12 } ]"""

"""class WorcesterScraper(OcellaScraper):

    _authority_name = 'Worcester'
    batch_size = 21 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 28 # start this number of days ago when gathering current ids
    _search_url = 'http://planningapps.worcester.gov.uk/portal/page/portal/worcester/search'
    _form_name = 'FORM_SEARCH'
    _search_form = '2'
    _next_form = '2'
    _applic_url = 'http://planningapps.worcester.gov.uk/portal/pls/portal/WWEB.RPT_DETAILS2.show'

    _scrape_min_data = ""
    <font> Application Reference </font> <font> {{ reference }} </font>
    <font> Description </font> <font> {{ address }} </font>
    <font> {{ description }} </font>
    <font> Date Started </font> <font> {{ date_received }} </font>
    ""
    _scrape_optional_data = [
    "<font> Current Status </font> <font> {{ status }} </font>",
    "<font> Ward </font> <font> {{ ward_name }} </font>",
    "<font> Agent Details </font> <font> {{ applicant_name }} </font> <font> {{ agent_name }} </font>",
    "<font> Agent Details </font> <font /> <font /> {* <font> {{ [applicant_address] }} </font> <font /> *} <font> Administration Details </font>",
    "<font> Agent Details </font> <font /> <font /> {* <font /> <font> {{ [agent_address] }} </font> *} <font> Administration Details </font>",
    "<font> Officer </font> <font> {{ case_officer }} </font>",
    "<font> Decision Due By </font> <font> {{ target_decision_date }} </font>",
    "<font> End of Consultation </font> <font> {{ consultation_end_date }} </font>",
    ""<font> Committee Date </font> <font> {{ meeting_date }} </font>
    <font> Decision </font> <font> {{ decision }} </font> <font> Decision Date </font> <font> {{ decision_date }} </font>"",
    "<font> Appeal Started </font> <font> {{ appeal_date }} </font>",
    "<font> Appeal Decision Date </font> <font> {{ appeal_decision_date }} </font> <font /> <font> {{ appeal_result }} </font>",
    '<a href="{{ comment_url|abs }}">Comment on this application</a>' ]
    detail_tests = [
        { 'uid': 'P11A0394', 'len': 15 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 16 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]"""

class Ocella2Scraper(base.DateScraper): # alternative form - inherits directly from DateScraper 

    min_id_goal = 300 # min target for application ids to fetch in one go
    current_span = 20 # start this number of days ago when gathering current ids
    
    _scraper_type = 'Ocella2'
    _handler = 'etree' # note definitely need this as HTML is pretty rubbish
    _detail_page = 'planningDetails'
    _date_from_field = 'receivedFrom'
    _date_to_field = 'receivedTo'
    _search_fields = { 'showall': 'showall' }
    _search_form = 'OcellaPlanningSearch'
    _request_date_format = '%d-%m-%y'
    _response_date_format = '%d-%m-%y'
    _scrape_ids = """
    <table /> <table> <tr />
    {* <tr>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    <td /> <td /> <td /> <td> {{ [records].application_type }} </td>
    </tr> *}
    </table>
    """
    _scrape_data_block = '<body> {{ block|html }} </body>'
    _scrape_min_data = """
    <table /> <td> Reference </td> <td> {{ reference }} </td>
    <td> Proposal </td> <td> {{ description }} </td>
    <td> Location </td> <td> {{ address }} </td>
    <td> Received </td> <td> {{ date_received }} </td>
    """
    _scrape_optional_data = [
    "<td> Status </td> <td> {{ status }} </td>",
    "<td> Ward </td> <td> {{ ward_name }} </td>",
    "<td> Parish </td> <td> {{ parish }} </td>",
    "<td> Applicant </td> <td> {{ applicant_address }} </td>",
    "<tr> <td> Agent </td> <td> {{ agent_address }} </td> </tr>",
    "<td> Officer </td> <td> {{ case_officer }} </td>",
    "<td> Decided </td> <td> {{ decision_date }} </td>",
    "<td> Decision By </td> <td> {{ target_decision_date }} </td>",
    "<td> Comment By </td> <td> {{ consultation_end_date }} </td>",
    "<td> Validated </td> <td> {{ date_validated }} </td>",
    '<form name="comment" action="{{ comment_url|abs }}" />',
    ]

    def get_id_batch (self, date_from, date_to):

        response = self.br.open(self._search_url)
        fields = {}
        fields.update(self._search_fields)
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s" % str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        final_result = []
        
        if response: # one long page only, see search fields
            html = response.read()
            url = response.geturl()
            #self.logger.debug("Batch html: %s" % html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            
        return final_result

    def get_html_from_uid (self, uid):
        url = urlparse.urljoin(self._search_url, self._detail_page) + "?from=planningSearch&reference=" + urllib.quote_plus(uid)
        return self.get_html_from_url(url)

class ArunScraper(Ocella2Scraper): # note inherits from Ocella2Scraper

    _authority_name = 'Arun'
    _search_url = 'http://www1.arun.gov.uk/aplanning/OcellaWeb/planningSearch'
    _scrape_ids = """
    <table /> <table> <tr> Reference </tr>
    {* <tr>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    </tr> *}
    </table>
    """
    detail_tests = [
        { 'uid': 'BR/202/12/', 'len': 15 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 30 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 7 } ]
        
class BrecklandScraper(Ocella2Scraper): # note inherits from Ocella2Scraper

    _authority_name = 'Breckland'
    _search_url = 'http://planning.breckland.gov.uk/OcellaWeb/planningSearch'
    
    detail_tests = [
        { 'uid': '3PL/2011/0917/F', 'len': 14 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 30 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 6 } ]
    
"""class BridgendScraper(Ocella2Scraper): # not working now - see GlamBridge custom scraper

    _authority_name = 'Bridgend'
    _search_url = 'http://planpor.bridgend.gov.uk/OcellaWeb/planningSearch'
    _scrape_ids = ""
    <table /> <table> <tr />
    {* <tr>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    <td /> <td /> <td> {{ [records].application_type }} </td>
    </tr> *}
    </table>
    ""
    detail_tests = [
        { 'uid': 'P/11/629/FUL', 'len': 13 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 11 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]"""

class FarehamScraper(Ocella2Scraper): # note inherits from Ocella2Scraper

    _authority_name = 'Fareham'
    _search_url = 'http://eoc.fareham.gov.uk/OcellaWeb/planningSearch'
    _scrape_data_block = '<div id="pnlPageContent"> {{ block|html }} </div>'
    
    detail_tests = [
        { 'uid': 'P/11/0703/FP', 'len': 14 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 24 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 9 } ]

class GreatYarmouthScraper(Ocella2Scraper): # note inherits from Ocella2Scraper

    _authority_name = 'GreatYarmouth'
    _search_url = 'http://planning.great-yarmouth.gov.uk/OcellaWeb/planningSearch'
    #_scrape_data_block = '<div id="planningSearch"> {{ block|html }} </div>'
    
    detail_tests = [
        { 'uid': '06/11/0529/F', 'len': 14 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 14 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 6 } ]
        
class HaveringScraper(Ocella2Scraper): # note inherits from Ocella2Scraper

    _authority_name = 'Havering'
    _search_url = 'http://development.havering.gov.uk/OcellaWeb/planningSearch'
    _scrape_ids = """
    <table rules="rows"> <tr />
    {* <tr>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    </tr> *}
    </table>
    """
    
    detail_tests = [
        { 'uid': 'C0005.12', 'len': 14 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 25 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ]

class HillingdonScraper(Ocella2Scraper): # note inherits from Ocella2Scraper

    _authority_name = 'Hillingdon'
    batch_size = 10
    _search_url = 'http://planning.hillingdon.gov.uk/OcellaWeb/planningSearch'
    _scrape_ids = """
    <table /> <table> <tr />
    {* <tr>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    </tr> *}
    </table>
    """
    _ref_field = 'reference'
    
    detail_tests = [
        { 'uid': '64345/APP/2011/1945', 'len': 14 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 59 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 9 } ]

    def get_html_from_uid (self, uid):
        response = self.br.open(self._search_url)
        #self.logger.debug("ID detail start html: %s", response.read())
        fields = {}
        fields.update(self._search_fields)
        fields[self._ref_field] = uid
        scrapeutils.setup_form(self.br, self._search_form, fields)
        response = scrapeutils.submit_form(self.br)
        html, url = self._get_html(response)
        result = scrapemark.scrape(self._scrape_ids, html, url)
        if result and result.get('records'):
            self._clean_ids(result['records'])
            for r in result['records']:
                if r.get('uid', '') == uid and r.get('url'):
                    self.logger.debug("Scraped url: %s", r['url'])
                    return self.get_html_from_url(r['url'])
        return None, None

class RotherScraper(Ocella2Scraper): # note inherits from Ocella2Scraper
    
    _authority_name = 'Rother'
    _search_url = 'http://planweb01.rother.gov.uk/OcellaWeb/planningSearch'
    _scrape_ids = """
    <table rules="rows"> <tr />
    {* <tr>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    </tr> *}
    </table>
    """
    
    detail_tests = [
        { 'uid': 'RR/2011/1789/P', 'len': 14 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 22 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 11 } ]
        
class SouthHollandScraper(Ocella2Scraper): # note inherits from Ocella2Scraper

    data_start_target = '2000-01-06'
    
    _authority_name = 'SouthHolland'
    _search_url = 'http://planning.sholland.gov.uk/OcellaWeb/planningSearch'
    _scrape_ids = """
    <table rules="rows"> <tr />
    {* <tr>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    </tr> *}
    </table>
    """
    _scrape_data_block = '<form name="showDocuments" /> {{ block|html }} <a href="#nav" />'
    _scrape_min_data = """
    <table> <td> Reference </td> <td> {{ reference }} </td>
    <td> Proposal </td> <td> {{ description }} </td>
    <td> Location </td> <td> {{ address }} </td>
    <td> Received </td> <td> {{ date_received }} </td> </table>
    """
    
    detail_tests = [
        { 'uid': 'H02-0763-12', 'len': 14 }]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 26 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 8 } ]

class WorcesterScraper(Ocella2Scraper): # note inherits from Ocella2Scraper

    _authority_name = 'Worcester'
    _search_url = 'http://planning.worcester.gov.uk/OcellaWeb/planningSearch'
    _scrape_ids = """
    <table rules="rows"> <tr />
    {* <tr>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    </tr> *}
    </table>
    """
    
    detail_tests = [
        { 'uid': 'P11A0394', 'len': 14 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 16 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]
    

    
