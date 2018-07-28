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

class AcolNetScraper(base.DateScraper):

    min_id_goal = 300 # min target for application ids to fetch in one go

    _scraper_type = 'AcolNet'
    _handler = 'etree' # note definitely need this as HTML is pretty rubbish
    _date_from_field = 'regdate1'
    _date_to_field = 'regdate2'
    _search_form = 'frmSearch'
    _ref_field = 'casefullref'
    _scrape_ids = """
    <div id="contentcol">
    {* <table class="results-table">
    <tr> <td class="casenumber"> <a href="{{ [records].url|abs }}">
    {{ [records].uid }} </a> </td> </tr>
    </table> *}
    </div>
    """
    _scrape_next = '<a id="lnkPageNext" href="{{ next_link }}"> </a>'
    _html_subs = { 
        r'<script\s.*?</script>': r'',
        r'<form\s[^>]*?WebMetric[^>]*?>.*?</form>': r'',
    }

    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = '<body> {{ block|html }} </body>'
    # the minimum acceptable valid dataset on the details page
    _scrape_min_data = """
    <th> Location </th> <td> {{ address }} </td>
    <th> Proposal </th> <td> {{ description }} </td>
    """
    # other optional parameters common to all scrapers can appear on the details page
    _scrape_optional_data = [
    '<th> Date Received </th> <td> {{ date_received }} </td>',
    "<th> Application Number: </th> <td> {{ reference }} </td>", # note colon
    "<th> Registration </th> <td> {{ date_validated }} </td>",
    "<th> Statutory Start </th> <td> {{ date_validated }} </td>",
    "<th> Application Type </th> <td> {{ application_type }} </td>",
    "<th> Case Officer </th> <td> {{ case_officer }} </td>",
    "<th> Decision Level </th> <td> {{ decided_by }} </td>",
    "Expected Decision Level <th> Decision Level </th> <td> {{ decided_by }} </td>",
    "<th> Appeal Received Date </th> <td> {{ appeal_date }} </td>",
    "<th> Date Appeal Recieved </th> <td> {{ appeal_date }} </td>", # NB spelling mistake is deliberate - Stoke on Trent
    "<th> Target Date for Decision </th> <td> {{ target_decision_date }} </td>",
    "<th> Appeal Decision </th> <td> {{ appeal_result }} </td>",
    "<th> Earliest Decision Date </th> <td> {{ consultation_end_date }} </td>",
    "<th> Consultation Period Expires </th> <td> {{ consultation_end_date }} </td>",
    "<th> Consultation Period Ends </th> <td> {{ consultation_end_date }} </td>",
    "<th> Status </th> <td> {{ status }} </td>",
    "<th> Parish </th> <td> {{ parish }} </td>",
    "<th> Ward </th> <td> {{ ward_name }} </td>",
    "<th> Comments </th> <td> {{ comment_date }} </td>",
    "<th> Applicant </th> <td> {{ applicant_name }} </td>",
    "<th> Consultation Start Date </th> <td> {{ consultation_start_date }} </td>",
    "<th> Consultation Period Starts </th> <td> {{ consultation_start_date }} </td>",
    "<th> Date from when comments </th> <td> {{ consultation_start_date }} </td>",
    "<th> Date Decision Made </th> <td> {{ decision_date }} </td>",
    "<th> Agent </th> <td> {{ agent_name }} </td>",
    "<th> Date Decision Despatched </th> <td> {{ decision_issued_date }} </td>",
    "<th> Decision Issued </th> <td> {{ decision_issued_date }} </td>",
    "<th> Meeting Date </th> <td> {{ meeting_date }} </td>",
    "<th> Committee </th> <td> {{ meeting_date }} </td>",
    "<tr> <th> Easting/Northing </th> <td> {{ easting }}/{{ northing }} </td> </tr>",
    "<th> Appeal Decision </th> <td> {{ appeal_result }} </td> <th> Appeal Decision Date </th> <td> {{ appeal_decision_date }} </td>",
    ]
    # optional parameters that can be replaced by versions in child scrapers
    _scrape_variants = [
    "<th> Agent </th> {* <tr> {{ [agent_address] }} </tr> *} <th> Applicant </th>",
    "<th> Applicant </th> {* <tr> {{ [applicant_address] }} </tr> *} <th> Date </th>",
    "Decision Despatched <th> Decision </th> <td> {{ decision }} </td>",
    ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        self._adjust_response(response)
        #self.logger.debug("First page html: %s", response.read())
        
        self.logger.debug(scrapeutils.list_forms(self.br))
        
        fields = {}
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        
        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        while response and page_count < max_pages:
            html = response.read()
            url = response.geturl()
            #self.logger.debug("ID batch page html: %s", html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                page_count += 1
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            else:
                self.logger.debug("Empty result after %d pages", page_count)
                break
            try:
                if 'next_link' in self._scrape_next:
                    result = scrapemark.scrape(self._scrape_next, html, url)
                    response = self.br.open(result['next_link'])
                else:
                    scrapeutils.setup_form(self.br, self._scrape_next)
                    self.logger.debug("ID next form: %s", str(self.br.form))
                    response = scrapeutils.submit_form(self.br)
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next form/link after %d pages", page_count)
                break
        
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
            
        return final_result

    def get_html_from_uid (self, uid):
        response = self.br.open(self._search_url)
        self._adjust_response(response)
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
        
    def _adjust_response(self, response): 
        """ fixes bad html that breaks form processing """
        if self._html_subs:
            html = response.get_data()
            for k, v in self._html_subs.items():
                html = re.sub(k, v, html, 0, re.U|re.S|re.I) # unicode|dot matches new line|ignore case
            response.set_data(html)
            self.br.set_response(response)
            
"""class BaberghScraper(AcolNetScraper): # now Idox

    _search_url = 'http://planning.babergh.gov.uk/dcdatav2/AcolNetCGI.gov?ACTION=UNWRAP&RIPNAME=Root.pgesearch'
    _authority_name = 'Babergh'
    _search_form = 'frmSearchByParish'
    _scrape_optional_data = AcolNetScraper._scrape_optional_data + AcolNetScraper._scrape_variants
    detail_tests = [
        { 'uid': 'B/11/00894', 'len': 18 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 25 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 6 } ]

    class BarnetScraper(AcolNetScraper): # now Idox

    _search_url = 'http://planningcases.barnet.gov.uk/planning-cases/acolnetcgi.exe?ACTION=UNWRAP&RIPNAME=Root.pgesearch'
    _authority_name = 'Barnet'
    _search_form = 'frmSearchByWard'
    _scrape_optional_data = AcolNetScraper._scrape_optional_data + AcolNetScraper._scrape_variants
    detail_tests = [
        { 'uid': ' B/03436/12', 'len': 18 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 25 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 6 } ] """

"""class BasingstokeScraper(AcolNetScraper): now Idox

    _search_url = 'http://planning.basingstoke.gov.uk/DCOnline2/AcolNetCGI.dcgov?ACTION=UNWRAP&RIPNAME=Root.pgesearch'
    _authority_name = 'Basingstoke'
    _scrape_optional_data = AcolNetScraper._scrape_optional_data + AcolNetScraper._scrape_variants
    detail_tests = [
        { 'uid': 'B/11/00894', 'len': 18 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 25 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 6 } ]

class BuryScraper(AcolNetScraper): # now Idox

    _search_url = 'http://e-planning.bury.gov.uk/DCWebPages/acolnetcgi.gov?ACTION=UNWRAP&RIPNAME=Root.pgesearch'
    _authority_name = 'Bury'
    _scrape_optional_data = AcolNetScraper._scrape_optional_data + AcolNetScraper._scrape_variants
    detail_tests = [
        { 'uid': '55622', 'len': 21 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 12 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]

class CambridgeshireScraper(AcolNetScraper): # now SwiftLG

    batch_size = 28 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 28 # min number of days to get when gathering current ids
    _search_url = 'http://planapps2.cambridgeshire.gov.uk/DCWebPages/AcolNetCGI.gov?ACTION=UNWRAP&RIPNAME=Root.pgesearch'
    _authority_name = 'Cambridgeshire'
    _search_form = 'frmSearchByParish'
    _scrape_variants = [
    "<th> Agent </th> <td /> {* <td> {{ [agent_address] }} </td> *} <th> Case Type </th>",
    "<th> Applicant </th> <td /> {* <td> {{ [applicant_address] }} </td> *} <th> Date </th>",
    "Decision Despatched <th> Decision </th> <td> {{ decision }} </td>",
    ]
    _scrape_optional_data = AcolNetScraper._scrape_optional_data + _scrape_variants
    detail_tests = [
        { 'uid': 'S/01521/11/CC', 'len': 20 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 12 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ] """

"""class CanterburyScraper(AcolNetScraper): now Idox

    search_url = 'http://www2.canterbury.gov.uk/planning/acolnetcgi.cgi?ACTION=UNWRAP&RIPNAME=Root.PgeSearch'
    _authority_name = 'Canterbury'
    date_from_field = 'edtregdate1'
    date_to_field = 'edtregdate2'
    ref_field = 'edtappno'
    scrape_ids = ""
    <div id="contentcol"> <table> <tr />
    {* <tr> <td> <a href="{{ [records].url|abs }}">
    {{ [records].uid }} </a> </td> </tr> *}
    </table> </div>
    ""
    scrape_next = 'frmNextPage'
    scrape_ref_link = '<div id="contentcol"> <td> <a href="{{ ref_link|abs }}"> </a> </td> </div>'
    scrape_variants = [
    "<th> Agent </th> <td /> {* <td> {{ [agent_address] }} </td> *} <th> Applicant </th>",
    "<th> Applicant </th> <td /> {* <td> {{ [applicant_address] }} </td> *} <th> Decision </th>",
    "Level <th> Decision Date </th> <td> {{ decision_date }} </td> <th> Decision </th> <td> {{ decision }} </td>",
    ] """

"""class CarlisleScraper(AcolNetScraper): now Idox

    search_url = 'http://planning.carlisle.gov.uk/applications/AcolNetCGI.gov?ACTION=UNWRAP&RIPNAME=Root.pgesearch'
    _authority_name = 'Carlisle' """

class CentralBedfordshireScraper(AcolNetScraper):

    _search_url = 'http://www.centralbedfordshire.gov.uk/PLANTECH/DCWebPages/acolnetcgi.gov?ACTION=UNWRAP&RIPNAME=Root.pgesearch'
    _authority_name = 'CentralBedfordshire'
    _search_form = 'frmSearchByParish'
    _scrape_ids = """
    <div id="contentcol">
    {* <table class="results-table">
    <tr> <td class="casenumber"> <a href="{{ [records].url|abs }}">
    {{ [records].uid }} (click for more details) </a> </td> </tr>
    </table> *}
    </div>
    """
    _scrape_min_data = """
    <th> Location </th> <td> {{ address }} </td>
    <th> Description </th> <td> {{ description }} </td>
    """
    _scrape_variants = [
    "<th> Agent </th> <td /> {* <td> {{ [agent_address] }} </td> *} <th> Date </th>",
    "<th> Applicant </th> <td /> {* <td> {{ [applicant_address] }} </td> *} <th> Agent </th>",
    "Decision Despatched <th> Decision </th> <td> {{ decision }} </td>",
    "<td> Details of Planning Application - {{ reference }} </td>"
    ]
    _scrape_optional_data = AcolNetScraper._scrape_optional_data + _scrape_variants
    detail_tests = [
        { 'uid': 'CB/11/02642/ADV', 'len': 19 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 44 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ] 

"""class CroydonScraper(AcolNetScraper): # active but Idox version also active too

    _search_url = 'http://planning.croydon.gov.uk/DCWebPages/acolnetcgi.gov?ACTION=UNWRAP&RIPNAME=Root.pgesearch'
    _authority_name = 'Croydon'
    detail_tests = [
        { 'uid': '11/01369/P', 'len': 20 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 60 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 11 } ] """

"""class DacorumScraper(AcolNetScraper): # now Idox

    _search_url = 'http://site.dacorum.gov.uk/planonline/AcolNetCGI.gov?ACTION=UNWRAP&RIPNAME=Root.pgesearch'
    _authority_name = 'Dacorum'
    _search_form = 'frmSearchByWard'
    _default_timeout = 30
    _html_subs = {
        r'<form name="aspnetForm"[^>]*>': r'',
    }
    _scrape_variants = [
    "<th> Agent </th> <td /> {* <td> {{ [agent_address] }} </td> *} <th> Case Type </th>",
    "<th> Applicant </th> <td /> {* <td> {{ [applicant_address] }} </td> *} <th> Date </th>",
    "Decision Despatched <th> Decision </th> <td> {{ decision }} </td>",
    ]
    _scrape_optional_data = AcolNetScraper._scrape_optional_data + _scrape_variants
    detail_tests = [
        { 'uid': '4/01130/11/FUL', 'len': 22 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 44 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 11 } ]"""

"""class DerbyScraper(AcolNetScraper): # now Idox

    search_url = 'http://eplanning.derby.gov.uk/acolnet/planningpages02/acolnetcgi.exe?ACTION=UNWRAP&RIPNAME=Root.pgesearch'
    _authority_name = 'Derby'
    scrape_ids = ""
    <div id="contentcol">
    {* <table class="results-table">
    <tr> <td class="casenumber"> <a href="{{ [records].url|abs }}">
    {{ [records].uid }} - link to more details </a> </td> </tr>
    </table> *}
    </div>
    ""
    scrape_variants = [
    "<th> Agent </th> <td> <p> {{ agent_name }} </p> {* <p> {{ [agent_address] }} </p> *} </td> <th> Applicant </th>",
    "<th> Applicant </th> <td> <p> {{ applicant_name }} </p> {* <p> {{ [applicant_address] }} </p> *} </td> <th> Date </th>",
    "Decision Made <th> Decision </th> <td> {{ decision }} </td>",
    ]"""
    
class ExeterScraper(AcolNetScraper):

    _search_url = 'http://pub.exeter.gov.uk/scripts/acolnet/planning/AcolnetCGI.gov?ACTION=UNWRAP&RIPNAME=Root.pgesearch'
    _authority_name = 'Exeter'
    _search_form = 'frmSearchByWard'
    _default_timeout = 20
    _scrape_variants = [
    "<th> Agent </th> <td /> {* <td> {{ [agent_address] }} </td> *} <th> Case Type </th>",
    "<th> Applicant </th> <td /> {* <td> {{ [applicant_address] }} </td> *} <th> Date </th>",
    "Decision Despatched <th> Decision </th> <td> {{ decision }} </td>",
    "<td> Details of Planning Application - {{ reference }} </td>"
    ]
    _scrape_optional_data = AcolNetScraper._scrape_optional_data + _scrape_variants
    detail_tests = [
        { 'uid': '11/1409/07', 'len': 24 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 21 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 } ]
        
    # SSL EOF error on Exeter site
    # with mechanize -> urlopen error EOF occurred in violation of protocol (_ssl.c:590)
    # with requests -> "bad handshake: SysCallError(-1, 'Unexpected EOF')"
    # The site offers mainly insecure SSL protocols - see
    # https://www.ssllabs.com/ssltest/analyze.html?d=pub.exeter.gov.uk
    # kludge fix is just to force not to use https URLs at any point
    
    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        self._adjust_response(response)
        #self.logger.debug("First page html: %s", response.read())
        
        self.logger.debug(scrapeutils.list_forms(self.br))
        
        fields = {}
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        action = self.br.form.action
        self.br.form.action = action.replace('https://', 'http://')
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        
        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        while response and page_count < max_pages:
            html = response.read()
            url = response.geturl()
            #self.logger.debug("ID batch page html: %s", html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                page_count += 1
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            else:
                self.logger.debug("Empty result after %d pages", page_count)
                break
            try:
                if 'next_link' in self._scrape_next:
                    result = scrapemark.scrape(self._scrape_next, html, url)
                    response = self.br.open(result['next_link'])
                else:
                    scrapeutils.setup_form(self.br, self._scrape_next)
                    action = self.br.form.action
                    self.br.form.action = action.replace('https://', 'http://')
                    self.logger.debug("ID next form: %s", str(self.br.form))
                    response = scrapeutils.submit_form(self.br)
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next form/link after %d pages", page_count)
                break
        
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
            
        return final_result
        
    def get_html_from_uid (self, uid):
        response = self.br.open(self._search_url)
        self._adjust_response(response)
        #self.logger.debug("ID detail start html: %s", response.read())
        fields = {  self._ref_field: uid }
        scrapeutils.setup_form(self.br, self._search_form, fields)
        action = self.br.form.action
        self.br.form.action = action.replace('https://', 'http://')
        #self.logger.debug("Get UID form: %s", str(self.br.form))
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
        
    def get_html_from_url(self, url):
        """ Get the html and url for one record given a URL """
        if self._uid_only:
            return None, None
        if self._search_url and self._detail_page:
            url_parts = urlparse.urlsplit(url)
            url = urlparse.urljoin(self._search_url, self._detail_page)
            if url_parts.query:
                url = url + '?' + url_parts.query
        url = url.replace('https://', 'http://')
        response = self.br.open(url) # use mechanize, to get same handler interface as elsewhere
        return self._get_html(response)
        
    def _clean_record(self, record):
        super(ExeterScraper, self)._clean_record(record)
        if record.get('url'):
            record['url'] = record['url'].replace('https://', 'http://')

"""class GreenwichScraper(AcolNetScraper): # now Idox

    _search_url = 'http://onlineplanning.greenwich.gov.uk/acolnet/planningonline/acolnetcgi.gov?ACTION=UNWRAP&RIPNAME=Root.pgesearch'
    _authority_name = 'Greenwich'
    search_form = 'frmSearchByWard'

class GuildfordScraper(AcolNetScraper): # now Idox

    _search_url = 'http://www2.guildford.gov.uk/DLDC_Version_2/acolnetcgi.gov?ACTION=UNWRAP&RIPNAME=Root.pgesearch'
    _authority_name = 'Guildford'
    scrape_variants = [
    "<th> Agent </th> <td /> {* <td> {{ [agent_address] }} </td> *} <th> Case Type </th>",
    "<th> Applicant </th> <td /> {* <td> {{ [applicant_address] }} </td> *} <th> Neighbours </th>",
    "Level <th> Decision Date </th> <td> {{ decision_date }} </td> <th> Decision </th> <td> {{ decision }} </td>",
    "<th> Location </th> <td> {{ address }} <a/> </td>",
    ]

class HarlowScraper(AcolNetScraper): # now Fastweb

    search_url = 'http://planning.harlow.gov.uk/DLDC_Version_2/acolnetcgi.exe?ACTION=UNWRAP&RIPNAME=Root.pgesearch'
    _authority_name = 'Harlow'

class HavantScraper(AcolNetScraper): # now Idox

    _search_url = 'http://www5.havant.gov.uk/ACOLNETDCOnline/acolnetcgi.gov?ACTION=UNWRAP&RIPNAME=Root.pgesearch'
    _authority_name = 'Havant'
    _scrape_optional_data = AcolNetScraper._scrape_optional_data + AcolNetScraper._scrape_variants
    detail_tests = [
        { 'uid': 'APP/11/01323', 'len': 17 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 44 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ]


class HertsmereScraper(AcolNetScraper): # now Idox

    search_url = 'http://www2.hertsmere.gov.uk/ACOLNET/DCOnline//acolnetcgi.gov?ACTION=UNWRAP&RIPNAME=Root.pgesearch'
    _authority_name = 'Hertsmere'

class LewishamScraper(AcolNetScraper): # now Idox

    search_url = 'http://acolnet.lewisham.gov.uk/lewis-xslpagesdc/acolnetcgi.exe?ACTION=UNWRAP&RIPNAME=Root.pgesearch'
    _authority_name = 'Lewisham'
    date_from_field = 'edtregdate1'
    date_to_field = 'edtregdate2'
    ref_field = 'edtappno'

class MedwayScraper(AcolNetScraper): # now Idox

    search_url = 'http://planning.medway.gov.uk/DCOnline/AcolNetCGI.gov?ACTION=UNWRAP&RIPNAME=Root.pgesearch'
    _authority_name = 'Medway'
    search_form = 'frmSearchByWard'

class NewForestScraper(AcolNetScraper): # now both Idox

    search_url = 'http://web3.newforest.gov.uk/planningonline/acolnetcgi.gov?ACTION=UNWRAP&RIPNAME=Root.pgesearch'
    _authority_name = 'NewForest'
    search_form = 'frmSearchByParish'
    scrape_variants = [
    "<th> Agent </th> <td /> {* <td> {{ [agent_address] }} </td> *} <th> Applicant </th>",
    "<th> Applicant </th> <td /> {* <td> {{ [applicant_address] }} </td> *} <th> Date </th>",
    "Level <th> Decision Date </th> <td> {{ decision_date }} </td> <th> Decision </th> <td> {{ decision }} </td>",
    "<th> Case Officer </th> <td> {{ case_officer }} Return to Search Page </td>",
    ]

class NewForestParkScraper(AcolNetScraper): # this is the national park, not the local authority

    search_url = 'http://web01.newforestnpa.gov.uk/Pages3/AcolNetCGI.dcgov?ACTION=UNWRAP&RIPNAME=Root.pgesearch'
    _authority_name = 'NewForestPark'
    search_form = 'frmSearchByParish'
    scrape_variants = [
    "<th> Agent </th> <td /> {* <td> {{ [agent_address] }} </td> *} <th> Applicant </th>",
    "<th> Applicant </th> <td /> {* <td> {{ [applicant_address] }} </td> *} <th> Date </th>",
    "Site Visit <th> Decision </th> <td> {{ decision }} </td>",
    ]

class NorthHertfordshireScraper(AcolNetScraper): # now Idox

    search_url = 'http://www.north-herts.gov.uk/dcdataonline/Pages/AcolNetCGI.gov?ACTION=UNWRAP&RIPNAME=Root.pgesearch'
    _authority_name = 'NorthHertfordshire'

class NorthNorfolkScraper(AcolNetScraper): # now Idox

    search_url = 'http://planweb.north-norfolk.gov.uk/Planning/AcolNetCGI.exe?ACTION=UNWRAP&RIPNAME=Root.pgesearch'
    _authority_name = 'NorthNorfolk'
    search_form = 'frmSearchByParish'
    scrape_variants = [
    "<th> Agent </th> <td /> {* <td> {{ [agent_address] }} </td> *} <th> Case Type </th>",
    "<th> Applicant </th> <td /> {* <td> {{ [applicant_address] }} </td> *} <th> Date </th>",
    "Decision Despatched <th> Decision </th> <td> {{ decision }} </td>",
    ]

class NorthWiltshireScraper(AcolNetScraper): # now PlanningExplorer

    search_url = 'http://northplanning.wiltshire.gov.uk/DCOnline/acolnetcgi.gov?ACTION=UNWRAP&RIPNAME=Root.pgesearch'
    _authority_name = 'NorthWiltshire'

class RenfrewshireScraper(AcolNetScraper): # now Idox

    search_url = 'http://planning.renfrewshire.gov.uk/dcwebpages02/acolnetcgi.gov?ACTION=UNWRAP&RIPNAME=Root.pgesearch'
    _authority_name = 'Renfrewshire'
    date_from_field = 'recdate1'
    date_to_field = 'recdate2'
    scrape_variants = [
    "<th> Agent </th> <td /> {* <td> {{ [agent_address] }} </td> *} <th> Applicant </th>",
    "<th> Applicant </th> <td /> {* <td> {{ [applicant_address] }} </td> *} <th> Decision </th>",
    "Applicant <th> Decision </th> <td> {{ decision }} </td>",
    "<th> Community Council </th> <td> {{ parish }} </td>",
    ]

class SouthwarkScraper(AcolNetScraper): # now Idox

    search_url = 'http://planningonline.southwarksites.com/planningonline2/AcolNetCGI.exe?ACTION=UNWRAP&RIPNAME=Root.pgesearch'
    _authority_name = 'Southwark'
    scrape_variants = [
    "<th> Agent </th> <td /> {* <td> {{ [agent_address] }} </td> *} <th> Ward </th>",
    "<th> Applicant </th> <td /> {* <td> {{ [applicant_address] }} </td> *} <th> Agent </th>",
    "Applicant <th> Decision Made </th> <td> {{ decision_date }} </td> <th> Decision </th> <td> {{ decision }} </td>",
    "<th> Community Council </th> <td> {{ parish }} </td>",
    ]

class StockportScraper(AcolNetScraper): # now Idox

    search_url = 'http://planning.stockport.gov.uk/PlanningData/AcolNetCGI.gov?ACTION=UNWRAP&RIPNAME=Root.pgesearch'
    _authority_name = 'Stockport'
    search_form = 'frmSearchByWard'

class StokeOnTrentScraper(AcolNetScraper): # now Idox

    search_url = 'http://www.planning.stoke.gov.uk/dataonlineplanning/AcolNetCGI.exe?ACTION=UNWRAP&RIPNAME=Root.pgesearch'
    _authority_name = 'StokeOnTrent'

class SuffolkCoastalScraper(AcolNetScraper): # now Idox

    search_url = 'http://apps3.suffolkcoastal.gov.uk/DCDataV2/acolnetcgi.gov?ACTION=UNWRAP&RIPNAME=Root.pgesearch'
    _authority_name = 'SuffolkCoastal'

class WirralScraper(AcolNetScraper): now Idox

    _search_url = 'http://www.wirral.gov.uk/planning/DC/AcolNetCGI.gov?ACTION=UNWRAP&RIPNAME=Root.pgesearch'
    _authority_name = 'Wirral'
    _search_form = 'frmSearchByWard'
    _scrape_variants = [
    "<th> Agent </th> <td /> {* <td> {{ [agent_address] }} </td> *} <th> Case Type </th>",
    "<th> Applicant </th> <td /> {* <td> {{ [applicant_address] }} </td> *} <th> Neighbours </th>",
    "Decision Despatched <th> Decision </th> <td> {{ decision }} </td>",
    ]
    _scrape_optional_data = AcolNetScraper._scrape_optional_data + _scrape_variants
    detail_tests = [
        { 'uid': 'APP/11/00960', 'len': 21 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 31 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 7 } ]"""

