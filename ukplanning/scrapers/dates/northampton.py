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
from .. import basereq
try:
    from ukplanning import scrapeutils
except ImportError:
    import scrapeutils
import urllib, urlparse
import json
import requests

# for other JSON based scrapers - see AmberValley, Broxtowe, SWDevon (Old), NorthLincs and Eastleigh

class NorthamptonScraper(basereq.DateReqScraper):
    
    # note the new version uses the 'requests' library and JSON requests/responses
    
    min_id_goal = 100 # min target for application ids to fetch in one go
    
    _authority_name = 'Northampton'
    _comment = 'Was Civica'
    _search_url = 'http://planning.northamptonboroughcouncil.com/planning/search-applications'
    _applic_url = 'http://planning.northamptonboroughcouncil.com/planning/planning-application?RefType=PBDC&KeyNo='
    _json_search_url = 'http://planning.northamptonboroughcouncil.com/civica/Resource/Civica/Handler.ashx/keyobject/pagedsearch'
    _json_applic_url = 'http://planning.northamptonboroughcouncil.com/civica/Resource/Civica/Handler.ashx/keyobject/search'
    _headers = {
    'Content-Type': 'application/json; charset=UTF-8',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'X-Requested-With': 'XMLHttpRequest'
    }
    _search_fields = { "refType": "PBDC", "fromRow": 1, "toRow": 10, "NoTotalRows": False }
    _date_from_field = 'valid_dateFrom'
    _date_to_field = 'valid_dateTo'
    
    # specifies JSON dict (sub) element encompassing all fields to be gathered
    _scrape_data_block = [ 'Record' ]
    # specifies JSON dict (sub) element whose existence indicates JSON return 
    # has known format but no appropriate data
    _scrape_invalid_format = [ 'TotalRows' ]
    
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
        'reference': 'ref_no',
        'date_received': 'received_date',
        'address': 'application_address', 
        'description': 'proposal'
    }
    _scrape_optional_data = {
        'planning_portal_id': 'planning_portal_ref_no"',
        'agent_name': 'AgentContactNoName',
        'application_type': 'app_type',
        'status': 'app_status',
        'meeting_date': 'committee_date',
        'decision': 'decision_notice_type', # or possibly 'recommendation'
        'decision_date': 'decision_date',
        'target_decision_date': 'target_date',
        'appeal_decision_date': 'appeal_decision_date',  
        'appeal_date': 'appeal_lodged_date',
        'appeal_result': 'appeal_decision',
        'date_validated': 'valid_date',
        'last_advertised_date': 'advertised_date',
        'decision_issued_date': 'decision_notice_sent_date',
        'consultation_end_date': 'consultation_end_date',
        'application_expires_date': 'expiry_date',
        'ward_name': 'ward',
        'parish': 'parish',
        'applicant_name': 'ApplicantContactNoName',
        'case_officer': 'case_officer',
        'decided_by': 'decision_level',
    }
    detail_tests = [
        { 'uid': 'N/2012/0791', 'len': 15 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 29 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 11 } ]
    
    def get_id_batch (self, date_from, date_to):
    
        final_result = []
        
        fields = {}
        fields.update(self._search_fields)
        search = {}
        search[self._date_from_field] = date_from.strftime(self._request_date_format)
        search[self._date_to_field] = date_to.strftime(self._request_date_format)
        fields["searchFields"] = search
        self.logger.debug("ID batch fields: %s", str(fields))
        data = json.dumps(fields)
        response = self.rs.post(self._json_search_url, data=data, timeout=self._timeout, headers=self._headers)
        html, url = self._get_html(response)
        json_dict = response.json()
        
        try:
            max_recs = int(json_dict['TotalRows'])
        except:
            max_recs = 0
        
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
                    if rec_items.get('ref_no') and rec_items.get('KeyNo'):
                        this_rec['uid'] = rec_items['ref_no']
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
                data = json.dumps(fields)
                response = self.rs.post(self._json_search_url, data=data, timeout=self._timeout, headers=self._headers)
                html, url = self._get_html(response)
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
        search = { 'ref_no': uid }
        fields["searchFields"] = search
        data = json.dumps(fields)
        response = self.rs.post(self._json_search_url, data=data, timeout=self._timeout, headers=self._headers)
        return self._get_html(response)
        
    def get_html_from_url(self, url):
        """ note returns JSON string not HTML
        in this case the JSON is a list payload with one record  
        the single record contains Description, KeyNo and Items among others """
        query = urlparse.parse_qs(urlparse.urlparse(url).query, keep_blank_values=True)
        keyText = query.get('KeyNo')
        if keyText:
            fields = { "refType": "PBDC", "fromRow": 1, "toRow": 1, "keyNumb": keyText[0] }
            data = json.dumps(fields)
            response = self.rs.post(self._json_applic_url, data=data, timeout=self._timeout, headers=self._headers)
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


