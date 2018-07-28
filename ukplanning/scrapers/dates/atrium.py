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
import mechanize

class AtriumScraper(base.DateScraper):

    min_id_goal = 100 # min target for application ids to fetch in one go
    batch_size = 28 # batch size for each scrape - number of days to gather to produce at least TWO results each time (a list)
    current_span = 28 # start this number of days ago when gathering current ids

    _scraper_type = 'Atrium'
    _date_from_field = { 'day': 'dayRegStart', 'month': 'monthRegStart', 'year': 'yearRegStart', }
    _date_to_field = { 'day': 'dayRegEnd', 'month': 'monthRegEnd', 'year': 'yearRegEnd', }
    _detail_page = 'loadFullDetails.do'
    _ref_field = 'aplRef'
    _search_form = 'SearchForms'
    _request_date_format = '%d/%b/%Y'

    _scrape_ids = """
    <div class="sectionHeaderBackground_Dark"> Planning Applications Found: </div>
    <table>
    {* <tr> <td> Application Ref No. </td> <td> {{ [records].uid }} </td> </tr> 
    <tr> <a href="{{ [records].url|abs }}"> </a> </tr>
    *}
    </table>
    """
    _scrape_id = """
    <body> <p> Main Details </p> 
    <tr> <td> Application Number </td> <td> {{ uid }} </td> </tr> </body>
    """

    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <body> <p> Main Details </p> {{ block|html }} </body>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <tr> <td> Application Number </td> <td> {{ reference }} </td> </tr>
    <tr> <td> Date Registered </td> <td> {{ date_validated }} </td> </tr>
    <tr> <td> Date Valid </td> <td> {{ date_received }} </td> </tr>
    <tr> <td> Location </td> <td> {{ address }} </td> </tr>
    <tr> <td> Proposal </td> <td> {{ description }} </td> </tr>
    """
    # other optional parameters that can appear on an application page
    # checked against Suffolk, Somerset
    _scrape_optional_data = [
    "<tr> <td> Application Type </td> <td> {{ application_type }} </td> </tr>", 
    "<tr> <td> Application Status/Decision </td> <td> {{ status }} </td> </tr>", 
    "<tr> <td> Case Officer </td> <td> {{ case_officer }} </td> </tr>", 
    "<tr> <td> Ward </td> <td> {{ ward_name }} </td> </tr>", 
    "<tr> <td> Parish\Town </td> <td> {{ parish }} </td> </tr>", 
    "<tr> <td> Parish </td> <td> {{ parish }} </td> </tr>", 
    "<tr> <td> Council </td> <td> {{ district }} </td> </tr>", 
    "<tr> <td> Applicant </td> <td> {{ applicant_name }} </td> </tr>", 
    "<tr> <td> Agent </td> <td> {{ agent_name }} </td> </tr>", 

    "<tr> <td> Committee Date </td> <td> {{ meeting_date }} </td> </tr>",
    "<tr> <td> Consultation Start Date </td> <td> {{ consultation_start_date }} </td> </tr>",
    "<tr> <td> Consultation End Date </td> <td> {{ consultation_end_date }} </td> </tr>",

    "<tr> <td> Determination Target </td> <td> {{ target_decision_date }} </td> </tr>",
    "<tr> <td> Determine By </td> <td> {{ target_decision_date }} </td> </tr>",
    "<tr> <td> Decision </td> <td> {{ decision }} </td> </tr> <tr> <td> Decision Date </td> <td> {{ decision_date }} </td> </tr>", 
    "<tr> <td> Decision Method </td> <td> {{ decided_by }} </td> </tr>", 

    "<tr> <td> Appeal Date </td> <td> {{ appeal_date }} </td> </tr>", 
    "<tr> <td> Appeal Decision </td> <td> {{ appeal_result }} </td> </tr>", 
    "<tr> <td> Hearing Date </td> <td> {{ appeal_decision_date }} </td> </tr>", 
    ]

    def get_id_batch (self, date_from, date_to):
        
        final_result = []
        response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s", response.read())
        
        fields = {}
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
        #self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        
        if response:
            html = response.read() 
            url = response.geturl()
            #self.logger.debug("Batch html: %s" % html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            if not final_result: # is it a single record?
                single_result = scrapemark.scrape(self._scrape_id, html, url)
                if single_result:
                    single_result['url'] = url
                    self._clean_record(single_result)
                    final_result = [ single_result ]
        return final_result

    # post process a set of uid/url records: converts the uid
    def _clean_record(self, record):
        super(AtriumScraper, self)._clean_record(record)
        if record.get('uid'):
            record['uid'] = re.sub(r'([^\(\)$]+).*', r'\1', record['uid'], 1, re.U)
            record['uid'] = record['uid'].replace('\\', '/')

    def get_html_from_uid(self, uid):
        response = self.br.open(self._search_url)
        #self.logger.debug("ID detail start html: %s", response.read())
        fields = {}
        fields[self._ref_field] = uid
        scrapeutils.setup_form(self.br, self._search_form, fields)
        #self.logger.debug("Get UID form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        html, url = self._get_html(response)
        # note return can be a single uid match page OR list of multiple matches
        result = scrapemark.scrape(self._scrape_ids, html, url)
        if result and result.get('records'):
            self._clean_ids(result['records'])
            for r in result['records']:
                if r.get('uid', '') == uid and r.get('url'):
                    self.logger.debug("Scraped url: %s", r['url'])
                    return self.get_html_from_url(r['url'])
            return None, None
        else:
            return html, url # this URL is unique via GET, so OK to update 'url' field from it
            
class SomersetScraper(AtriumScraper): 

    _authority_name = 'Somerset'
    data_start_target = '2004-02-01' # gathers id data by working backwards from the current date towards this one
    _search_url = 'http://schpwebapppln.somerset.gov.uk/ePlanning/searchPageLoad.do'
    detail_tests = [
        { 'uid': 'PL/1967/10', 'len': 17 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '24/09/2012', 'len': 8 }, 
        { 'from': '22/08/2012', 'to': '22/08/2012', 'len': 1 } ]
        
class SuffolkScraper(AtriumScraper):
    
    import ssl
    # Above Python 2.7.9 default HTTPS behaviour has changed - now always verifies remote HTTPS certificate
    # Causes SSL errors on this site - urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:590)
    # See kludge fix here and Halton and Castle Point
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass # Legacy Python that doesn't verify HTTPS certificates by default
    else:
        # Handle target environment that doesn't support HTTPS verification
        ssl._create_default_https_context = _create_unverified_https_context

    _authority_name = 'Suffolk'
    #_search_url = 'http://atrium.suffolkcc.gov.uk/ePlanning/searchPageLoad.do?advanced=Y'
    _search_url = 'https://secure.suffolkcc.gov.uk/ePlanning/searchPageLoad.do?advanced=Y'
    detail_tests = [
        { 'uid': 'PL/0258/11', 'len': 19 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '24/09/2012', 'len': 2 }, 
        { 'from': '16/08/2012', 'to': '16/08/2012', 'len': 1 } ]
        
    # note a bug on this server means if the result is a single record it redirects
    # to the result page using the http protocol which results in a 403 error
    # so we catch those events here, and change the URLs to use https protocol
    def get_html_from_uid(self, uid):
        try:
            return super(SuffolkScraper, self).get_html_from_uid(uid)
        except (mechanize.HTTPError) as e:
            url = e.geturl()
            if e.code in [403, 404, 503] and 'http://secure.suffolkcc.gov.uk' in url:
                url = url.replace('http://', 'https://')
                return self.get_html_from_url(url)
            else:
                raise
                
    def get_id_batch(self, date_from, date_to):
        try:
            return super(SuffolkScraper, self).get_id_batch(date_from, date_to)
        except (mechanize.HTTPError) as e:
            url = e.geturl()
            if e.code in [403, 404, 503] and 'http://secure.suffolkcc.gov.uk' in url:
                html, url = self.get_html_from_url(url)
                single_result = scrapemark.scrape(self._scrape_id, html, url)
                if single_result:
                    single_result['url'] = url
                    self._clean_record(single_result)
                    return [ single_result ]
                else:
                    raise
            else:
                raise
        
class WestSussexScraper(AtriumScraper):

    data_start_target = '2004-01-08'
    batch_size = 42 # batch size for each scrape - number of days to gather to produce at least TWO results (a list) each time
    
    _authority_name = 'WestSussex'
    _search_url = 'http://buildings.westsussex.gov.uk/ePlanningOPS/searchPageLoad.do'
    detail_tests = [
        { 'uid': 'WSCC/056/11/SU', 'len': 20 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '24/09/2012', 'len': 5 }, 
        { 'from': '15/08/2012', 'to': '15/08/2012', 'len': 2 } ]
        
class KentScraper(AtriumScraper):

    _authority_name = 'Kent'
    data_start_target = '2004-02-01' # gathers id data by working backwards from the current date towards this one
    #_search_url = 'http://host1.atriumsoft.com/ePlanningOPSkent/searchPageLoad.do'
    _search_url = 'https://cloud2.atriumsoft.com/KCCePlanningOPS/searchPageLoad.do?advanced=Y'
    detail_tests = [
        { 'uid': 'KCC/TM/0403/2011', 'len': 20 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '24/09/2012', 'len': 11 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ]
        
class LeicestershireScraper(AtriumScraper):

    _authority_name = 'Leicestershire'
    data_start_target = '2004-02-05' # gathers id data by working backwards from the current date towards this one
    _search_url = 'https://cloud2.atriumsoft.com/LCCePlanning/searchPageLoad.do'
    #_search_url = 'http://planning.leics.gov.uk/ePlanning/searchPageLoad.do'
    detail_tests = [
        { 'uid': '2011/0752/04', 'len': 19 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '24/09/2012', 'len': 22 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 2 } ]
        
class CumbriaScraper(AtriumScraper): # very slow site

    _authority_name = 'Cumbria'
    data_start_target = '2004-02-01' # gathers id data by working backwards from the current date towards this one
    min_id_goal = 50 # min target for application ids to fetch in one go
    #_search_url = 'http://onlineplanning.cumbria.gov.uk/ePlanningOPS/searchPageLoad.do'
    _search_url = 'https://cloud2.atriumsoft.com/ePlanningCMB/searchPageLoad.do'
    detail_tests = [
        { 'uid': 'PL/0904/05', 'len': 17 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '24/09/2012', 'len': 1 }, 
        { 'from': '15/08/2012', 'to': '15/08/2012', 'len': 1 } ]
        
class HertfordshireScraper(AtriumScraper): # low numbers

    _authority_name = 'Hertfordshire'
    data_start_target = '2004-02-01' # gathers id data by working backwards from the current date towards this one
    batch_size = 60 # batch size for each scrape - number of days to gather to produce at least TWO results (a list) each time
    #_search_url = 'https://www.hertsdirect.org/ePlanningOPS/searchPageLoad.do'
    _search_url = 'https://cloud1.atriumsoft.com/HCCePlanningOPS/searchPageLoad.do'
    detail_tests = [
        { 'uid': 'PL/0382/11', 'len': 18 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '24/09/2012', 'len': 1 }, 
        { 'from': '20/08/2012', 'to': '20/08/2012', 'len': 1 } ]
        
class LincolnshireScraper(AtriumScraper):

    _authority_name = 'Lincolnshire'
    data_start_target = '2005-10-12'
    batch_size = 42 # batch size for each scrape - number of days to gather to produce at least TWO results (a list) each time
    _search_url = 'http://eplanning.lincolnshire.gov.uk/ePlanning/searchPageLoad.do?advanced=Y'
    detail_tests = [
        { 'uid': 'PL/0155/11', 'len': 20 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '24/09/2012', 'len': 2 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 1 } ]
        
class DorsetScraper(AtriumScraper):

    _authority_name = 'Dorset'
    _search_url = 'http://countyplanning.dorsetforyou.com/ePlanningOPS/searchPageLoad.do'
    detail_tests = [
        { 'uid': 'PL/1237/11', 'len': 15 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '24/09/2012', 'len': 41 }, 
        { 'from': '17/08/2012', 'to': '17/08/2012', 'len': 1 } ]
        

