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
from datetime import timedelta

class FastwebScraper(base.DateScraper):

    min_id_goal = 300 # min target for application ids to fetch in one go
    batch_size = 21 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 21 # start this number of days ago when gathering current ids
    
    _scraper_type = 'Fastweb'
    _date_from_field = 'DateReceivedStart'
    _date_to_field = 'DateReceivedEnd'
    _search_fields = { 'ShowDecided': [] }
    _search_form = 'SearchForm'
    _scrape_ids = """
    <body> Search Results <table>
    {* <table> <tr> 
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td> </tr>
    <tr /> <tr />
    </table> *}
    </table> </body>
    """
    _next_page = 'Next'
    _detail_page = 'fulldetail.asp'

    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = "<body> <h1 /> {{ block|html }} </body>"
    # the minimum acceptable valid dataset on the details page
    _scrape_min_data = """
    <tr> <th> Application Number </th> <td> {{ reference }} </td> </tr>
    <tr> <th> Site Address </th> <td> {{ address }} </td> </tr>
    <tr> <th> Description </th> <td> {{ description }} </td> </tr>
    """
    # other optional parameters that can appear on the details page
    _scrape_optional_data = [
    "<tr> <th> Date Received </th> <td> {{ date_received }} </td> </tr>",
    "<tr> <th> Date Valid </th> <td> {{ date_validated }} </td> </tr>",
    "<tr> <th> Application Status </th> <td> {{ status }} </td> </tr>",
    "<tr> <th> Case Officer </th> <td> {{ case_officer }} </td> </tr>",
    "<tr> <th> Decision Level/Committee </th> <td> {{ decided_by }} </td> </tr>",
    "<tr> <th> Decision Level </th> <td> {{ decided_by }} </td> </tr>",
    "<tr> <th> Application Status </th> <td> {{ status }} </td> </tr>",
    "<tr> <th> Applicant Name </th> <td> {{ applicant_name }} <br> {{ applicant_address }} </td> </tr>",
    "<tr> <th> Agent Name </th> <td> {{ agent_name }}  <br> {{ agent_address }} </td> </tr>",
    "<tr> <th> Date Valid </th> </tr> <tr> <th> Decision </th> <td> {{ decision }} </td> </tr> <tr> <th> Decision Date </th> </tr>",
    "<tr> <th> Decision </th> <td> {{ decision }} </td> </tr> <tr> <th> Decision Status </th> <td> {{ status }} </tr>",
    "<tr> <th> Decision Type </th> <td> {{ decision }} </td> </tr>",
    "<tr> <th> Decision Date </th> <td> {{ decision_date }} </td> </tr>",
    "<tr> <th> Sent Date </th> <td> {{ decision_issued_date }} </td> </tr>",
    "<tr> <th> Target Date For Decision </th> <td> {{ target_decision_date }} </td> </tr>",
    "<tr> <th> Target Date of Application </th> <td> {{ target_decision_date }} </td> </tr>",
    "<tr> <th> Agent Phone </th> <td> {{ agent_tel }} </td> </tr>",
    "<tr> <th> Ward </th> <td> {{ ward_name }} </td> </tr>",
    "<tr> <th> Parish </th> <td> {{ parish }} </td> </tr>",
    "<tr> <th> Advert Date </th> <td> {{ last_advertised_date }} </td> </tr>",
    "<tr> <th> Appeal </th> <td> {{ appeal_result }} </td> </tr>",
    #"<tr> <th> Constraints </th> <td> {{ constraints|html }} </td> </tr>",
    #"<tr> <th> Recommendation Date </th> <td> {{ target_decision_date }} </td> </tr>",
    "<tr> <th> Area Team </th> <td> {{ district }} </td> </tr>",
    "<tr> <th> Consultation Period Begins </th> <td> {{ consultation_start_date }} </td> </tr>",
    "<tr> <th> Consultation Period Ends </th> <td> {{ consultation_end_date }} </td> </tr>", 
    "<tr> <th> Consultation/Reconsultation End Date </th> <td> {{ consultation_end_date }} </td> </tr>",
    "<tr> <th> Committee Date </th> <td> {{ meeting_date }} </td> </tr>",
    '<a href="{{ comment_url|abs }}"> Comment </a>',
    ]

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
        response = scrapeutils.submit_form(self.br)
        
        page_count = 0
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
                response = self.br.follow_link(text=self._next_page)
            except: # normal failure to find next page link at end of page sequence here
                self.logger.debug("No next link after %d pages", page_count)
                break
                
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
       
        return final_result

    def get_html_from_uid(self, uid):
        url = urlparse.urljoin(self._search_url, self._detail_page) + "?AltRef=" + urllib.quote_plus(uid)
        return self.get_html_from_url(url)
        
"""class CravenScraper(FastwebScraper): now Idox

    _search_url = 'http://www.planning.cravendc.gov.uk/fastweb/search.asp'
    _authority_name = 'Craven'
    detail_tests = [
        { 'uid': '30/2011/11959', 'len': 20 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 21 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]"""

"""class EastleighOldScraper(FastwebScraper): now JSON based

    current_span = 28 # start this number of days ago when gathering current ids
    _search_url = 'https://planning.eastleigh.gov.uk/search.asp'
    _authority_name = 'EastleighOld'
    detail_tests = [
        { 'uid': 'T/11/69536', 'len': 19 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 21 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 6 } ]"""

class EdenScraper(FastwebScraper): 

    _search_url = 'http://eforms.eden.gov.uk/fastweb/search.asp'
    _authority_name = 'Eden'
    detail_tests = [
        { 'uid': '11/0716', 'len': 20 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 16 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 4 } ]

"""class HarlowScraper(FastwebScraper): # now Idox 

    _search_url = 'http://communitymap.harlow.gov.uk/fastweb/search.asp'
    _authority_name = 'Harlow'
    detail_tests = [
        { 'uid': 'HW/PL/13/00028', 'len': 21 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 14 }, 
        { 'from': '15/08/2012', 'to': '15/08/2012', 'len': 2 } ]"""
    
"""class MansfieldScraper(FastwebScraper): # now Idox

    _search_url = 'http://www.mansfield.gov.uk/Fastweb/search.asp'
    _authority_name = 'Mansfield'
    detail_tests = [
        { 'uid': '2011/0474/ST', 'len': 17 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 10 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 4 } ]"""

class NeathScraper(FastwebScraper):

    _search_url = 'http://planning.npt.gov.uk/search.asp'
    _authority_name = 'Neath'
    detail_tests = [
        { 'uid': 'P2011/0713', 'len': 23 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 16 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 6 } ]

class NorthDevonScraper(FastwebScraper):

    _search_url = 'http://planning.northdevon.gov.uk/search.asp'
    _authority_name = 'NorthDevon'
    detail_tests = [
        { 'uid': '52673', 'len': 20 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 33 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 8 } ]

"""class PlymouthScraper(FastwebScraper): # now Idox

    _search_url = 'http://www.plymouth.gov.uk/planningapplicationsv4/search.asp'
    _authority_name = 'Plymouth'
    _detail_page = 'detail.asp'
    _scrape_ids = ""
    <body> <h1 /> <table>
    {* <table> <tr>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td> </tr>
    <tr> Received Date: {{ [records].date_received }} Decision Sent Date: </tr>
    </table> *}
    </table> </body>
    ""
    detail_tests = [
        { 'uid': '11/01380/FUL', 'len': 17 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 23 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 8 } ]"""

class ReadingScraper(FastwebScraper): # note end date is exclusive

    _search_url = 'http://planning.reading.gov.uk/fastweb_PL/search.asp'
    _authority_name = 'Reading'
    _search_fields = { 'ShowDecided': [], 'Decision_Made': [] }
    detail_tests = [
        { 'uid': '121722', 'len': 19 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 33 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 8 } ]
        
    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s", response.read())

        new_date_to = date_to + timedelta(days=1) # end date is exclusive, increment end date by one day
        fields = {}
        fields.update(self._search_fields)
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = new_date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        
        page_count = 0
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
                response = self.br.follow_link(text=self._next_page)
            except: # normal failure to find next page link at end of page sequence here
                self.logger.debug("No next link after %d pages", page_count)
                break
                
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
       
        return final_result
        
class RotherhamScraper(FastwebScraper):

    _search_url = 'http://planning.rotherham.gov.uk/fastweblive/search.asp'
    _authority_name = 'Rotherham'
    _comment = 'was custom scraper'
    detail_tests = [
        { 'uid': 'RB2011/0959', 'len': 23 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 43 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 6 } ]
        
class RugbyScraper(FastwebScraper):

    _search_url = 'http://www.planningportal.rugby.gov.uk/search.asp'
    _authority_name = 'Rugby'
    detail_tests = [
        { 'uid': 'R11/1591', 'len': 13 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 25 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 4 } ]

class SouthLakelandScraper(FastwebScraper):

    _search_url = 'http://applications.southlakeland.gov.uk/planningapplications/search.asp'
    _authority_name = 'SouthLakeland'
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = "<body> <h2 /> {{ block|html }} </body>"
    detail_tests = [
        { 'uid': 'SL/2011/0700', 'len': 19 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 31 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]

class SuttonScraper(FastwebScraper):

    _search_url = 'https://fastweb.sutton.gov.uk/fastweb/search.asp'
    _authority_name = 'Sutton'
    detail_tests = [
        { 'uid': 'B2011/64812', 'len': 19 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 48 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]

"""class WelwynHatfieldScraper(FastwebScraper): now Custom scraper

    current_span = 28 # start this number of days ago when gathering current ids
    _search_url = 'https://fastweb.welhat.gov.uk/search.asp?ApplicationNumber=&AddressPrefix=&submit1=Go'
    _authority_name = 'WelwynHatfield'
    detail_tests = [
        { 'uid': 'N6/2011/1682/TP', 'len': 19 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 41 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 9 } ]"""
    
class WyreForestScraper(FastwebScraper):

    _search_url = 'http://www.wyreforest.gov.uk/fastweb/search.asp'
    _authority_name = 'WyreForest'
    detail_tests = [
        { 'uid': '11/0516/FULL', 'len': 21 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 12 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 4 } ]
    


    
