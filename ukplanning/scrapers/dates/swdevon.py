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
from .. import base
from .. import basereq
try:
    from ukplanning import scrapeutils
except ImportError:
    import scrapeutils
import urllib, urlparse
import json
import requests
from datetime import timedelta, datetime

# South Hams and West Devon

# Note first old system only works up to 10 Nov 2015
# Next old system was JSON based and returns records for West Devon and South Hams combined (see 'UnitCode' field to separate them)
# Current system is a dates based scraper for both councils on their combined planning website - cannot distinguish between authorities
        
class SWDevonOldScraper(basereq.DateReqScraper):
    
    # note the new version uses the 'requests' library and JSON requests/responses
    
    min_id_goal = 100 # min target for application ids to fetch in one go
      
    _scraper_type = 'SWDevonOld'
    _default_timeout = 40
    _search_fields = { "refType": "APPPlanCase", "fromRow": 1, "toRow": 10 }
    _date_from_field = 'ReceivedDateFrom'
    _date_to_field = 'ReceivedDateTo'
    
    # specifies JSON dict (sub) element encompassing all fields to be gathered
    _scrape_data_block = [ 'Record' ]
    # specifies JSON dict (sub) element whose existence indicates JSON return 
    # has known format but no appropriate data
    _scrape_invalid_format = [ 'KeyText' ]
    
    # In the following maps ...
    # VALUES can be plain field names to return the named JSON field
    # Or arrays of strings/integers to return items within a JSON tree structure
    # eg 'z' would return 'val2' from { 'a': 'val1', 'z': 'val2' }
    # eg [ 'a', 'c' ] would return 'val2' from { 'a': { 'b': 'val1', 'c': 'val2' } }
    # eg [ 'a', 2 ]  would return 'val2' from { 'a': [ 'val0', 'val1', 'val2' ] }
    # KEYS can be plain field names to receive the value in the output dict
    # Or scrapemark markup to extract sub-text within JSON fields
    # e.g. 'result' would set { 'result': 'text' } in the output if 'text' was in the field
    # e.g. 'xx {{ result }} yy' would set { 'result': '2' } if 'xx 2 yy' was in the field
    #      but would not set any value if the field was 'aa 2 bb'
    
    _scrape_min_data = { 
        'reference': 'LARef',
        'date_received': 'ReceivedDate',
        'address': 'PremisesAddress', 
        'description': 'PlanningApplicationDescription'
    }
    _scrape_optional_data = {
        'planning_portal_id': 'PlanningPortalRef',
        'agent_name': 'AgentName',
        'agent_address': 'AgentAddress',
        'status': 'ApplicationStatus',
        'application_type': 'PlanningApplicationTypeCode',
        'development_type': 'DevelopmentTypeCode',
        'decision': 'DecisionCode',
        'decision_date': 'DecisionDate',
        'target_decision_date': 'TargetDeterminationDate',
        'appeal_decision_date': 'AppealDeterminationDate',
        'appeal_date': 'AppealDate',
        'appeal_result': 'AppealResultCode',
        'date_validated': 'ApplicationValidDate',
        'consultation_start_date': 'ConsulteeStartDate',
        'consultation_end_date': 'ConsulteeFinishDate',
        'application_expires_date': 'ExpiryDate',
        'uprn': 'UPRN',
        'easting': 'Easting',
        'northing': 'Northing',
        'postcode': 'Postcode',
        'ward_name': 'WardCode',
        'parish': 'AreaCode',
        'applicant_name': 'ApplicantName',
        'applicant_address': 'ApplicantAddress',
        'case_officer': 'OfficerCode',
        'decided_by': 'DecisionLevelCode',
    }
    
    def get_id_batch (self, date_from, date_to):

        # does not like single day requests - returns all 60k results
        if date_from == date_to: # note min 2 days, rejects same day requests
            date_to = date_to + timedelta(days=1) # increment end date by one day
            
        final_result = []
        
        fields = {}
        fields.update(self._search_fields)
        search = {}
        search[self._date_from_field] = date_from.strftime(self._request_date_format)
        search[self._date_to_field] = date_to.strftime(self._request_date_format)
        fields["searchFields"] = search
        self.logger.debug("ID batch fields: %s", str(fields))
        response = self.rs.post(self._json_search_url, json=fields, timeout=self._timeout)
        
        json_dict = response.json()
        #print json_dict
        try:
            max_recs = int(json_dict['TotalRows'])
        except:
            max_recs = 0
        
        #print max_recs
        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        while json_dict and len(final_result) < max_recs and page_count < max_pages:
            #self.logger.debug("JSON payload: %s" % str(json_dict))
            result = json_dict.get('KeyObjects')
            if result:
                page_count += 1
                rout = []
                for r in result:
                    this_rec = {}
                    rec_items = self._field_dict(r['Items'])
                    if rec_items.get('LARef') and rec_items.get('KeyNo') and rec_items.get('UnitCode') and rec_items['UnitCode'].startswith(self._unit_name):
                        this_rec['uid'] = rec_items['LARef']
                        this_rec['url'] = self._applic_url + rec_items['KeyNo']
                        rout.append(this_rec)
                self._clean_ids(rout)
                final_result.extend(rout)
            else:
                self.logger.debug("Empty payload after %d pages", page_count)
                break
            if len(final_result) >= max_recs: break
            try:
                fields ['fromRow'] = (page_count * 10) + 1
                fields ['toRow'] = (page_count * 10) + 10
                self.logger.debug("ID next fields: %s", str(fields))
                response = self.rs.post(self._json_search_url, json=fields, timeout=self._timeout)
                json_dict = response.json()
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next payload after %d pages", page_count)
                break
        
        if page_count >= max_pages:
            self.logger.warning("Too many payload requests - %d - probable run away loop" % page_count)
        
        return final_result
        
    def _field_dict(self, items_list):
        """ turns the Items array into a dict keyed on FieldName """
        result = {}
        for i in items_list:
            k = i.get('FieldName')
            v = i.get('Value')
            if k and v is not None and v <> "":
                result[k] = v
        return result
     
    def get_html_from_uid(self, uid):
        """ note returns JSON string not HTML
        in this case the the JSON is a dict payload with TotalRows of 1 and single record in a KeyObjects list
        the single record contains Description, KeyNo and Items among others"""
        fields = {}
        fields.update(self._search_fields)
        search = { 'LARef': uid }
        fields["searchFields"] = search
        response = self.rs.post(self._json_search_url, json=fields, timeout=self._timeout)
        return self._get_html(response)
        
    def get_html_from_url(self, url):
        """ note returns JSON string not HTML
        in this case the JSON is a list payload with one record  
        the single record contains Description, KeyNo and Items among others """
        query = urlparse.parse_qs(urlparse.urlparse(url).query, keep_blank_values=True)
        keyText = query.get('KeyText')
        if keyText:
            data = { "refType": "APPPlanCase", "fromRow": 1, "toRow": 1, "keyText": keyText[0] }
            response = self.rs.post(self._json_app_url, json=data, timeout=self._timeout)
        else:
            response = self.rs.get(url, timeout=self._timeout)
        return self._get_html(response)
        
    def _get_full_details(self, html, real_url, update_url=False):
        """ Return scraped record but never update base url using the website response """
        self.logger.debug("Real url: %s", real_url)
        return self._get_details(html, real_url)
        
    def _get_details(self, html, this_url):
        """ Scrapes detailed information for one record given a JSON string (html) and url 
        - this is an optional hook to allow e.g. data from multiple linked pages to be merged
        OR to interpolate a JSON decoder """
        try:
            #self.logger.debug("JSON to scrape: %s", html)
            json_dict = json.loads(html.strip())
            if isinstance(json_dict, list):
                json_dict = json_dict[0]
            elif json_dict['TotalRows'] == 1:
                json_dict = json_dict['KeyObjects'][0]
            json_dict['Record'] = self._field_dict(json_dict['Items'])
        except:
            json_dict = {}
        return self._get_detail_json(json_dict, this_url)
            
class SouthHamsOldScraper(SWDevonOldScraper): 

    _authority_name = 'SouthHamsOld'
    _unit_name = 'South Hams'
    
    #_search_url = 'http://apps.southhams.gov.uk/planningSearch/default.aspx'
    _search_url = 'http://apps.southhams.gov.uk/PlanningSearchMVC/'
    _applic_url = 'http://www.southhams.gov.uk/planningdetails?RefType=APPPlanCase&KeyText='
    _json_search_url = 'http://www.southhams.gov.uk/civica/Resource/Civica/Handler.ashx/keyobject/pagedsearch'
    #_json_app_url = 'http://www.southhams.gov.uk/civica/Resource/Civica/Handler.ashx/keyobject/search'
    _json_app_url = 'http://apps.southhams.gov.uk/PlanningSearchMVC/Home/LARefSearch'
    detail_tests = [
        { 'uid': '37/2268/12/F', 'len': 26 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '24/09/2012', 'len': 67 }, # 84 total
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 22 } ] # 27 total
        
class WestDevonOldScraper(SWDevonOldScraper):

    _authority_name = 'WestDevonOld'
    _unit_name = 'West Devon'
    
    #_search_url = 'http://apps.westdevon.gov.uk/planningSearch/default.aspx'
    _search_url = 'http://apps.westdevon.gov.uk/PlanningSearchMVC/'
    _applic_url = 'http://www.westdevon.gov.uk/planningdetails?RefType=APPPlanCase&KeyText='
    _json_search_url = 'http://www.westdevon.gov.uk/civica/Resource/Civica/Handler.ashx/keyobject/pagedsearch'
    _json_app_url = 'http://www.westdevon.gov.uk/civica/Resource/Civica/Handler.ashx/keyobject/search'
    
    detail_tests = [
        { 'uid': '03187/2012', 'len': 24 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '24/09/2012', 'len': 17 }, # 84 total
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ] # 27 total
        
"""class SWDevonOldScraper(base.DateScraper):

    min_id_goal = 200 # min target for application ids to fetch in one go
    
    _disabled = True # default, can be selectively enabled below
    _scraper_type = 'SWDevonOld'
    #_advanced_tab = 'ctl00$BodyContent$tab2'
    _lists_tab = 'ctl00$BodyContent$tab3'
    _date_from_field = {
        'day': 'ctl00$BodyContent$ddlAllAppsFromD',
        'month': 'ctl00$BodyContent$ddlAllAppsFromM',
        'year': 'ctl00$BodyContent$ddlAllAppsFromY',
        }
    _date_to_field = {
        'day': 'ctl00$BodyContent$ddlAllAppsToD',
        'month': 'ctl00$BodyContent$ddlAllAppsToM',
        'year': 'ctl00$BodyContent$ddlAllAppsToY',
        }
    _search_form = '0'
    _scrape_max_recs = ""
    <div id="BodyContent_divabwResults"> {{ max_recs }} applications found </div>""
    _scrape_ids = ""
    <fieldset title="Details">
    {* <div class="listResultLine">
    <a> {{ [records].uid }} </a>
    </div *}
    </fieldset>
    ""
    _scrape_next_submit = '<input type="submit" name="{{ next_submit }}" value="Next" />'
    _dates_tab = 'ctl00$BodyContent$sub3'
    _names_tab = 'ctl00$BodyContent$sub4'
    _scrape_data_block = ""
    <fieldset title="Application Details"> {{ block|html }} </fieldset>
    ""
    _scrape_min_data = ""
    <span id="BodyContent_lblNumber1"> {{ reference }} </span>
    <div id="BodyContent_basicDescriptionData"> {{ description }} </div>
    <div id="BodyContent_basicAddressData"> {{ address }} </div>
    ""
    _scrape_min_names = ""
    <div id="BodyContent_basicApplicantNameData"> {{ applicant_name }} </div>
    ""
    _scrape_min_dates = ""
    <div id="BodyContent_basicDateReceivedData"> {{ date_received }} </div>
    ""
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<div id="BodyContent_basicDecisionData"> {{ decision }} </div>',
    '<div id="BodyContent_basicDecisionDateData"> {{ decision_date }} </div>',
    '<div id="BodyContent_basicCaseOfficerData"> {{ case_officer }} </div>',
    ]
    _scrape_optional_dates = [
    '<div id="BodyContent_basicDateRegisteredData"> {{ date_validated }} </div>',
    '<div id="BodyContent_basicDateValidData"> {{ date_validated }} </div>',
    '<div id="BodyContent_basicDateTargetData"> {{ target_decision_date }} </div>',
    '<div id="BodyContent_basicDateCommentsData"> {{ comment_date }} </div>',
    '<div id="BodyContent_basicDateDecisionData"> {{ decision_date }} </div>',
    '<div id="BodyContent_basicDateAdvertData"> {{ last_advertised_date }} </div>',
    ]
    _scrape_optional_names = [
    '<div id="BodyContent_basicApplicantAddressData"> {{ applicant_address }} </div>',
    '<div id="BodyContent_basicAgentNameData"> {{ agent_name }} </div>',
    '<div id="BodyContent_basicAgentAddressData"> {{ agent_address }} </div>',
    ]

    def get_id_batch (self, date_from, date_to):
        
        final_result = []
        response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s", response.read())
        
        fields = { '__EVENTTARGET': self._lists_tab, 
            '__EVENTARGUMENT': '', 'ctl00$BodyContent$btnSimpleSearch': None}
        scrapeutils.setup_form(self.br, self._search_form, fields)
        #self.logger.debug("ID lists form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        #self.logger.debug("Lists html: %s", response.read())
        
        fields = {}
        dfrom = date_from.strftime('X%d/X%m/%Y').replace('X0','X').replace('X','')
        date_parts = dfrom.split('/')
        fields[self._date_from_field['day']] = [ date_parts[0] ]
        fields[self._date_from_field['month']] = [ date_parts[1] ]
        fields[self._date_from_field['year']] = [ date_parts[2] ]
        dto = date_to.strftime('X%d/X%m/%Y').replace('X0','X').replace('X','')
        date_parts = dto.split('/')
        fields[self._date_to_field['day']] = [ date_parts[0] ]
        fields[self._date_to_field['month']] = [ date_parts[1] ]
        fields[self._date_to_field['year']] = [ date_parts[2] ]
        scrapeutils.setup_form(self.br, self._search_form, fields)
        #self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        
        html = response.read()
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
                for res in result['records']:
                    res['url'] = url + '?shortid=' + urllib.quote_plus(res['uid'])
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            else:
                self.logger.debug("Empty result after %d pages", page_count)
                break
            if len(final_result) >= max_recs: break
            try:
                result = scrapemark.scrape(self._scrape_next_submit, html)
                next_submit = result['next_submit']
                self.logger.debug("Next submit control: %s", next_submit)
                scrapeutils.setup_form(self.br, self._search_form)
                self.logger.debug("ID next form: %s", str(self.br.form))
                response = scrapeutils.submit_form(self.br, next_submit)
                html = response.read() 
            except: # failure to find next page link at end of page sequence here
                self.logger.debug("No next form after %d pages", page_count)
                break
                
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
                
        return final_result
        
    # post process a set of uid/url records: sets the url
    ""def _clean_record(self, record):
        super(SWDevonScraper, self)._clean_record(record)
        if record.get('uid') and not record.get('url'):
            record['url'] = self._search_url + '?shortid=' + urllib.quote_plus(uid)""
            
    def get_html_from_uid(self, uid):
        url = self._search_url + '?shortid=' + urllib.quote_plus(uid)
        return self.get_html_from_url(url)
        
    def _get_details(self, html, this_url):
        "" Scrapes detailed information for one record given html and url 
        - this is an optional hook to allow data from multiple linked pages to be merged ""
        result = self._get_detail(html, this_url)
        if 'scrape_error' in result:
            return result
        try:
            fields = { '__EVENTTARGET': self._dates_tab, '__EVENTARGUMENT': ''}
            scrapeutils.setup_form(self.br, self._search_form, fields)
            response = scrapeutils.submit_form(self.br)
            html, url = self._get_html(response)
        except:
            self.logger.warning("No link to dates page found")
        else:
            #self.logger.debug("Html obtained from dates url: %s", html)
            result2 = self._get_detail(html, url, self._scrape_data_block, self._scrape_min_dates, self._scrape_optional_dates)
            if 'scrape_error' not in result2:
                result.update(result2)
            else:
                self.logger.warning("No information found on dates page")
        try:
            fields = { '__EVENTTARGET': self._names_tab, '__EVENTARGUMENT': ''}
            scrapeutils.setup_form(self.br, self._search_form, fields)
            response = scrapeutils.submit_form(self.br)
            html, url = self._get_html(response)
        except:
            self.logger.warning("No link to names page found")
        else:
            #self.logger.debug("Html obtained from names url: %s", html)
            result3 = self._get_detail(html, url, self._scrape_data_block, self._scrape_min_names, self._scrape_optional_names)
            if 'scrape_error' not in result3:
                result.update(result3)
            else:
                self.logger.warning("No information found on names page")
        return result"""
        
class SouthWestDevonScraper(base.DateScraper):
        
    min_id_goal = 200 # min target for application ids to fetch in one go
    
    _authority_name = 'SouthWestDevon'
    #_search_url = 'http://apps.southhams.gov.uk/PlanningSearchMVC/Home/AdvSearch'
    #_applic_url = 'http://apps.southhams.gov.uk/PlanningSearchMVC/Home/Details/'
    _search_url = 'http://apps.westdevon.gov.uk/PlanningSearchMVC/Home/AdvSearch'
    _applic_url = 'http://apps.westdevon.gov.uk/PlanningSearchMVC/Home/Details/'
    _date_from_field = 'RvalidFrom'
    _date_to_field = 'RvalidTo'
    _request_date_format = '%d-%m-%Y'
    _search_form = '#bottomsearchform'
    _ref_field = 'AdvLARef'
    _scrape_max_recs = """
    <h2> Search Results - {{ max_recs }} Results found </h2>"""
    _scrape_ids = """
    <h2> Search Results </h2> <table>
    {* <td colspan="2">
    <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a>
    </td> </tr> *}
    </table>
    """
    _scrape_data_block = """
    <div id="body"> {{ block|html }} </div>
    """
    _scrape_min_data_previous = """
    <tr> <td> LA REF (Planning Application ID): {{ reference }} ( {{ alt_reference }} ) </td> </tr>
    <tr> <td> Description: {{ description }} </td> </tr>
    <tr> <td> Address: {{ address }} </td>
    <td> Application Date: {{ date_validated }} </td> </tr>
    """
    _scrape_min_data = """
    <tr> <td> Planning Application Ref: {{ reference }} </td> </tr>
    <tr> <td> Description: {{ description }} </td> </tr>
    <tr> <td> Address: {{ address }} </td>
    <td> Application Date: {{ date_validated }} </td> </tr>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<tr> <td> Applicant Name: {{ applicant_name }} </td> </tr>',
    '<tr> <td> Target Determination Date: {{ target_decision_date }} </td> </tr>',
    '<tr> <td> Officer Name: {{ case_officer }} </td> </tr>',
    '<tr> <td> Agent Name: {{ agent_name }} </td> </tr>',
    '<tr> <td> Decision Date: {{ decision_date }} </td> </tr>',
    'Decision Date: <td colspan="2"> {{ decision }} </td>',
    '<tr> <td> Comments Due By: {{ comment_date }} <a href="{{ comment_url }}" /> </td> </tr>',
    '<a href="{{ comment_url }}"> Comment on this application </a>',
    ]
    detail_tests = [
        { 'uid': '37/2268/12/F', 'len': 11 },
        { 'uid': '121318', 'len': 11 }, 
        { 'uid': '03187/2012', 'len': 11 }, 
        { 'uid': '124340', 'len': 11 },
        { 'uid': '0931/17/HHO', 'len': 10 },
        { 'uid': '170931', 'len': 9 },
    ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 50 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 4 } ]
        
    # scraper times out if run in the early morning
    @classmethod
    def can_run(cls):
        now = datetime.now()
        if now.hour >= 0 and now.hour <= 6:
            return False
        else:
            return True
            
    def get_id_batch (self, date_from, date_to):

        final_result = []
        
        fields = {}
        #fields.update(self._search_fields)
        fields [self._date_from_field] = date_from.strftime(self._request_date_format)
        fields [self._date_to_field] = date_to.strftime(self._request_date_format)
        
        self.logger.debug("Fields: %s", str(fields))
        query = urllib.urlencode(fields)
        url = self._search_url + '?' + query
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
            #self.logger.debug("Batch html: %s" % html)
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
                #response = self.br.follow_link(text=self._link_next)
                url = self._search_url + '?' + query + '&page=' + str(page_count+1)
                response = self.br.open(url)
                html = response.read()
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next link after %d pages", page_count)
                break
        
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
              
        return final_result
        
    def get_html_from_uid (self, uid):
        if uid.isdigit():
            url = self._applic_url + urllib.quote_plus(uid)
            return self.get_html_from_url(url)
        else:
            response = self.br.open(self._search_url)
            #self.logger.debug("ID detail start html: %s", response.read())
            fields = {  self._ref_field: uid }
            scrapeutils.setup_form(self.br, self._search_form, fields)
            self.logger.debug("Get UID form: %s", str(self.br.form))
            response = scrapeutils.submit_form(self.br)
            html, url = self._get_html(response)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                self._clean_ids(result['records'])
                for r in result['records']:
                    if r.get('uid', '') == uid and r.get('url'):
                        self.logger.debug("Scraped url: %s", r['url'])
                        return self.get_html_from_url(r['url'])
            return None, None

    def _clean_record(self, record):
        if record.get('uid') and ' ' in record['uid']:
            fields = record['uid'].split()
            record['uid'] = fields[0] # only use the prefix before any space
        super(SouthWestDevonScraper, self)._clean_record(record)
        if record.get('alt_reference'):
            record['reference'] = record['alt_reference']
            del record['alt_reference']


