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
try:
    from ukplanning import scrapeutils
except ImportError:
    import scrapeutils
import idox
from datetime import timedelta, datetime
import re

# with mechanize produces ParseError: expected name token at '<!\xe2?? Getty Thesauru'
# <![non-ascii]?? Getty Thesaurus of Geographic Names (TGN) metadata [non-ascii]??>

# with requests Http/URL error: ("bad handshake: Error([('SSL routines', 'ssl3_get_server_certificate', 'certificate verify failed')],)",)

# solution is to massage html before form processing using mechanize

class NewarkScraper(idox.IdoxScraper):

    _search_url = 'https://publicaccess.newark-sherwooddc.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Newark'
    _html_subs = { 
        r'<meta\s.*?\s/>': r'',
        r'<![^>]*>': r''
    }
    _disabled = False
    detail_tests = [
        { 'uid': '12/01061/FUL', 'len': 21 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 27 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 }  ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        self._adjust_response(response)
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
                self._adjust_response(response)
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
        response = self.br.open(url) # use mechanize, to get same handler interface as elsewhere
        self._adjust_response(response)
        return self._get_html(response)

    def get_html_from_uid(self, uid):
        response = self.br.open(self._search_url)
        self._adjust_response(response)
        self.logger.debug("ID detail start html: %s", response.read())
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
            self._adjust_response(response)
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
            self._adjust_response(response)
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
                    
    def _adjust_response(self, response): 
        """ fixes bad html that breaks form processing """
        if self._html_subs:
            html = response.get_data()
            for k, v in self._html_subs.items():
                html = re.sub(k, v, html, 0, re.U|re.S|re.I) # unicode|dot matches new line|ignore case
            response.set_data(html)
            self.br.set_response(response)

