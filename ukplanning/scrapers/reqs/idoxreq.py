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
from .. import basereq
from ..dates import idox
import requests
import urlparse
from datetime import timedelta

# SSL errors on these sites when using normal mechanize/urllib2 interface with python 2.7.6
# so re-engineered to use requests/urllib3

class IdoxReqScraper(basereq.DateReqScraper, idox.IdoxScraper):
    
    _scraper_type = 'IdoxReq'
    _disabled = False
    _search_fields = { 'searchType': 'Application'  }
    _results_page = 'advancedSearchResults.do?action=firstPage'
    
    def __init__(self, *args, **kwargs):
        super(IdoxReqScraper, self).__init__(*args, **kwargs)
        
    def get_id_batch (self, date_from, date_to):

        final_result = []
        fields = {}
        fields.update(self._search_fields)
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        rurl = urlparse.urljoin(self._search_url, self._results_page)
        response = self.rs.post(rurl, data=fields, timeout=self._timeout)
        
        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        while response and page_count < max_pages:
            html, url = self._get_html(response)
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
                response = self.rs.get(result['next_link'], timeout=self._timeout)
            except:
                self.logger.debug("No next link after %d pages", page_count)
                break
                
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
       
        return final_result
        
    def get_html_from_uid(self, uid):
        fields = {}
        fields.update(self._search_fields)
        fields[self._ref_field] = uid
        rurl = urlparse.urljoin(self._search_url, self._results_page)
        response = self.rs.post(rurl, data=fields, timeout=self._timeout)
        html, url = self._get_html(response)
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
            response = self.rs.get(dates_url, timeout=self._timeout)
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
            response = self.rs.get(info_url, timeout=self._timeout)
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
        
"""class IdoxReqDatesScraper(IdoxReqScraper):

    _date_from_field = 'dates(applicationReceivedStart)'
    _date_to_field = 'dates(applicationReceivedEnd)'"""
        
class IdoxReqEndExcScraper(IdoxReqScraper):

    def get_id_batch (self, date_from, date_to): # end date is exclusive, not inclusive
        new_date_to = date_to + timedelta(days=1) # increment end date by one day
        return super(IdoxReqEndExcScraper, self).get_id_batch(date_from, new_date_to)

class AdurWorthingScraper(IdoxReqScraper): # tested

    _search_url = 'https://planning.adur-worthing.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'AdurWorthing'
    _comment = 'Combined planning service covering Adur and Worthing'
    detail_tests = [
        { 'uid': 'AWDM/0971/12', 'len': 31 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 29 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 12 } ]
        
class BasingstokeScraper(IdoxReqScraper):

    _search_url = 'https://planning.basingstoke.gov.uk/online-applications/search.do?action=advanced'
    _results_url = 'https://planning.basingstoke.gov.uk/online-applications/advancedSearchResults.do?action=firstPage'
    _authority_name = 'Basingstoke'
    _comment = 'was AcolNet'
    detail_tests = [
        { 'uid': 'BDB/77008', 'len': 23 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 51 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 18 } ]

class BarnetScraper(IdoxReqScraper): 

    current_span = 21 # start this number of days ago when gathering current ids
    batch_size = 17 # batch size for each scrape - number of days to gather to produce at least one result each time
    
    _search_url = 'https://publicaccess.barnet.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Barnet'
    _comment = 'was AcolNet'
    detail_tests = [
        { 'uid': 'F/03385/11', 'len': 25 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 83 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 17 } ]
        
class BoltonScraper(IdoxReqEndExcScraper): 
    
    # note uses insecure SSL3 only - see https://www.ssllabs.com/ssltest/analyze.html
    def __init__(self, *args, **kwargs):
        super(BoltonScraper, self).__init__(*args, **kwargs)
        self.rs.mount('https://www.planningpa.bolton.gov.uk', basereq.Ssl3HttpAdapter())

    _search_url = 'https://www.planningpa.bolton.gov.uk/online-applications-17/search.do?action=advanced'
    _authority_name = 'Bolton'
    detail_tests = [
        { 'uid': '86677/11', 'len': 28 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 33 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 12 } ]

class BrentScraper(IdoxReqEndExcScraper):

    _search_url = 'https://pa.brent.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Brent'
    _comment = 'was Custom'
    detail_tests = [
        { 'uid': '12/2463', 'len': 22 },
        { 'uid': '15/0709', 'len': 20 }]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 66 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 8 } ]
               
class ClackmannanshireScraper(IdoxReqScraper): # very slow

    _search_url = 'https://eplanning.clacks.gov.uk/eplanning/search.do?action=advanced'
    _authority_name = 'Clackmannanshire'
    detail_tests = [
        { 'uid': '11/00233/CLPUD', 'len': 20 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 5 }, 
        { 'from': '15/08/2012', 'to': '15/08/2012', 'len': 3 }  ]
    
class LichfieldScraper(IdoxReqScraper):

    _search_url = 'https://planning.lichfielddc.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Lichfield'
    detail_tests = [
        { 'uid': '11/00878/FUL', 'len': 30 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 15 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 }  ]
        
class SouthNorfolkScraper(IdoxReqScraper): 

    batch_size = 9
    _search_url = 'https://info.south-norfolk.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'SouthNorfolk'
    _comment = 'Was PlanningExplorer'
    detail_tests = [
        { 'uid': '2012/1709', 'len': 27 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 46 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]
        
class WestSomersetScraper(IdoxReqEndExcScraper): 

    _search_url = 'https://www.westsomerset.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'WestSomerset'
    detail_tests = [
        { 'uid': '3/01/12/017', 'len': 31 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 9 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 6 } ]    
        
class WyreScraper(IdoxReqScraper): 

    _search_url = 'https://publicaccess.wyre.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Wyre'
    _comment = 'Was custom annual scraper up to July 2016'
    detail_tests = [
        { 'uid': '12/00775/FUL', 'len': 30 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 14 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 } ]

