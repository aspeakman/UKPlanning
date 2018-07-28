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
try:
    from ukplanning import scrapeutils
except ImportError:
    import scrapeutils
from .. import base
import urllib, urlparse
from datetime import date
import re

# Hounslow and Kingson on Thames and Richmond on Thames

class ThamesScraper(base.DateScraper):

    min_id_goal = 300 # min target for application ids to fetch in one go
    
    _scraper_type = 'Thames'
    _handler = 'etree'
    _date_from_field = 'strRecFrom'
    _date_to_field = 'strRecTo'
    _uid_field = 'strCASENO'
    _search_form = 'Form1'
    _search_submit = 'btn_Search'
    
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <form id="Form1"> {{ block|html }} </form>
    """
    
    def get_id_batch (self, date_from, date_to):

        final_result = []
        
        fields = {}
        fields.update(self._search_fields)
        fields [self._date_from_field] = date_from.strftime(self._request_date_format)
        fields [self._date_to_field] = date_to.strftime(self._request_date_format)
        
        self.logger.debug("Fields: %s", str(fields))
        query = urllib.urlencode(fields)
        url = urlparse.urljoin(self._search_url, self._results_page) + '?' + query
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
        
    def get_html_from_uid(self, uid): 
        url = urlparse.urljoin(self._search_url, self._detail_page) + '?' + self._uid_field + '=' + urllib.quote_plus(uid)
        return self.get_html_from_url(url) 

class HounslowScraper(ThamesScraper):

    batch_size = 28
    current_span = 28
    min_id_goal = 1
    _authority_name = 'Hounslow'
    _search_url = 'http://planning.hounslow.gov.uk/planning_search.aspx'
    _detail_page = 'Planning_CaseNo.aspx'
    _results_page = 'planning_summary.aspx'
    _cookies = [{
        'name': 'LBHSupportCookies',
        'value': 'true',
        'domain': 'planning.hounslow.gov.uk',
        },
        {
        'name': 'LBHPlanningAccept',
        'value': 'true',
        'domain': 'planning.hounslow.gov.uk',
        }]
    _uid_regex = re.compile(r'[A-Z][A-Z]?/\d\d\d\d/\d\d\d\d')
    _ref_field = 'txt_Alt_No'
    _search_fields = {
        'strWeekListType': 'SRCH',
        'strStreet': 'ALL',
        'strStreetTxt': 'All Streets',
        'strWard': 'ALL',
        'strAppTyp': 'ALL',
        'strWardTxt': 'All Wards',
        'strAppTypTxt': 'All Application Types',
        'strArea': 'ALL',
        'strAreaTxt': 'All Areas',
        'strLimit': '500',
    }
    _scrape_ids = """
    <form id="Form1"> <table />
    {* <table>
    <tr /> <tr>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> {{ [records].reference }} <br /> </td> </tr>
    </table> *}
    </form>
    """
    
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <span id="lbl_APPS"> Planning Reference: {{ reference }} <a /> </span>
    <span id="lbl_Site_description"> {{ address }} </span>
    <span id="lbl_Date_Rec"> {{ date_received }} </span>
    <span id="lbl_Proposal"> {{ description }} </span>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<span id="lbl_Date_Val"> {{ date_validated }} </span>',
    '<span id="lbl_Neighbourhood"> {{ district }} </span>',
    '<span id="lbl_App_Type"> {{ application_type }} </span>',
    '<span id="lbl_Ward"> {{ ward_name }} </span>',
    '<span id="lbl_Officer"> {{ case_officer }} </span>',
    '<span id="lbl_Status"> {{ status }} </span>',
    '<span id="lbl_COMMDATETYPE"> {{ decided_by }} </span>',
    '<span id="lbl_Dec_Level"> {{ decided_by }} </span>',
    '<span id="lbl_Target_Date"> {{ target_decision_date }} </span>',
    '<span id="lbl_Committee_Date"> {{ meeting_date }} </span>',
    '<span id="lbl_Applic_Name"> {{ applicant_name }} </span>',
    '<span id="lbl_Agent_Name"> {{ agent_name }} </span>',
    '<span id="lbl_Agent_Address"> {{ agent_address }} </span>',
    '<span id="lbl_Agent_Phone"> {{ agent_tel }} </span>',
    '<span id="lbl_Applic_Address"> {{ applicant_address }} </span>',
    '<span id="lbl_DECISIONNOTICESENTDATE"> {{ decision_issued_date }} </span>',
    '<span id="lbl_APPEAL_LODGED_DATE"> {{ appeal_date }} </span>',
    '<span id="lbl_P_APPEALS_DECISION"> {{ appeal_result }} </span>',
    '<span id="lbl_P_APPEALS_DECISIONDATE"> {{ appeal_decision_date }} </span>',
    '<a href="http://www.streetmap.co.uk/newmap.srf?x={{easting}}&amp;y={{northing}}"> Click here for a location map </a>',
    ]
    detail_tests = [
        { 'uid': 'SC/2016/0376', 'len': 19 },
        { 'uid': 'PA/2016/0763', 'len': 19 },
        { 'uid': 'P/2012/2353', 'len': 21 },
        { 'uid': '00496/3/P2', 'len': 21 },
        { 'uid': 'P/2013/3054', 'len': 19 },
        { 'uid': '00505/7FW/P1', 'len': 19 },]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 73 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 11 } ]
        
    def get_html_from_uid(self, uid): 
        uid_match = self._uid_regex.search(uid)
        if uid_match:
            return super(HounslowScraper, self).get_html_from_uid(uid)
        response = self.br.open(self._search_url)
        fields = { self._ref_field: uid }
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("Ref form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._search_submit)
        html = response.read()
        url = response.geturl()
        result = scrapemark.scrape(self._scrape_ids, html)
        if result and result.get('records'):
            self._clean_ids(result['records'])
            for r in result['records']:
                if r.get('reference', '') == uid:
                    self.logger.debug("Ref id: %s, Ref page url: %s" % (r['reference'], r['url']))
                    return self.get_html_from_url(r['url'])
            return None, None
        else:
            return html, url
            
    def _clean_record(self, record):
        if record.get('address') and record['address'].endswith('Click here for a location map'):
            record['address'] = record['address'][:-29] # strip out any suffix
        super(HounslowScraper, self)._clean_record(record)

class KingstonScraper(ThamesScraper):
    
    _authority_name = 'Kingston'
    _search_url = 'https://maps.kingston.gov.uk/propertyServices/planning/Search'
    _detail_page = 'Details'
    _results_page = 'Summary'
    _date_from_field = 'recFrom'
    _date_to_field = 'recTo'
    _uid_field = 'caseNo'
    _search_fields = {
        'weekListType': 'SRCH',
        'ward': 'ALL',
        'appTyp': 'ALL',
        'wardTxt': 'All Wards',
        'appTypTxt': 'All Application Types',
        'limit': '500',
    }
    _request_date_format = '%d/%b/%Y'
    
    _scrape_ids = """
    <main id="content"> 
    {* <div id="planningApplication">
    <h4> <a href="{{ [records].url|abs }}"> {{ [records].uid }} - </a> </h4>
    </div> *}
    </main>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <main id="content"> {{ block|html }} </main>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <span id="MainContent_lbl_APPS"> {{ reference }} </span>
    <span id="MainContent_lbl_Site_description"> {{ address }} </span>
    <span id="MainContent_lbl_Proposal"> {{ description }} </span>
    <span id="MainContent_lbl_Date_Rec"> {{ date_received }} </span>
    """
        # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<span id="MainContent_lbl_Date_Val"> {{ date_validated }} </span>',
    '<span id="MainContent_lbl_App_Type"> {{ application_type }} </span>',
    '<span id="MainContent_lbl_Neighbourhood"> {{ district }} </span>',
    '<span id="MainContent_lbl_Ward"> {{ ward_name }} </span>',
    '<span id="MainContent_lbl_Officer"> {{ case_officer }} </span>',
    '<span id="MainContent_lbl_COMMDATETYPE"> {{ decided_by }} </span>',
    '<span id="MainContent_lbl_Status"> {{ status }} </span>',
    '<span id="MainContent_lbl_Dec_Level"> {{ decided_by }} </span>',
    '<span id="MainContent_lbl_Target_Date"> {{ target_decision_date }} </span>',
    '<span id="MainContent_lbl_Committee_Date"> {{ meeting_date }} </span>',
    '<span id="MainContent_lbl_Applic_Name"> {{ applicant_name }} </span>',
    '<span id="MainContent_lbl_Agent_Name"> {{ agent_name }} </span>',
    '<span id="MainContent_lbl_Agent_Address"> {{ agent_address }} </span>',
    '<span id="MainContent_lbl_Agent_Phone"> {{ agent_tel }} </span>',
    '<span id="MainContent_lbl_Applic_Address"> {{ applicant_address }} </span>',
    '<span id="MainContent_lbl_DECISIONNOTICESENTDATE"> {{ decision_issued_date }} </span>',
    '<span id="MainContent_lbl_APPEAL_LODGED_DATE"> {{ appeal_date }} </span>',
    '<span id="MainContent_lbl_P_APPEALS_DECISION"> {{ appeal_result }} </span>',
    '<span id="MainContent_lbl_P_APPEALS_DECISIONDATE"> {{ appeal_decision_date }} </span>',
    '<a id="MainContent_hlViewMap" href="https://maps.kingston.gov.uk/maps/?map=boroughMap&amp;sm=true&amp;x={{easting}}&amp;y={{northing}}"> View location on map </a>',
    ]
    detail_tests = [
        { 'uid': '12/10213/FUL', 'len': 19 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 105 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 9 } ]

    def get_html_from_uid(self, uid): 
        if not uid.isdigit():
            uid = uid[0:8] # strip out any non-numeric suffix
        return super(KingstonScraper, self).get_html_from_uid(uid)
        
    def _clean_record(self, record):
        super(KingstonScraper, self)._clean_record(record)
        if record.get('uid') and not record['uid'].isdigit():
            record['uid'] = record['uid'][0:8] # strip out any suffix

class RichmondScraper(ThamesScraper):
    
    _authority_name = 'Richmond'
    _search_url = 'http://www2.richmond.gov.uk/PlanData2/Planning_Report.aspx'
    _detail_page = 'Planning_CaseNo.aspx'
    _results_page = 'planning_summary.aspx'
    _search_fields = {
        'strWeekListType': 'SRCH',
        'strWard': 'ALL',
        'strAppTyp': 'ALL',
        'strWardTxt': 'All Wards',
        'strAppTypTxt': 'ALL - all applications',
        'strAppStat': 'ALL',
        'strAppStatTxt': 'All Applications',
        'strStreet': 'ALL',
        'strStreetTxt': 'All Streets',
        'strLimit': '500',
        'strOrder': 'REC_DEC',
        'strOrderTxt': 'Most recently received first',
    }
    _request_date_format = '%d-%b-%Y'
    
    _scrape_ids = """
    <form id="Form1"> <table> <tr /> 
    {* 
    <tr> <td /> <td> {{ [records].uid }} </td> <td />
    <td> <a href="{{ [records].url|abs }}" /> </td> </tr>
    *}
    </table> </form>
    """

    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <h1> Planning application number: {{ reference }} </h1>
    <span id="PageContent_lbl_Site_description"> {{ address }} </span>
    <th class="lb-table-header"> Proposal </th> <td> {{ description }} </td>
    <th class="lb-table-header"> Application Received </th> <td> {{ date_received }} </td>
    """
        # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<th class="lb-table-header"> Validated </th> <td> {{ date_validated }} </td>',
    '<th class="lb-table-header"> Type </th> <td> {{ application_type }} </td>',
    '<span id="PageContent_lbl_Neighbourhood"> {{ district }} </span>',
    '<th class="lb-table-header"> Ward </th> <td> {{ ward_name }} </td>',
    '<th class="lb-table-header"> Officer </th> <td> {{ case_officer }} </td>',
    '<th class="lb-table-header"> Agent </th> <td> {{ agent_name }} <br/> {{ agent_address }}</td>',
    '<span id="PageContent_lbl_COMMDATETYPE"> {{ decided_by }} </span>',
    '<span id="PageContent_lbl_Status"> {{ status }} </span>',
    '<span id="PageContent_lbl_Dec_Level"> {{ decided_by }} </span>',
    '<span id="PageContent_lbl_Due_Date"> {{ target_decision_date }} </span>',
    '<span id="PageContent_lbl_Committee_Date"> {{ meeting_date }} </span>',
    '<span id="PageContent_lbl_Applic_Name"> {{ applicant_name }} </span>',
    '<span id="PageContent_lbl_Agent_Name"> {{ agent_name }} </span>',
    '<span id="PageContent_lbl_Agent_Address"> {{ agent_address }} </span>',
    '<span id="PageContent_lbl_Agent_Phone"> {{ agent_tel }} </span>',
    '<span id="PageContent_lbl_Applic_Address"> {{ applicant_address }} </span>',
    '<th class="lb-table-header"> Decision Issued </th> <td> {{ decision_issued_date }} </td>',
    '<th class="lb-table-header"> Neighbour notification started </th> <td> {{ neighbour_consultation_start_date }} </td>',
    '<span id="PageContent_lbl_APPEAL_LODGED_DATE"> {{ appeal_date }} </span>',
    '<span id="PageContent_lbl_P_APPEALS_DECISION"> {{ appeal_result }} </span>',
    '<span id="PageContent_lbl_P_APPEALS_DECISIONDATE"> {{ appeal_decision_date }} </span>',
    '<a id="amap" href="http://maps.google.com/?q={{latitude}},{{longitude}}&amp;z=24&amp;output=embed"> View on map </a>',
    ]
    detail_tests = [
        { 'uid': '12/2622/PS192', 'len': 15 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 106 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 24 } ]
        
    
    

