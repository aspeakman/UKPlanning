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

# stops working after 25/8/15 - now Idox

"""class BrentScraper(base.DateScraper):

    min_id_goal = 350
    
    _authority_name = 'Brent'
    _handler = 'soup'
    _search_url = 'https://forms.brent.gov.uk/servlet/ep.ext?extId=101149&byPeriod=Y&st=PL&periodUnits=day&periodMultiples=14'
    _ref_url = 'https://forms.brent.gov.uk/servlet/ep.ext?extId=109264&byOther1=Y&other1Label=Application%20Number&st=PL'
    _date_from_field = 'from'
    _date_to_field = 'until'
    _search_form = 'NonStopGov'
    _ref_field = 'other1'
    _scrape_ids = ""
    <p> Search Results </p>
    {* <strong> Case No: {{ [records].uid }} </strong> 
    <a href="{{ [records].url|abs }}"> Full details </a>
    <hr/> *}
    <a> Try another search </a>
    ""
    _scrape_no_results = "<strong> Sorry, no planning records {{ no_results }} to match your search. </strong>"

    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = '<body> {{ block|html }} </body>'
    # the minimum acceptable valid dataset on each page
    _scrape_min_data = ""
    <p> Information for Planning Application {{ reference }} </p>
    <td> <strong> Location: </strong> </td> <td> {{ address }} </td>
    <td> <strong> Proposal: </strong> </td> <td> {{ description }} </td>
    <td> <strong> Received Date: </strong> </td> <td> {{ date_received }} </td>
    ""
    # other optional parameters on a page
    _scrape_optional_data = [
    '<td> <strong> Application Type: </strong> </td> <td> {{ application_type }} </td>',
    '<td> <strong> Associated Application: </strong> </td> <td> {{ associated_application_uid }} </td>',
    '<td> <strong> Status: </strong> </td> <td> {{ status }} </td>',
    '<td> <strong> Decision: </strong> </td> <td> {{ decision }} </td>',
    '<td> <strong> Decision Date: </strong> </td> <td> {{ decision_date }} </td>',
    '<td> <strong> Case Officer: </strong> </td> <td> {{ case_officer|html }} </td>',
    '<td> <strong> Applicant: </strong> </td> <td> {{ applicant_name }} , {{ applicant_address }} </td>',
    '<td> <strong> Agent: </strong> </td> <td> {{ agent_name }} , {{ agent_address }} </td>',
    '<td> <strong> Comments: </strong> </td> <td> <a href="{{ comment_url }}"> Comment on this </a> </td>',
    ]
    detail_tests = [
        { 'uid': '12/2463', 'len': 15 },
        { 'uid': '15/0709', 'len': 15 }]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 70 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 7 } ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        params = 'from=%s&until=%s&auth=402&st=PL&parentst=&periodUnits=day&periodMultiples=14&' \
        'displayTitle=Search+by+Application+Date&instructions=&byFormat=N&byOther1=N&byOther2=N&' \
        'byOther3=N&byOther4=N&byOther5=N&byPostcode=N&byStreet=N&byHouseNumber=N&byAddress=N&' \
        'byPeriod=Y&extId=101149&queried=Y&other1Label=Other1&other2Label=Other2&other3Label=Other3&' \
        'other4Label=Other4&other5Label=Other5&other1List=&other2List=&other3List=&other4List=&' \
        'other5List=&periodLabel=From&addressLabel=Select+Address&print='
        dfrom = date_from.strftime(self._request_date_format)
        dto = date_to.strftime(self._request_date_format)
        response = self.br.open(self._search_url, params % (dfrom, dto))
        
        if response:
            html = response.read()
            url = response.geturl()
            #self.logger.debug("ID batch page html: %s", html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
           
        return final_result
        
    def get_html_from_uid(self, uid):
        uid = uid.strip()[:7]
        params = 'other1=%s&auth=402&st=PL&parentst=&periodUnits=Quarter&periodMultiples=1&' \
        'displayTitle=Planning+Applications&instructions=&byFormat=N&byOther1=Y&byOther2=N&' \
        'byOther3=N&byOther4=N&byOther5=N&byPostcode=N&byStreet=N&byHouseNumber=N&byAddress=N&' \
        'byPeriod=N&extId=109264&queried=Y&other1Label=Application+Number&other2Label=Other2&' \
        'other3Label=Other3&other4Label=Other4&other5Label=Other5&other1List=&other2List=&other3List=&' \
        'other4List=&other5List=&periodLabel=From&addressLabel=Select+Address&print='
        response = self.br.open(self._ref_url, params % urllib.quote_plus(uid))
        
        html, url = self._get_html(response)
        self.logger.debug("ID detail result html: %s", html)
        result = scrapemark.scrape(self._scrape_ids, html, url)
        
        if result and result.get('records'):
            self._clean_ids(result['records'])
            for r in result['records']:
                if r.get('uid', '') == uid and r.get('url'):
                    self.logger.debug("Scraped url: %s", r['url'])
                    return self.get_html_from_url(r['url'])
                    
        return None, None"""

        

