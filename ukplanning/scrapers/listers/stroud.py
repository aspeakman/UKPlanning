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
#from .. import base
try:
    from ukplanning import scrapeutils
except ImportError:
    import scrapeutils
import urllib, urlparse
from datetime import date
from annuallist import AnnualListScraper

# does not allow full date searches without restriction by application type or other criteria
# so this now works from the sequence of application numbers (in S.YY/NNNN format)

class StroudScraper(AnnualListScraper): # note annual list scraper is disabled by default

    min_id_goal = 300 # min target for application ids to fetch in one go
    current_span = 30 # min number of records to get when gathering current ids
    data_start_target = 20000001
    
    _disabled = False
    _authority_name = 'Stroud'
    _uid_only = True
    _max_index = 3000 # maximum records per year
    _search_url = 'http://www.stroud.gov.uk/apps/planning'
    #_date_from_field = 'ctl00$MainContent$receivedafter'
    #_date_to_field = 'ctl00$MainContent$receivedb4'
    _search_form = '1'
    _search_fields = { 
        #'__EVENTTARGET': 'ctl00$MainContent$Button41', 
        #'__EVENTARGUMENT': '',
        '__EVENTTARGET': 'ctl00$MainContent$searchLinkButton', 
        '__EVENTARGUMENT': '',
        #'ctl00$MainContent$dropapptype': ['FUL'],
        #'ctl00$MainContent$ApplicationDecided': 'N' 
    }
    #_search_submit = 'ctl00$MainContent$Button41'
    #_ref_submit = 'ctl00$MainContent$butSimpleSearch'
    _ref_field = 'ctl00$MainContent$simplesearch1'
    _scrape_invalid_format = '<table id="simpleSearchGridView" rules="{{invalid_format}}"> <td colspan="7"> No matches </td>'
    
    _scrape_ids = """
    <table id="simpleSearchGridView"> <tbody>
    {* <tr> <td /> <td> <span id="refvalid"> {{ [records].uid }} </span> </td> </tr> *}
    </tbody> </table>
    """
    _scrape_ids_ref = """
    <table id="simpleSearchGridView"> <tbody>
    {* <tr> <td /> <td> <span id="refvalid"> {{ [records].uid }} </span> </td> </tr> *}
    </tbody> </table>
    """
    _scrape_data_block = """
    <div id="simpleSearchPanel"> {{ block|html }} </div>
    """
    _scrape_min_data = """
    <table id="simpleSearchGridView"> <tbody> <tr> <td /> <td> <span id="refvalid"> {{ reference }} </span> </td> 
    <td> {{ address }} </td > <td> {{ description }} </td> <td> {{ status }} </td> </tr> </tbody> </table>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<table id="DetailsView1"> <td> Received On </td> <td> {{ date_received }} </td> </table>',
    '<table id="DetailsView1"> <td> Validated On </td> <td> {{ date_validated }} </td> </table>',
    '<table id="DetailsView1"> <td> Decision Notice </td> <td> decision notice on {{ decision_date }} </td> </table>',
    '<table id="DetailsView1"> <td> Decision Notice </td> <td> {{ decision }} </td> </table>',
    '<table id="DetailsView1"> <td> Appeal Status </td> <td> {{ appeal_status }} </td> </table>',
    '<table id="DetailsView1"> <td> Applicant Name </td> <td> {{ applicant_name }} </td> </table>',
    '<table id="DetailsView1"> <td> Agent Name </td> <td> {{ agent_name }} </td> </table>',
    '<table id="DetailsView1"> <td> Handling Officer </td> <td> {{ case_officer }} </td> </table>',
    '<table id="DetailsView1"> <td> Ward </td> <td> {{ ward_name }} </td> </table>',
    '<table id="DetailsView1"> <td> Parish </td> <td> {{ parish }} </td> </table>',
    '<table id="DetailsView1"> <td> Application Type </td> <td> {{ application_type }} </td> </table>',
    '<table id="DetailsView1"> <td> Delegation </td> <td> {{ decided_by }} </td> </table>',
    '<table id="DetailsView1"> <td> Publication Date </td> <td> {{ last_advertised_date }} </td> </table>',
    ]
    detail_tests = [
        { 'uid': 'S.12/1985/FUL', 'len': 16 },
        { 'uid': '20121985', 'len': 16 } 
    ]
    #batch_tests = [ # note date ranges should not overlap
    #    { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 9 }, 
    #    { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 } ]
    batch_tests = [ 
        { 'from': '20120506', 'to': '20120516', 'len': 8 },
        { 'from': '20119998', 'to': '20120008', 'len': 8 },
        { 'from': '20122990', 'to': '20123010', 'len': 8 },
        { 'from': '20150750', 'to': '20150760', 'len': 11 }, ]

    """def get_id_batch (self, date_from, date_to): for use in date scraper
        
        final_result = []
        response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s" % response.read())
        
        fields = {}
        #fields.update(self._search_fields)
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        #for control in self.br.form.controls:
        #    if control.type == "submit":
        #        control.disabled = True
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._search_submit)
        #response = scrapeutils.submit_form(self.br)
        
        if response:
            html = response.read()
            url = response.geturl()
            #self.logger.debug("Batch html: %s" % html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
        
        return final_result"""
        
    # based on same function in annuallist.py but copes with multiple uids returned
    def get_id_records (self, request_from, request_to, max_recs):
        if not request_from or not request_to or not max_recs:
            return [], None, None # if any parameter invalid - try again next time
        from_rec = int(request_from)
        to_rec = int(request_to)
        num_recs = int(max_recs)
        if from_rec < 1:
            if to_rec < 1: # both too small
                return [], None, None
            from_rec = 1
        if to_rec > num_recs:
            if from_rec > num_recs: # both too large
                return [], None, None
            to_rec = num_recs
        
        final_result = []
        rfrom = None; rto = None
        n = to_rec - from_rec + 1
        if self.over_sequence(to_rec): # at max sequence and gathering forward
            ii, yy, from_rec = self.split_sequence(from_rec, True)
        else: 
            ii, yy, from_rec = self.split_sequence(from_rec, False)
        to_rec = from_rec + n - 1
        in_current_year = False
        this_year = date.today().year
        for i in range(from_rec, to_rec + 1):
            index, year, new_seq = self.split_sequence(i)
            if year == this_year and index > 0:
                in_current_year = True
            if rfrom is None:
                rfrom = i
            rto = new_seq
            base_uid =  self.get_uid(index, year)
            uids = self.get_uid_list(base_uid)
            if not uids:
                uids = [ base_uid ]
            for uid in uids:
                html, url = self.get_html_from_uid(uid)
                if not html:
                    self.logger.debug("No html from uid %s", uid)
                    return [], None, None # no html to work on - something is wrong - exit
                result = scrapemark.scrape(self._scrape_min_data, html)
                if result and result.get('reference'):
                    final_result.append( { 'url': url, 'uid': uid } )
                else:
                    result = scrapemark.scrape(self._scrape_invalid_format, html)
                    if result and result.get('invalid_format'):
                        self.logger.debug("No valid record for uid %s", uid)
                    else:
                        if self._scrape_invalid_format2:
                            result = scrapemark.scrape(self._scrape_invalid_format2, html)
                            if result and result.get('invalid_format'):
                                self.logger.debug("No valid record for uid %s", uid)
                            else:
                                self.logger.error("Unrecognised record for uid %s", uid)
                                return [], None, None # not recognised as bad data - something is wrong - exit
                        else:
                            self.logger.error("Unrecognised record for uid %s", uid)
                            return [], None, None # not recognised as bad data - something is wrong - exit
            
        if not in_current_year or final_result:
            return final_result, rfrom, rto
        else:
            return [], None, None # empty result is invalid if any of the results are in the current year

    def get_uid(self, index, year):
        # create a uid from year and index integer values
        uid = 'S.' + str(year)[2:4] + '/' + str(index).zfill(self._index_digits)
        return uid
        
    def get_uid_list(self, uid):
        # note return is a list of uid matches (empty if no match)
        if uid.isdigit() and int(uid) > self.data_start_target: 
            uid = 'S.' + str(uid)[2:4] + '/' + str(uid)[4:8]
        html, url = self._get_html_from_uid(uid)
        #self.logger.debug("Uid html: %s" % html)
        result = scrapemark.scrape(self._scrape_ids_ref, html, url)
        uid_list = []
        if result and result.get('records'):
            #print result['records']
            self._clean_ids(result['records'])
            for r in result['records']:
                if r.get('uid', '').startswith(uid):
                    uid_list.append(r['uid'])
        return uid_list

    def _get_html_from_uid(self, uid):
        # note return here can be a single uid match page OR no match
        # however a list of multiple matches is an error
        response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s" % response.read())
        fields = {}
        fields.update(self._search_fields)
        fields[self._ref_field] = uid
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID ref form: %s", str(self.br.form))
        #response = scrapeutils.submit_form(self.br, self._ref_submit)
        response = scrapeutils.submit_form(self.br)
        return self._get_html(response)
        
    def get_html_from_uid(self, uid):
        # note return here can be a single uid match page OR no match
        # however a list of multiple matches is an error
        if uid.isdigit() and int(uid) > self.data_start_target: 
            uid = 'S.' + str(uid)[2:4] + '/' + str(uid)[4:8]
        html, url = self._get_html_from_uid(uid)
        #self.logger.debug("Uid html: %s" % html)
        result = scrapemark.scrape(self._scrape_ids_ref, html, url)
        if result and result.get('records'):
            #print result['records']
            self._clean_ids(result['records'])
            if len(result['records']) == 1:
                r = result['records'][0]
                if r.get('uid', '').startswith(uid):
                    return html, url
            return None, None
        else:
            return html, url

