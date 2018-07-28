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
import re
import urllib

class AshfieldScraper(base.DateScraper):

    min_id_goal = 200 # min target for application ids to fetch in one go
    
    _authority_name = 'Ashfield'
    _search_url = 'http://www2.ashfield.gov.uk/cfusion/Planning/plan_findfile.cfm'
    _direct_url = 'http://www2.ashfield.gov.uk/cfusion/Planning/plan_arc_results2_v_date.cfm'
    _applic_url = 'http://www2.ashfield.gov.uk/cfusion/Planning/plan_history.cfm?reference='
    _ref_url = 'http://www2.ashfield.gov.uk/cfusion/Planning/plan_history_results.cfm'
    _date_from_field = {
        'day': 'fromday',
        'month': 'frommonth',
        'year': 'fromyear',
        }
    _date_to_field = {
        'day': 'to_day',
        'month': 'to_month',
        'year': 'to_year',
        }
    _search_form = '1'
    _search_fields = { 'search_date': 'Search',  }
    _ref_search = { 'search_ref': 'Search',  }
    _ref_field = 'reference'
    _next_link = 'Next' + chr(194) + chr(160) + '>>' 
    # UTF-8 bytes for &nbsp; as a non-unicode string
    _scrape_max_recs = '<p> Now displaying Planning Applications <strong /> to <strong /> of {{ max_recs }}. </p>'
    _scrape_ids = """
    <table class="planning_search"> <tr />
    {* <tr> <td> <a href="{{ [records].url|abs }}">
    {{ [records].uid }} </a> </td> </tr> *}
    </table>
    """
    _scrape_data_block = """
    <div id="mainBody"> {{ block|html }} </div>
    """
    _scrape_min_data = """
    <span class="headerbg"> <strong> Ref No. </strong> <strong> {{ reference }} </strong> </span>
    <span class="planning_heading"> Location </span> <div> {{ address }} <br /> </div>
    <span class="planning_heading"> Proposal </span> <div> {{ description }} </div>
    <span class="planning_heading"> Application Received </span> <div> {{ date_received }} </div>
    <span class="planning_heading"> Planning Application Valid </span> <div> {{ date_validated }} </div>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<span class="planning_heading"> Applicant </span> <div> {{ applicant_name }} </div>',
    '<span class="planning_heading"> Agent </span> <div> {{ agent_name }} </div>',
    '<span class="planning_heading"> Case Officer </span> <div> {{ case_officer }} </div>',
    '<span class="planning_heading"> Council Ward </span> <div> {{ ward_name }} </div>',
    '<span class="planning_heading"> Consultation Sent </span> <div> {{ consultation_start_date }} </div>',
    '<span class="planning_heading"> Consultation End </span> <div> {{ consultation_end_date }} </div>',
    '<span class="planning_heading"> Decision Made By </span> <div> {{ decided_by }} </div>',
    '<span class="planning_heading"> Decision Likely By </span> <div> {{ target_decision_date }} </div>',
    '<span class="planning_heading"> Decision Type </span> <div> {{ decision }} </div>',
    '<span class="planning_heading"> Decision Date </span> <div> {{ decision_date }} </div>',
    '<a href="{{ comment_url|abs }}"> Add a comment on this Planning Application </a>',
    '<a href="http://maps.ashfield.gov.uk/rmx4-webapp/RMX/public-map.htm?X={{easting}}&Y={{northing}}&ZOOM=10&LAYERS=ashfield,Ashfield_Parishes,Ashfield_Wards,Gazetteer,Streetview2012,Not_yet_built_for_RMX4,Current_Planning,Planning_History&LAYERS-VISIBLE=ashfield,Ashfield_Parishes,Ashfield_Wards,Gazetteer,Streetview2012,Not_yet_built_for_RMX4,Current_Planning,Planning_History&ERRORS=true&TOOLBAR=print,search&LEGEND=true&TABS=layers,enquire,annotate,markers"> View Location in Interactive Map via MOLE </a>',
    '<span class="planning_heading"> Appeal Start Date </span> <div> {{ appeal_date }} </div>',
    """<span class="planning_heading"> Appeal Decision </span> <div> {{ appeal_result }} </div>
    <span class="planning_heading"> Appeal Decision Date </span> <div> {{ appeal_decision_date }} </div>""",
    ]
    detail_tests = [
        { 'uid': 'V/2011/0659', 'len': 21 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 12 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]

    def get_id_batch (self, date_from, date_to):
        
        final_result = []
        
        response = self.br.open(self._search_url)
        
        fields = {}
        #fields.update(self._search_fields)
        date_from = date_from.strftime(self._request_date_format)
        date_parts = date_from.split('/')
        fields[self._date_from_field['day']] = [ date_parts[0] ]
        fields[self._date_from_field['month']] = [ date_parts[1] ]
        fields[self._date_from_field['year']] = [ date_parts[2] ]
        date_to = date_to.strftime(self._request_date_format)
        date_parts = date_to.split('/')
        fields[self._date_to_field['day']] = [ date_parts[0] ]
        fields[self._date_to_field['month']] = [ date_parts[1] ]
        fields[self._date_to_field['year']] = [ date_parts[2] ]
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        
        #response = self.br.open(self._direct_url, urllib.urlencode(fields))
        
        html = response.read()
        self.logger.debug("ID batch page html: %s", html)
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
                    final_result = [ single_result ]
            else:
                self.logger.debug("Empty result after %d pages", page_count)
                break
            if len(final_result) >= max_recs: break
            try:
                response = self.br.follow_link(text=self._next_link)
                #fields['StartRow'] = str((page_count*10)+1)
                #fields['PageNum'] = str(page_count+1)
                #print fields
                #response = self.br.open(self._direct_url, urllib.urlencode(fields))
                html = response.read()
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next link after %d pages", page_count)
                break
                
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
        
        return final_result

    def get_html_from_uid(self, uid):
        url = self._applic_url + urllib.quote_plus(uid)
        return self.get_html_from_url(url)
            
