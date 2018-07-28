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
from idoxreq import IdoxReqScraper
import requests
import urlparse
from datetime import timedelta

# Above Python 2.7.9 default HTTPS behaviour has changed - now always verifies remote HTTPS certificate
# Causes SSL errors on this site 
# urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:590)>
# ("bad handshake: Error([('SSL routines', 'ssl3_get_server_certificate', 'certificate verify failed')],)",)
# so re-engineered to use requests and kludge fix verify=False work around

# alternative non-implemented ssl import solution at bottom also would work

# also see Halton 
# and alternative non-requests fix for Suffolk

requests.packages.urllib3.disable_warnings()

class CastlePointScraper(IdoxReqScraper):
    
    batch_size = 28 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 28 # start this number of days ago when gathering current ids
    _search_url = 'https://publicaccess.castlepoint.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'CastlePoint'
    _disabled = False
    _comment = 'Was Ocella up to April 2014'
    detail_tests = [
        { 'uid': 'CPT/659/12/FUL', 'len': 26 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 7 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 } ]
        
    def get_id_batch (self, date_from, date_to):

        final_result = []
        fields = {}
        fields.update(self._search_fields)
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        rurl = urlparse.urljoin(self._search_url, self._results_page)
        response = self.rs.post(rurl, data=fields, verify=False, timeout=self._timeout)
        
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
        
    def get_html_from_url(self, url):
        """ Get the html and url for one record given a URL """
        if self._uid_only:
            return None, None
        if self._search_url and self._detail_page:
            url_parts = urlparse.urlsplit(url)
            url = urlparse.urljoin(self._search_url, self._detail_page)
            if url_parts.query:
                url = url + '?' + url_parts.query
        response = self.rs.get(url, verify=False, timeout=self._timeout) 
        return self._get_html(response)
        
    def get_html_from_uid(self, uid):
        fields = {}
        fields.update(self._search_fields)
        fields[self._ref_field] = uid
        rurl = urlparse.urljoin(self._search_url, self._results_page)
        response = self.rs.post(rurl, data=fields, verify=False, timeout=self._timeout)
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
            response = self.rs.get(dates_url, verify=False, timeout=self._timeout)
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
            response = self.rs.get(info_url, verify=False, timeout=self._timeout)
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
        
"""class CastlePointNewScraper(idox.IdoxScraper):
    
    import ssl
    # Above Python 2.7.9 default HTTPS behaviour has changed - now always verifies remote HTTPS certificate
    # Causes SSL errors on this site - urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:590)
    # See kludge fix here and Halton and Suffolk
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass # Legacy Python that doesn't verify HTTPS certificates by default
    else:
        # Handle target environment that doesn't support HTTPS verification
        ssl._create_default_https_context = _create_unverified_https_context

    batch_size = 28 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 28 # start this number of days ago when gathering current ids
    _search_url = 'https://publicaccess.castlepoint.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'CastlePointNew'
    _disabled = False
    _comment = 'Was Ocella up to April 2014'
    detail_tests = [
        { 'uid': 'CPT/659/12/FUL', 'len': 26 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 7 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 } ]"""
 

