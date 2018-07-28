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
from datetime import date
try:
    from ukplanning import myutils
except ImportError:
    import myutils
import urllib, urlparse
import re

class IsleOfWightScraper(base.ListScraper):

    data_start_target = 18000 # gathering back to this record number (around year 2000)
    min_id_goal = 200 # min target for application ids to fetch in one go
    
    _authority_name = 'IsleOfWight'
    _uid_num_sequence = True # uid is numeric sequence number not the local authority reference
    _start_point = 28000 # default start if no other indication = see base.py
    _min_recs = 60
    _pin_regex = re.compile(r'P/\d\d\d\d\d/?\d?\d?') # note can overlap with TCP, so 2nd pref
    _tcp_regex = re.compile(r'TCP/\d\d\d\d\d/?\w?')
    _uid_regex = re.compile(r'frmId=(\d+)\s*$')
    _search_form = '0'
    _form_fields = { '__EVENTTARGET': 'lnkShowAll', '__EVENTARGUMENT': '', 'btnSearch': None, }
    _find_fields = { '__EVENTTARGET': '', '__EVENTARGUMENT': '' }
    _search_submit = 'btnSearch'
    _max_url = 'https://www.iwight.com/planning/planAppSearch.aspx'
    _search_url = 'https://www.iwight.com/planning/planAppSearchHistory.aspx'
    _applic_url = 'https://www.iwight.com/planning/AppDetails3.aspx?frmId='
    _scrape_ids = """
    <table id="dgResults"> <tr />
        {* <tr>
            <td> <a href="{{ [records].url|abs }}"> {{ [records].reference }} </a> </td>
         </tr> *}
    </table>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <form id="Form1"> {{ block|html }} </form>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <span id="lblAppNo"> {{ reference }} </span>
    <span id="lblLocation"> {{ address }} </span>
    <span id="lblProposal"> {{ description }} </span>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<span id="lblTrackreceivedDate"> {{ date_received }} </span>',
    '<span id="lblTrackRegDate"> {{ date_validated }} </span>',
    '<span id="lblTrackConsultStart"> {{ consultation_start_date }} </span>',
    '<span id="lblTrackConsultEnd"> {{ consultation_end_date }} </span>',
    '<span id="lblofficer"> {{ case_officer }} </span>',
    '<span id="lblTrackDecisionDate"> {{ decision_date }} </span>',
    '<span id="lblTrackAppealDate"> {{ appeal_date }} </span>',
    '<span id="lblWard"> {{ ward_name }} </span>',
    '<span id="lblParish"> {{ parish }} </span>',
    '<span id="lblCurrentStatus"> {{ status|html }} </span>',
    '<span id="lblAgent"> {{ agent_name }} <br /> {{ agent_address }} <br /> </span>',
    '<span id="lblDecisionNotice"> {{ decision|html }} </span>',
    '<span id="lblTrackAppealDate"> {{ appeal_date }} </span>',
    '<span id="lblTrackAppealDecisionDate"> {{ appeal_decision_date }} </span>',
    '<span id="lblCommitteeDate"> {{ meeting_date }} </span>',
    '<span id="lblPubDate"> {{ last_advertised_date }} </span>',
    '<span id="lblcommentsby"> {{ comment_date }} </span>',
    '<span id="lblEN"> {{ easting }} / {{ northing }} </span>',
    '<a id="lnkMakeComment" href="{{ comment_url|abs }}"> </a>',
    ]
    detail_tests = [
        { 'uid': '24669', 'len': 21 },
        { 'uid': 'TCP/05385/A, P/00404/12', 'len': 21 },
        ] 
    batch_tests = [ 
        { 'from': '25006', 'to': '25036', 'len': 31 }, ]

    def get_id_records (self, request_from, request_to, max_recs):
        if not request_from or not request_to or not max_recs:
            return [], None, None # if any parameter invalid - try again next time
        final_result = []
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
            
        for i in range(from_rec, to_rec + 1):
            final_result.append( { 'url': self._applic_url + str(i), 'uid': str(i) } )
            
        if final_result:
            return final_result, from_rec, to_rec
        else:
            return [], None, None # list scraper - so empty result is always invalid

    @property
    def max_sequence (self):
        response = self.br.open(self._max_url) 
        #self.logger.debug("max sequence html: %s", response.read())
        scrapeutils.setup_form(self.br, self._search_form, self._form_fields)
        self.logger.debug("max sequence form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        max_recs = None
        if response:
            html = response.read()
            url = response.geturl()
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                self._clean_ids(result['records'])
                num_recs = 0
                for i in result['records']:
                    try:
                        num = int(i['uid'])
                        if num > num_recs: 
                            num_recs = num
                    except:
                        pass
                self.logger.debug('Number of records %d' % num_recs)
                if num_recs > 0:
                    max_recs = num_recs
        return max_recs
        
    # post process a set of uid/url records: gets the uid from the url
    def _clean_record(self, record):
        if record.get('url'):
            uid_match = self._uid_regex.search(record['url'])
            if uid_match and uid_match.group(1):
                record['uid'] = uid_match.group(1)
        if record.get('reference'):    
            record['reference'] = record['reference'].replace(' - ', ', ')
        super(IsleOfWightScraper, self)._clean_record(record)

    # the uid can be a numeric "frmId", a PIN number - P/-----/-- or a TCP number - TCP/-----/-
    def get_html_from_uid (self, uid):
        uid = myutils.GAPS_REGEX.sub('', uid) # NB removes spaces
        if uid.isdigit():
            url = self._applic_url + str(uid)
            return self.get_html_from_url(url)
        else:
            fields = {}
            fields.update(self._find_fields)
            tcp_match = self._tcp_regex.search(uid)
            if tcp_match:
                fields['txtPIN'] = ''
                fields['txtTCP'] = tcp_match.group()
            else:        
                pin_match = self._pin_regex.search(uid)
                if pin_match:
                    fields['txtPIN'] = pin_match.group()
                    fields['txtTCP'] = ''
                else:
                    return None, None
            response = self.br.open(self._search_url) 
            scrapeutils.setup_form(self.br, self._search_form, fields)
            self.logger.debug("Uid form: %s", str(self.br.form))
            response = scrapeutils.submit_form(self.br, self._search_submit)
            html, url = self._get_html(response)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                self._clean_ids(result['records'])
                if len(result['records']) == 1: # supplied uid may not match scraped reference exactly 
                    r = result['records'][0]
                    if r.get('reference') and r.get('url'):
                        self.logger.debug("Scraped url: %s", r['url'])
                        return self.get_html_from_url(r['url'])
            return None, None
        


