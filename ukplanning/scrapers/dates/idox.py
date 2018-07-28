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
from datetime import timedelta, datetime
try:
    from ukplanning import scrapemark
except ImportError:
    import scrapemark
try:
    from ukplanning import scrapeutils
except ImportError:
    import scrapeutils
from .. import base

class IdoxScraper(base.DateScraper):

    data_start_target = '2007-12-01' 
    # temporarily reduce collection period for all Idox scrapers - will extend it later 14/2/17
    
    min_id_goal = 300 # min target for application ids to fetch in one go
    _disabled = False # default, can be selectively disabled below
    _scraper_type = 'Idox'
    _date_from_field = 'date(applicationReceivedStart)'
    _date_to_field = 'date(applicationReceivedEnd)'
    _search_form = 'searchCriteriaForm'
    _ref_field = 'searchCriteria.reference'
    _detail_page = 'applicationDetails.do'
    _scrape_ids = """
    <ul id="searchresults">
    {* <li>
    <a href="{{ [records].url|abs }}" /> 
    <p> No: {{ [records].uid }} <span />
    </li> *}
    </ul>
    """
    _scrape_one_id = """
    <a id="subtab_summary" href="{{ url|abs }}" />
    <th> Reference </th> <td> {{ uid }} </td> </table>
    """
    _scrape_next_link = '<p class="pager top"> <a href="{{ next_link|abs }}" class="next"> </a> </p>'
    _scrape_dates_link = '<a id="subtab_dates" href="{{ dates_link|abs }}" />'
    _scrape_info_link = '<a id="subtab_details" href="{{ info_link|abs }}" />'

    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = '<body> {{ block|html }} </body>'
    _scrape_dates_block = '<body> {{ block|html }} </body>'
    _scrape_info_block = '<body> {{ block|html }} </body>'
    # the minimum acceptable valid dataset on each page
    _scrape_min_data = """
    <th> Reference </th> <td> {{ reference }} </td>
    <th> Address </th> <td> {{ address }} </td>
    <th> Proposal </th> <td> {{ description }} </td>
    """
    _scrape_min_dates = """
    <th> Validated </th> <td> {{ date_validated }} </td>
    """
    _scrape_min_info = """
    <th> Application Type </th> <td> {{ application_type }} </td>
    """
    # min field list used in testing only
    _min_fields = [ 'reference', 'address', 'description', 'date_validated', 'application_type' ]
    # other optional parameters on a page
    _scrape_optional_data = [
    '<a id="subtab_summary" href="{{ url|abs }}" />',
    '<th> Received </th> <td> {{ date_received }} </td>',
    '<th> Registered </th> <td> {{ date_validated }} </td>',
    '<th> Valid </th> <td> {{ date_validated }} </td>',
    '<th> Validated </th> <td> {{ date_validated }} </td>',
    '<th> Planning Portal Reference </th> <td> {{ planning_portal_id }} </td>',
    '<th> Reference </th> <td> {{ reference }} </td> <th> Alternative Reference </th>',
    '<th> Alternative Reference </th> <td> {{ alt_reference }} </td>',
    '<th> Application Type </th> <td> {{ application_type }} </td>',
    '<th> Status </th> <td> {{ status }} </td>',
    '<th> Status </th> <td> {{ status }} </td> <th> Appeal Status </th> <td> {{ appeal_status }} </td>',
    '<th> Status </th> <td> {{ status }} </td> <th> Appeal Decision </th> <td> {{ appeal_result }} </td>',
    '<th> Appeal Received </th> <td> {{ appeal_date }} </td>',
    '<th> Decision Date </th> <td> {{ decision_date }} </td> <th> Decision </th> <td> {{ decision }} </td>',
    '<th> Decision </th> <td> {{ decision }} </td> <th> Decision Issued Date </th> <td> {{ decision_issued_date }} </td>',
    '<a id="tab_makeComment" href="{{ comment_url|abs }}"/>',
    '<a id="tab_neighbourComments" href="{{ comment_url|abs }}"/>',
    ]
    _scrape_optional_info = [
    '<th> Parish </th> <td> {{ parish }} </td>',
    '<th> Community Council </th> <td> {{ parish }} </td>',
    '<th> Ward </th> <td> {{ ward_name }} </td>',
    '<th> Neighbourhood </th> <td> {{ district }} </td>',
    '<th> Case Officer </th> <td> {{ case_officer }} </td>',
    '<th> Applicant Name </th> <td> {{ applicant_name }} </td>',
    '<th> Applicants Name </th> <td> {{ applicant_name }} </td>',
    '<th> Applicant Address </th> <td> {{ applicant_address }} </td>',
    '<th> Agent Name </th> <td> {{ agent_name }} </td>',
    '<th> Agent Company </th> <td> {{ agent_company }} </td>',
    '<th> Agent Address </th> <td> {{ agent_address }} </td>',
    '<th> Agent Phone Number </th> <td> {{ agent_tel }} </td>',
    '<th> Decision </th> <td> {{ decision }} </td> <th> Decision Level </th> <td> {{ decided_by }} </td>',
    ]
    _scrape_optional_dates = [
    '<th> Received </th> <td> {{ date_received }} </td>',
    '<th> Expiry Date </th> <td> {{ application_expires_date }} </td> Committee Date',
    '<th> Committee Date </th> <td> {{ meeting_date }} </td>',
    '<th> Determination Deadline </th> <td> {{ target_decision_date }} </td>',
    '<th> Target Date </th> <td> {{ target_decision_date }} </td>',
    '<th> Target Determination Date </th> <td> {{ target_decision_date }} </td>',
    '<th> Neighbour Consultation Date </th> <td> {{ neighbour_consultation_start_date }} </td>',
    '<th> Neighbour Consultation Expiry </th> <td> {{ neighbour_consultation_end_date }} </td>',
    '<th> Standard Consultation Date </th> <td> {{ consultation_start_date }} </td>',
    '<th> Standard Consultation Expiry </th> <td> {{ consultation_end_date }} </td>',
    '<th> Site Notice Posted Date </th> <td> {{ site_notice_start_date }} </td>',
    '<th> Site Notice Expiry Date </th> <td> {{ site_notice_end_date }} </td>',
    '<th> Advertised In Press </th> <td> {{ last_advertised_date }} </td>',
    '<th> Advertisement Expiry Date  </th> <td> {{ latest_advertisement_expiry_date }} </td>',
    '<th> Decision Issued Date </th> <td> {{ decision_issued_date }} </td>',
    '<th> Decision Printed Date </th> <td> {{ decision_published_date }} </td>',
    '<th> Decision Made Date </th> <td> {{ decision_date }} </td>',
    '<th> Decision Date </th> <td> {{ decision_date }} </td>',
    '<th> Permission Expiry Date  </th> <td> {{ permission_expires_date }} </td>',
    '<th> Closing Date for Comments </th> <td> {{ comment_date }} </td>',
    ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        #self.logger.debug("ID batch start html: %s", response.read())
        
        fields = {}
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
            elif not final_result: # is it a single record?
                single_result = scrapemark.scrape(self._scrape_one_id, html, url)
                if single_result:
                    self._clean_record(single_result)
                    final_result = [ single_result ]
                    break
            else:
                self.logger.debug("Empty result after %d pages", page_count)
                break
            try:
                result = scrapemark.scrape(self._scrape_next_link, html, url)
                response = self.br.open(result['next_link'])
            except:
                self.logger.debug("No next link after %d pages", page_count)
                break
                
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
       
        return final_result

    def get_html_from_uid(self, uid):
        response = self.br.open(self._search_url)
        #self.logger.debug("ID detail start html: %s", response.read())
        fields = {}
        fields[self._ref_field] = uid
        scrapeutils.setup_form(self.br, self._search_form, fields)
        #self.logger.debug("Get UID form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        html, url = self._get_html(response)
        # note return can be a single uid match page OR list of multiple matches
        result = scrapemark.scrape(self._scrape_ids, html, url)
        if result and result.get('records'):
            self._clean_ids(result['records'])
            for r in result['records']:
                if r.get('uid', '') == uid and r.get('url'):
                    self.logger.debug("Scraped url: %s", r['url'])
                    return self.get_html_from_url(r['url'])
            return None, None
        else:
            return html, url # this URL is not unique (POST query), so not OK to update 'url' field (see get_detail_from_uid below)
            
    def get_detail_from_uid(self, uid):
        html, url = self.get_html_from_uid(uid) 
        if html and url:
            return self._get_full_details(html, url, False) # NOTE does not not update the 'url' field
            #  also URL is scraped in the record so no need to update it here
        else:
            return None
        
    def _get_details(self, html, this_url):
        """ Scrapes detailed information for one record given html and url 
        - this is an optional hook to allow data from multiple linked pages to be merged """
        result = self._get_detail(html, this_url)
        if 'scrape_error' in result:
            return result
        try:
            temp_result = scrapemark.scrape(self._scrape_dates_link, html, this_url)
            dates_url = temp_result['dates_link']
            self.logger.debug("Dates url: %s", dates_url)
            response = self.br.open(dates_url)
            html, url = self._get_html(response)
        except:
            self.logger.warning("No link to dates page found")
        else:
            #self.logger.debug("Html obtained from dates url: %s", html)
            result2 = self._get_detail(html, url, self._scrape_dates_block, self._scrape_min_dates, self._scrape_optional_dates)
            if 'scrape_error' not in result2:
                result.update(result2)
            else:
                self.logger.warning("No information found on dates page")
        try:
            temp_result = scrapemark.scrape(self._scrape_info_link, html, this_url)
            info_url = temp_result['info_link']
            self.logger.debug("Info url: %s", info_url)
            response = self.br.open(info_url)
            html, url = self._get_html(response)
        except:
            self.logger.warning("No link to info page found")
        else:
            #self.logger.debug("Html obtained from info url: %s", html)
            result3 = self._get_detail(html, url, self._scrape_info_block, self._scrape_min_info, self._scrape_optional_info)
            if 'scrape_error' not in result3:
                result.update(result3)
            else:
                self.logger.warning("No information found on info page")
        return result
        
    def _clean_record(self, record):
        super(IdoxScraper, self)._clean_record(record)
        if record.get('alt_reference'):
            if not record.get('planning_portal_id') and record['alt_reference'].startswith('PP-'):
                record['planning_portal_id'] = record['alt_reference']
            elif len(record['alt_reference']) > 3 and record['alt_reference'].lower() <> 'not available':
                record['reference'] = record['alt_reference']
            del record['alt_reference']

"""class IdoxDatesScraper(IdoxScraper): no longer used by any site 

    _date_from_field = 'dates(applicationReceivedStart)'
    _date_to_field = 'dates(applicationReceivedEnd)'"""
        
class BexleyScraper(IdoxScraper): 

    min_id_goal = 100 # min target for application ids to fetch in one go
    
    _search_url = 'http://pa.bexley.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Bexley'
    detail_tests = [
        { 'uid': '11/01320/FUL', 'len': 31 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 33 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 6 } ]
        
    # unavailable 3 am to 5 am
    @classmethod
    def can_run(cls):
        now = datetime.now()
        if now.hour >= 2 and now.hour <= 6:
            return False
        else:
            return True

class ChelmsfordScraper(IdoxScraper): 

    _search_url = 'https://publicaccess.chelmsford.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Chelmsford'
    _scrape_min_dates = "<th> Received </th> <td> {{ date_received }} </td>"
    _min_fields = [ 'reference', 'address', 'description', 'date_received', 'application_type' ]
    detail_tests = [
        { 'uid': '12/01416/FUL', 'len': 26 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 43 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 16 } ]
        
class ChesterScraper(IdoxScraper):

    _search_url = 'https://pa.cheshirewestandchester.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Chester'
    _scrape_min_dates = "<th> Received </th> <td> {{ date_received }} </td>"
    _min_fields = [ 'reference', 'address', 'description', 'date_received', 'application_type' ]
    detail_tests = [
        { 'uid': '12/03351/FUL', 'len': 18 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 86 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 15 } ]

class HammersmithScraper(IdoxScraper):

    _search_url = 'http://public-access.lbhf.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Hammersmith'
    _scrape_min_dates = """
    <th> Registered </th> <td> {{ date_validated }} </td>
    """
    detail_tests = [
        { 'uid': '2011/02554/FUL', 'len': 21 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 55 }, 
        { 'from': '15/08/2012', 'to': '15/08/2012', 'len': 15 }  ]
    
class HinckleyScraper(IdoxScraper): 

    min_id_goal = 100 # min target for application ids to fetch in one go

    _search_url = 'https://pa.hinckley-bosworth.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Hinckley'
    detail_tests = [
        { 'uid': '12/00774/HOU', 'len': 25 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 18 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 4 } ]
               
class MidKentScraper(IdoxScraper): 

    _search_url = 'http://pa.midkent.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'MidKent'
    _comment = 'Combined planning service covering Maidstone and Swale - bu now excluding Tunbridge Wells'
    detail_tests = [
        { 'uid': '12/1714', 'len': 26 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 74 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 15 } ]
        
    # note Mid Kent scraper fails (500 error) if run between midnight? and 6 am ish
    @classmethod
    def can_run(cls):
        now = datetime.now()
        if now.hour >= 0 and now.hour <= 6:
            return False
        else:
            return True
    
class NorthKestevenScraper(IdoxScraper): 

    _search_url = 'http://planningonline.n-kesteven.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'NorthKesteven'
    detail_tests = [
        { 'uid': '11/0901/FUL', 'len': 32 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 16 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 } ]
        
    # note North Kesteven scraper fails (500 error) if run between midnight? and 8 am ish
    @classmethod
    def can_run(cls):
        now = datetime.now()
        if now.hour >= 0 and now.hour <= 7:
            return False
        else:
            return True

class OadbyScraper(IdoxScraper):

    _search_url = 'https://pa.oadby-wigston.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Oadby'
    _scrape_min_dates = """
    <th> Valid Date </th> <td> {{ date_validated }} </td>
    """
    detail_tests = [
        { 'uid': '12/00260/FUL', 'len': 28 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '23/09/2012', 'len': 10 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 }  ]
    
class TestValleyScraper(IdoxScraper): # very slow

    batch_size = 7 # batch size for each scrape - number of days to gather to produce at least one result each time
    min_id_goal = 200 # min target for application ids to fetch in one go

    _search_url = 'http://view-applications.testvalley.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'TestValley'
    detail_tests = [
        { 'uid': '11/01790/FULLS', 'len': 28 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 46 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 } ]

class TorbayScraper(IdoxScraper): 

    _headers = {
    'User-Agent': 'Mozilla/5.0 (Windows; U; MSIE 7.0; Windows NT 6.0; en-US)',
    'Accept-Charset': 'UTF-8,*',
    'Accept': 'text/html',
    'Accept-Language': 'en-gb,en' }
    _search_url = 'http://www.torbay.gov.uk/newpublicaccess/search.do?action=advanced'
    _authority_name = 'Torbay'
    detail_tests = [
        { 'uid': 'P/2011/0849', 'len': 20 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 34 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 4 } ]
        
"""class WestWiltshireScraper(IdoxScraper): now Planning Explorer

    _search_url = 'http://westplanning.wiltshire.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'WestWiltshire'
    detail_tests = [
        { 'uid': 'W/12/01640/FUL', 'len': 32 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 34 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 }  ]"""
        
