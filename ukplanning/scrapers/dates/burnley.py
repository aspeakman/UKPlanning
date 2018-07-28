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
import re

#also see Ribble Valley, Walsall, Wyre, Rossendale

class BurnleyScraper(base.DateScraper):

    min_id_goal = 350
    
    _authority_name = 'Burnley'
    _handler = 'etree'
    _search_url = 'http://www.burnley.gov.uk/custom/plnapps/index.php'
    _detail_page = 'results.php'
    _search_fields = { 'search': 'search', 'clk': '1' }
    _date_from_field = 'from_date2'
    _date_to_field = 'to_date2'
    _link_next = '>'
    _scrape_ids = """
    <table id="searchresults"> 
        {* <tr> <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td> </tr> *}
    </table>"""
    _scrape_id = """
    <h1> Application {{ uid }} </h1>
    """
    _scrape_max_recs = '<h3> <strong> {{ max_recs }} </strong> Results for </h3>'
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <div id="contentContainer"> {{ block|html }} </div>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <h1> Application {{ reference }} </h1>
    <tr> <td> Proposal </td> <td> {{ description }} </td> </tr>
    <tr> <td> Development address </td> <td> {{ address }} </td> </tr>
    <tr> <td> Key dates </td> <td> <strong> Valid date </strong> {{ date_validated }} <strong /> </td> </tr>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    #'<p class="first"> <strong> {{ application_type }} </strong> </p>',
    #'<tr> <td> Development address </td> <td> <strong> Ward </strong> : {{ ward_name }} <br /> </td> </tr>',
    #'<tr> <td> Development address </td> <td> <strong> Parish </strong> : {{ parish }} </td> </tr>',
    '<tr> <td> Officer </td> <td> {{ case_officer }} </td> </tr>',
    '<tr> <td> Applicant </td> <td> <strong> {{ applicant_name }} </strong> {{ applicant_address }} </td> </tr>',
    '<tr> <td> Agent </td> <td> <strong> {{ agent_name }}</strong> {{ agent_address }} </td> </tr>',
    #'<tr> <td> Planning Status </td> <td> {{ status }} </td> </tr>',
    '<tr> <td> Decision </td> <td> <strong> {{ decision }} </strong> </td> </tr>',
    '<tr> <td> Decision </td> <td> <strong/> Date: {{ decision_date }} Decision level:  </td> </tr>',
    '<tr> <td> Decision </td> <td> <strong/> Decision level: {{ decided_by }} </td> </tr>',
    '<tr> <td> Key dates </td> <td> <strong> Committee </strong> {{ meeting_date }}  <strong />  </td> </tr>',
    '<tr> <td> Key dates </td> <td> <strong> Decision date </strong> {{ decision_date }}  <strong />  </td> </tr>',
    '<tr> <td> Key dates </td> <td> <strong> Eight week date </strong> {{ target_decision_date }}  <strong />  </td> </tr>',
    '<tr> <td> Key dates </td> <td> <strong> Consultation sent </strong> {{ consultation_start_date }}  <strong />  </td> </tr>',
    '<tr> <td> Key dates </td> <td> <strong> Consultation expires </strong> {{ consultation_end_date }}  <strong />  </td> </tr>',
    '<tr> <td> Key dates </td> <td> <strong> Advertised on </strong> {{ last_advertised_date }}  <strong />  </td> </tr>',
    '<tr> <td> Key dates </td> <td> <strong> Advert expires </strong> {{ latest_advertisement_expiry_date }}  <strong />  </td> </tr>',
    '<tr> <td> Key dates </td> <td> <strong> Decision date </strong> {{ decision_date }} <strong />  </td> </tr>',
    #'<tr> <td> Neighbour Consultation Sent </td> <td> {{ neighbour_consultation_start_date }} </td> </tr>',
    #'<tr> <td> Neighbour Consultation Expiry </td> <td> {{ neighbour_consultation_end_date }} </td> </tr>',
    ]
    detail_tests = [
        { 'uid': 'APP/2012/0113', 'len': 14 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 16 },
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 1 } ]
    
    def get_id_batch (self, date_from, date_to):

        final_result = []
        
        fields = {}
        fields.update(self._search_fields)
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        response = self.br.open(self._search_url + '?' + urllib.urlencode(fields))
        
        html = response.read()
        #self.logger.debug("ID batch page html: %s", html)
        try:
            result = scrapemark.scrape(self._scrape_max_recs, html)
            max_recs = int(result['max_recs'])
        except:
            max_recs = 0
        
        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        while response and len(final_result) < max_recs and page_count < max_pages:
            url = response.geturl()
            #self.logger.debug("Batch html: %s" % html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                page_count += 1
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            elif not final_result: # is it a single record?
                single_result = scrapemark.scrape(self._scrape_id, html, url)
                if single_result:
                    single_result['url'] = url
                    self._clean_record(single_result)
                    return [ single_result ]
            else:
                self.logger.debug("Empty result after %d pages", page_count)
                break
            if len(final_result) >= max_recs: break
            try:
                response = self.br.follow_link(text=self._link_next)
                html = response.read()
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next link after %d pages", page_count)
                break
        
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
            
        return final_result
        
    def get_html_from_uid(self, uid):
        url = urlparse.urljoin(self._search_url, self._detail_page) + '?ref=' + urllib.quote_plus(uid)
        return self.get_html_from_url(url)


