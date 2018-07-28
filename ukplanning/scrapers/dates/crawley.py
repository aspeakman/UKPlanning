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

class CrawleyScraper(base.DateScraper):

    min_id_goal = 300 # min target for application ids to fetch in one go

    _authority_name = 'Crawley'
    _search_url = 'http://www.crawley.gov.uk/pw/Planning_and_Development/Planning_Permission___Applications/Planning_Applications_Search/index.htm'
    _date_from_field = 'pFromDate'
    _date_to_field = 'pToDate'
    _uid_field = 'pApplicationNo'
    _search_fields = {
        'is_NextRow': '1',
        'accept': 'yes',
        'pDateType': 'received',
        'submit': 'Search',
        'strCSS': '',
        'pProposal': '',
        'pLocation': '',
        'pPostcode': '',
        'pWard': '',
        'pExternalCode': '', }
    _scrape_ids = """
    <div class="mainarea"> <table> <tr />
    {* 
    <tr> <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td> </tr>
    *}
    </table> </div>
    """
    _scrape_max_recs = '<div id="againlink" /> <p> <strong> Displaying 1-{{dummy}} of {{ max_recs }} </strong> </p>'
    _scrape_data_block = '<div id="leftcol" /> {{ block|html }} <div id="rightcol" />'
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <div class="pagetitle"> Planning Application {{ reference }} </div>
    <p> <strong> Location: </strong> {{ address }} </p>
    <p> <strong> Proposal: </strong> {{ description }} </p>
    <p> <strong> Received Date: </strong> {{ date_received }} </p>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<p> <strong> Location Postcode: </strong> {{ postcode }} </p>',
    '<p> <strong> Application Type: </strong> {{ application_type }} </p>',
    '<p> <strong> Expected Decision Date: </strong> {{ target_decision_date }} </p>',
    '<p> <strong> Delegated or Committee: </strong> {{ decided_by }} </p>',
    '<p> <strong> Case Officer: </strong> {{ case_officer }} </p>',
    '<p> <strong> Applicant Name:  </strong> {{ applicant_name }} </p>',
    '<p> <strong> Case Officer: </strong> {{ case_officer }} </p>',
    '<p> <strong> Agent:  </strong> {{ agent_name }} </p>',
    '<p> <strong> Agent Address:  </strong> {{ agent_address|html }} </p>',
    """<p> Application Status and Key Dates </p> <table> <tr />
    <tr> <td> {{ date_validated }} </td> <td> {{ comment_date }} </td> <td> {{ decision_date }} </td>
    <td> {{ appeal_date }} </td> <td> {{ appeal_decision_date }} </td> </tr> </table>""",
    '<p> <strong> Planning Portal ID: </strong> {{ planning_portal_id }} </p>',
    '<p> <strong> Planning Application Decision: </strong> {{ decision }} </p>',
    ]
    detail_tests = [
        { 'uid': 'CR/2012/0428/FUL', 'len': 18 },
    ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 28 }, 
        { 'from': '15/08/2012', 'to': '15/08/2012', 'len': 3 } ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        
        fields = {}
        fields.update(self._search_fields)
        fields [self._date_from_field] = date_from.strftime(self._request_date_format)
        fields [self._date_to_field] = date_to.strftime(self._request_date_format)
        fields [self._uid_field] = ''
        
        self.logger.debug("Fields: %s", str(fields))
        url = self._search_url + '?' + urllib.urlencode(fields)
        response = self.br.open(url)
        
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
                nextp = (page_count * 20) + 1
                fields['is_NextRow'] = str(nextp)
                self.logger.debug("Next fields: %s", str(fields))
                url = self._search_url + '?' + urllib.urlencode(fields)
                response = self.br.open(url)
                html = response.read()
                #self.logger.debug("ID next page html: %s", html)
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next link after %d pages", page_count)
                break
        
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
            
        return final_result
        
    def get_html_from_uid(self, uid): 
        fields = {}
        fields.update(self._search_fields)
        fields [self._date_from_field] = ''
        fields [self._date_to_field] = ''
        fields [self._uid_field] = uid
        self.logger.debug("UID Fields: %s", str(fields))
        url = self._search_url + '?' + urllib.urlencode(fields)
        response = self.br.open(url)
        html = response.read()
        url = response.geturl()
        #self.logger.debug("UID page html: %s", html)
        result = scrapemark.scrape(self._scrape_ids, html)
        if result and result.get('records'):
            self._clean_ids(result['records'])
            for r in result['records']:
                if r.get('uid', '') == uid:
                    return self.get_html_from_url(r['url'])
            return None, None
        else:
            return html, url
        
        

