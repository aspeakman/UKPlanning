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
import re

# also see SurreyHeath and Astun

# note address/easting/northing fields are scraped when gathering ids so field missing during uid testing - so have to supply dummy value - see comment below

class ElmbridgeScraper(base.DateScraper):

    min_id_goal = 350
    
    _authority_name = 'Elmbridge'
    _handler = 'etree'
    _search_url = 'http://emaps.elmbridge.gov.uk/ebc_planning.aspx?requesttype=parseTemplate&template=AdvancedSearchTab.tmplt'
    _start_url = 'http://emaps.elmbridge.gov.uk/ebc_planning.aspx'
    _applic_url = 'http://emaps.elmbridge.gov.uk/ebc_planning.aspx?requesttype=parsetemplate&template=PlanningDetailsTab.tmplt&basepage=ebc_planning.aspx&Filter=^APPLICATION_NUMBER^=%%27%s%%27&appno:PARAM=%s'
    #_dates_url = 'http://emaps.elmbridge.gov.uk/ebc_planning.aspx?requesttype=parseTemplate&template=PlanningKeyDatesTab.tmplt&Filter=^APPLICATION_NUMBER^=%%27%s%%27&appno:PARAM=%s'
    #_contacts_url = 'http://emaps.elmbridge.gov.uk/ebc_planning.aspx?requesttype=parseTemplate&template=PlanningContactsTab.tmplt&Filter=^APPLICATION_NUMBER^=%%27%s%%27&appno:PARAM=%s'
    
    _date_from_field = 'daterec_from:PARAM'
    _date_to_field = 'daterec_to:PARAM'
    _search_form = '1'
    _search_fields = { 
        'SearchType:PARAM': 'Advanced',
        'orderxyz:PARAM': 'REG_DATE_DT:DESCENDING',
        'pageno': '1',
        'pagerecs': '2000',
        'requestType': 'parseTemplate',
        'template': 'AdvancedSearchResultsTab.tmplt',
    }
    _east_regex = re.compile(r'easting:PARAM=(\d+)', re.I) # matches easting in URL
    _north_regex = re.compile(r'northing:PARAM=(\d+)', re.I) # matches northing in URL
    _scrape_ids = """
    <h2> Search Results </h2> <table> <tr />
    {* <tr>  <td> {{ [records].uid }} </td> 
        <td> {{ [records].address }} </td> <td/>
        <td> <a href="{{ [records].url|abs }}" /> </td>
        </tr>
    *}
    </table> 
    """
    _scrape_dates_link = '<li> Consultees </li> <li> <a href="{{ dates_link|abs }}"> Key Dates </a> </li>'
    _scrape_contacts_link = '<li> Details </li> <li> <a href="{{ contacts_link|abs }}"> Contacts </a> </li>'

    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = '<body> {{ block|html }} </body>'
    _scrape_dates_block = '<body> {{ block|html }} </body>'
    _scrape_contacts_block = '<body> {{ block|html }} </body>'
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <h1> Planning Applications </h1>
    <h2> {{ reference }} - {{ address }} </h2> 
    <dt> Description </dt> <dd> {{ description }} </dd>
    """
    _scrape_min_dates = """
    <dt> Received On </dt> <dd> {{ date_received }} </dd>
    """
    _scrape_min_contacts = """
    <dt> Case Officer </dt> <dd> {{ case_officer }} </dd>
    """
    # min field list used in testing only
    _min_fields = [ 'reference', 'description', 'date_received', 'case_officer' ]
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<ul id="tracker"> <p> Received On </p> <p> {{ date_received }} </p> </ul>',
    '<ul id="tracker"> <p> Valid From </p> <p> {{ date_validated }} </p> </ul>',
    '<dt> Application Type </dt> <dd> {{ application_type }} </dd>',
    '<dt> Status </dt> <dd> {{ status }} </dd>',
    '<dt> Ward </dt> <dd> {{ ward_name }} </dd>',
    '<dt> Decision Type : </dt> <dd> {{ decided_by }} </dd>',
    '<dt> Decision : </dt> <dd> {{ decision }} </dd>',
    ]
    _scrape_optional_contacts = [
    '<dt> Applicant Name </dt> <dd> {{ applicant_name }} </dd>',
    '<dt> Applicant Address </dt> <dd> {{ applicant_address }} </dd>',
    '<dt> Agent Name </dt> <dd> {{ agent_name }} </dd>',
    '<dt> Agent Company </dt> <dd> {{ agent_company }} </dd>',
    '<dt> Agent Address </dt> <dd> {{ agent_address }} </dd>',
    '<dt> Phone Number </dt> <dd> {{ agent_tel }} </dd>',
    ]
    _scrape_optional_dates = [
    '<dt> Valid From </dt> <dd> {{ date_validated }} </dd>',
    '<dt> Committee Date </dt> <dd> {{ meeting_date }} </dd>',
    '<dt> Decision Date </dt> <dd> {{ decision_date }} </dd>',
    '<dt> Target For Decision </dt> <dd> {{ target_decision_date }} </dd>',
    '<dt> Consultation Starts On </dt> <dd> {{ consultation_start_date }} </dd>',
    '<dt> Comments Welcome By </dt> <dd> {{ consultation_end_date }} </dd>',
    ]
    detail_tests = [
        { 'uid': '2012/3631', 'len': 18 },
        { 'uid': '2016/0582', 'len': 19 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 49 },
        { 'from': '15/08/2012', 'to': '15/08/2012', 'len': 11 } ]
    
    def get_id_batch (self, date_from, date_to):

        final_result = []
        
        fields = {}
        fields.update(self._search_fields)
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        
        url = self._start_url + '?' + urllib.urlencode(fields)
        response = self.br.open(url)
        
        if response:
            html = response.read()
            url = response.geturl()
            #self.logger.debug("Batch html: %s" % html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            
        return final_result
        
    def get_html_from_uid (self, uid):
        url = self._applic_url % (urllib.quote_plus(uid), urllib.quote_plus(uid))
        return self.get_html_from_url(url)
        # note never update URL from uid (does not have address)
            
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
            temp_result = scrapemark.scrape(self._scrape_contacts_link, html, this_url)
            contacts_url = temp_result['contacts_link']
            self.logger.debug("Contacts url: %s", contacts_url)
            response = self.br.open(contacts_url)
            html, url = self._get_html(response)
        except:
            self.logger.warning("No link to contacts page found")
        else:
            #self.logger.debug("Html obtained from contacts url: %s", html)
            result3 = self._get_detail(html, url, self._scrape_contacts_block, self._scrape_min_contacts, self._scrape_optional_contacts)
            if 'scrape_error' not in result3:
                result.update(result3)
            else:
                self.logger.warning("No information found on contacts page")
        return result
        
    def get_detail_from_uid(self, uid):
        html, url = self.get_html_from_uid(uid) 
        if html and url:
            return self._get_full_details(html, url, False) 
            # NOTE does not not update the 'url' field because is incomplete if scraped via this route
        else:
            return None
                
    def _clean_record(self, record):
        super(ElmbridgeScraper, self)._clean_record(record)
        #if record.get('ward_name') and not record.get('address'): # only use this for testing to supply dummy address
        #    record['address'] = record['ward_name']
        if record.get('url') and not record.get('easting') and not record.get('northing'):
            east_match = self._east_regex.search(record['url'])
            north_match = self._north_regex.search(record['url'])
            if east_match and east_match.group(1) and north_match and north_match.group(1):
                record['easting'] = east_match.group(1)
                record['northing'] = north_match.group(1)

