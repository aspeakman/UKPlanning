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
import re
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
try:
    from ukplanning import myutils
except ImportError:
    import myutils
import mechanize

class PlanningExplorerScraper(base.DateScraper):

    min_id_goal = 300 # min target for application ids to fetch in one go
    
    _scraper_type = 'PlanningExplorer'
    _handler = 'etree' # note definitely need this as HTML is pretty rubbish, also see HTML subs for bad characters in URLs below
    _headers = {
    'Accept-Charset': 'UTF-8,*',
    'Accept': 'text/html',
    'User-Agent': 'Mozilla/5.0 (Windows; U; MSIE 7.0; Windows NT 6.0; en-US)',
    }
    _date_from_field = 'dateStart'
    _date_to_field = 'dateEnd'
    _ref_field = 'txtApplicationNumber'
    _detail_page = 'Generic/StdDetails.aspx'
    _search_fields = { 'rbGroup': ['rbRange'] }
    _search_form = 'M3Form'
    _search_submit = '#csbtnSearch'
    _applic_fields = { 'rbGroup': ['rbNotApplicable'] }
    _scrape_dates_link = '<a href="{{ dates_link }}"> Application Dates </a>'
    _html_subs = {}
    _scrape_ids = """
    <table class="display_table"> <tr />
    {* <tr>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    </tr> *}
    </table>
    """
    _scrape_no_recs = '<div id="pageCenter"> {{ no_recs }} any results </div>'
    _scrape_next_link = '<a href="{{ next_link }}"> <img title="Go to next page"> </a>'
    
    _BADCHARS_REGEX = re.compile(r'%0D|%0A|%09|&#194;&#160;|&#xD;|&#xA;|&#x9;')

    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = '<body> Details Page {{ block|html }} </body>'
    _scrape_dates_block = '<body> Dates Page {{ block|html }} </body>'
    # the minimum acceptable valid dataset on the details page
    _scrape_min_data = """
    <li> <span> Application Registered </span> {{ date_validated }} </li>
    <li> <span> Application Number </span> {{ reference }} </li>
    <li> <span> Site Address </span> {{ address }} </li>
    <li> <span> Proposal </span> {{ description }} </li>
    """
    _scrape_min_dates = """
    <li> <span> Received </span> {{ date_received }} </li>
    """
    # min field list used in testing only
    _min_fields = [ 'reference', 'address', 'description', 'date_received' ]
    # other optional parameters that can appear on the details page
    _scrape_optional_data = [
    "<li> <span> Application Type </span> {{ application_type }} </li>",
    "<li> <span> Current Status </span> {{ status }} </li>",
    "<li> <span> Applicant </span> {{ applicant_name }} </li>",
    "<li> Applicant </li> <li> <span> Applicant Address </span> {{ applicant_address }} </li>",
    "<li> <span> Agent </span> {{ agent_name }} </li>",
    "<li> Agent </li> <li> <span> Agent Address </span> {{ agent_address }} </li>",
    "<li> <span> Ward </span> {{ ward_name }} </li>",
    "<li> <span> Electoral Division </span> {{ ward_name }} </li>",
    "<li> <span> Parishes </span> {{ parish }} </li>",
    "<li> <span> Parish </span> {{ parish }} </li>",
    "<li> <span> Community Council </span> {{ parish }} </li>",
    "<li> <span> Comments Until </span> {{ comment_date }} </li>",
    "<li> <span> Comments Welcome Until </span> {{ comment_date }} </li>",
    "<li> <span> Date of Committee </span> {{ meeting_date }} </li>",
    "<li> <span> Committee Date </span> {{ meeting_date }} </li>",
    "<li> <span> Decision </span> {{ decision }} </li>", 
    "<li> <span> Appeal Lodged </span> {{ appeal_date }} </li>",
    "<li> <span> Appeal Logged </span> {{ appeal_date }} </li>",
    "<li> <span> Appeal Decision </span> {{ appeal_result }} </li>",
    "<li> <span> Appeal Decision </span> {{ appeal_result }} </li> <li> <span> Appeal Decision Date </span> {{ appeal_decision_date }} </li>",
    "<li> <span> Appeal Date </span> {{ appeal_date }} </li> <li> <span> Appeal Decision Date </span> {{ appeal_decision_date }} </li>",
    "<li> <span> Officer </span> {{ case_officer }} </li>",
    "<li> <span> District </span> {{ district }} </li>",
    "<li> <span> Constituency </span> {{ district }} </li>",
    "<li> <span> Determination Level </span> {{ decided_by }} </li>",
    "<li> Easting {{ easting }} Northing {{ northing }} </li>",
    "<li> <span> Development Type </span> {{ development_type }} </li>",
    "<li> <span> Consultation Period Ends </span> {{ consultation_end_date }} </li>",
    "<li> <span> Expiry Date for Consultations </span> {{ consultation_end_date }} </li>",
    "<li> <span> Committee Date </span> {{ meeting_date }} </li> <li> <span> Decision Date </span> {{ decision_date }} </li>",
    ]
    _scrape_optional_dates = [
    "<li> <span> Registered </span> {{ date_validated }} </li>",
    "<li> <span> Validated </span> {{ date_validated }} </li>",
    "<li> <span> Valid From </span> {{ date_validated }} </li>",
    "<li> <span> Consultation Expiry </span> {{ consultation_end_date }} </li>",
    "<li> <span> Consultation Period Ends </span> {{ consultation_end_date }} </li>",
    "<li> <span> Date of First Consultation </span> {{ consultation_start_date }} </li>",
    "<li> <span> Statutory Expiry </span> {{ application_expires_date }} </li>",
    "<li> <span> Decision Expiry </span> {{ permission_expires_date }} </li>",
    "<li> <span> Target Date </span> {{ target_decision_date }} </li>",
    "<li> <span> Target Decision Date </span> {{ target_decision_date }} </li>",
    ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        self._adjust_response(response)
        #self.logger.debug("Start html: %s", response.read())
        
        fields = self._search_fields
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        #self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._search_submit)
        
        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        while response and page_count < max_pages:
            html = response.read()
            url = response.geturl()
            sub_html = self._BADCHARS_REGEX.sub(' ', html)
            ##self.logger.debug("ID batch page html: %s", sub_html)
            result = scrapemark.scrape(self._scrape_ids, sub_html, url)
            if result and result.get('records'):
                page_count += 1
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            else:
                self.logger.debug("Empty result after %d pages", page_count)
                break
            try:
                result = scrapemark.scrape(self._scrape_next_link, sub_html, url)
                #print result
                next_url = myutils.GAPS_REGEX.sub('', result['next_link'])
                self.logger.debug("ID next url: %s", next_url)
                response = self.br.open(next_url)
                self._adjust_response(response)
            except: # normal failure to find next page link at end of page sequence here
                self.logger.debug("No next link after %d pages", page_count)
                break
                
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
                
        return final_result
        
    def get_html_from_uid (self, uid):
        response = self.br.open(self._search_url)
        self._adjust_response(response)
        #self.logger.debug("ID detail start html: %s", response.read())
        fields = self._applic_fields
        fields [ self._ref_field ] = uid
        scrapeutils.setup_form(self.br, self._search_form, fields)
        response = scrapeutils.submit_form(self.br, self._search_submit)
        html, url = self._get_html(response)
        sub_html = self._BADCHARS_REGEX.sub(' ', html)
        #self.logger.debug("Detail page html: %s", sub_html)
        result = scrapemark.scrape(self._scrape_ids, sub_html, url)
        #print result
        if result and result.get('records'):
            self._clean_ids(result['records'])
            for r in result['records']:
                if r.get('uid', '') == uid and r.get('url'):
                    self.logger.debug("Scraped url: %s", r['url'])
                    return self.get_html_from_url(r['url'])
        return None, None
        
    def _get_details(self, html, this_url):
        """ Scrapes detailed information for one record given html and url 
        - this is an optional hook to allow data from multiple linked pages to be merged """
        sub_html = self._BADCHARS_REGEX.sub(' ', html)
        result = self._get_detail(sub_html, this_url)
        if 'scrape_error' in result or not self._scrape_dates_link:
            return result
        try:
            date_result = scrapemark.scrape(self._scrape_dates_link, sub_html, this_url)
            dates_url = myutils.GAPS_REGEX.sub('', date_result['dates_link'])
            self.logger.debug("Dates url: %s", dates_url)
            response = self.br.open(dates_url)
            self._adjust_response(response)
            html, url = self._get_html(response)
            sub_html = self._BADCHARS_REGEX.sub(' ', html)
        except:
            self.logger.warning("No link to dates page found")
        else:
            #self.logger.debug("Html obtained from dates url: %s", html)
            result2 = self._get_detail(sub_html, url, self._scrape_dates_block, self._scrape_min_dates, self._scrape_optional_dates)
            if 'scrape_error' not in result2:
                result.update(result2)
            else:
                self.logger.warning("No information found on dates page")
        return result
        
    def _adjust_response(self, response): 
        """ fixes bad html that breaks form processing """
        if self._html_subs:
            html = response.get_data()
            for k, v in self._html_subs.items():
                html = re.sub(k, v, html, 0, re.U|re.S|re.I) # unicode|dot matches new line|ignore case
            response.set_data(html)
            self.br.set_response(response)

class BarnsleyScraper(PlanningExplorerScraper): # note different from other Planning Explorer scraper

    min_id_goal = 300 # min target for application ids to fetch in one go
    batch_size = 24 # batch size for each scrape - number of days to gather to produce at least one result each time
    
    _authority_name = 'Barnsley'
    _search_url = 'https://wwwapplications.barnsley.gov.uk/PlanningExplorerMVC/Home/AdvanceSearch'
    _date_from_field = 'dateReceivedFrom'
    _date_to_field = 'dateReceivedTo'
    _ref_field = 'ApplicationNumber'
    _detail_page = 'ApplicationDetails'
    _search_form = '0'
    _scrape_ids = """
    <tbody> 
    {* <tr>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    </tr> *}
    </tbody>
    """
    _scrape_max_recs = "<strong> Results for Application Search : {{ max_recs }} </strong>"

    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = '<body> {{ block|html }} <footer /> </body>'
    # the minimum acceptable valid dataset on the details page
    _scrape_min_data = """
    <tr> <td> Reference Number </td> <td> {{ reference }} </td> </tr>
    <tr> <td> Description </td> <td> {{ description }} </td> </tr>
    <tr> <td> Site Address </td> <td> {{ address }} </td> </tr>
    <tr> <td> Received Date </td> <td> {{ date_received }} </td> </tr>
    """
    _scrape_dates_link = None
    _min_fields = [ 'reference', 'address', 'description' ] # min field list used in testing only
    # other optional parameters that can appear on the details page
    _scrape_optional_data = [
    '<tr> <td> Validated Date </td> <td> {{ date_validated }} </td> </tr>',
    """<tr> <td> Decision </td> <td> {{ decision }} </td> </tr>
    <tr> <td> Status </td> <td> {{ status }} </td> </tr>""",
    "<tr> <td> Ward </td> <td> {{ ward_name }} </td> </tr>",
    "<tr> <td> Parish </td> <td> {{ parish }} </td> </tr>",
    "<tr> <td> Application Type </td> <td> {{ application_type }} </td> </tr>",
    "<tr> <td> Applicant Name </td> <td> {{ applicant_name }} </td> </tr>",
    "<tr> <td> Applicant Address </td> <td> {{ applicant_address }} </td> </tr>",
    "<tr> <td> Agent Name </td> <td> {{ agent_name }} </td> </tr>",
    "<tr> <td> Agent Address </td> <td> {{ agent_address }} </td> </tr>",
    "<tr> <td> Determination Level </td> <td> {{ decided_by }} </td> </tr>",
    "<tr> <td> Case Officer Name </td> <td> {{ case_officer }} </td> </tr>",
    "<tr> <td> Consultation Expiry Date </td> <td> {{ consultation_end_date }} </td> </tr>",
    """<tr> <td> Target Decision Date </td> <td> {{ target_decision_date }} </td> </tr>
    Extended <tr> <td> Decision Date </td> <td> {{ decision_date }} </td> </tr>""",
    ]
    detail_tests = [
        { 'uid': '2011/1001', 'len': 19 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 23 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 11 } ]
    
    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s", response.read())
        
        fields = {}
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
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
        
        return final_result
    
    def get_html_from_uid(self, uid):
        url = urlparse.urljoin(self._search_url, self._detail_page) + '?planningApplicationNumber=' + urllib.quote_plus(uid)
        return self.get_html_from_url(url)
        
class BirminghamScraper(PlanningExplorerScraper): # NB does not like returning large numbers
    # nested form on this site
    # <form class="site-search form form--search" action="">

    batch_size = 5 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 15 # min number of days to get when gathering current ids
    min_id_goal = 250 # min target for application ids to fetch in one go
    
    _authority_name = 'Birmingham'
    _search_url = 'https://eplanning.birmingham.gov.uk/Northgate/PlanningExplorer/GeneralSearch.aspx'
    _html_subs = { 
        r'<script\s.*?</script>': r'',
        r'<form\s[^>]*?"site-search[^>]*?>.*?</form>': r''
    }
    detail_tests = [
        { 'uid': '2012/06298/PA', 'len': 11 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 142 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 18 } ]
        
class BlackburnScraper(PlanningExplorerScraper):

    data_start_target = '2000-04-01'
    _authority_name = 'Blackburn'
    _search_url = 'http://planning.blackburn.gov.uk/Northgate/PlanningExplorer/GeneralSearch.aspx'
    detail_tests = [
        { 'uid': '10/11/0878', 'len': 22 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 29 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 1 } ]
    
class BroadlandScraper(PlanningExplorerScraper):
    
    # Error on this site when using python 2.7.6/mechanize/urllib2 interface
    # <urlopen error [Errno 10054] An existing connection was forcibly closed by the remote host>
    # This is because 2.7.6 does not include the TLSv1.2 SSL protocol suite which is the only one the site accepts
    # see https://www.ssllabs.com/ssltest/analyze.html
    # Solution is to upgrade to python 2.7.10 or greater
    _authority_name = 'Broadland'
    _search_url = 'https://secure.broadland.gov.uk/Northgate/PlanningExplorer/GeneralSearch.aspx'
    _search_form = '0'
    _scrape_data_block = 'Details Page {{ block|html }} </body>'
    _scrape_dates_link = None
    _scrape_min_data = """
    <li> <span> Application Valid </span> {{ date_validated }} </li>
    <li> <span> Application Number </span> {{ reference }} </li>
    <li> <span> Site Address </span> {{ address }} </li>
    <li> <span> Proposal </span> {{ description }} </li>
    """
    # min field list used in testing only
    _min_fields = [ 'reference', 'address', 'description' ]
    detail_tests = [
        { 'uid': '20111169', 'len': 13 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 25 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 } ]
    
class CamdenScraper(PlanningExplorerScraper):

    _authority_name = 'Camden'
    _search_url = 'http://planningrecords.camden.gov.uk/Northgate/PlanningExplorer17/GeneralSearch.aspx'
    detail_tests = [
        { 'uid': '2011/4317/P', 'len': 20 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 133 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 12 } ]
        
class CharnwoodScraper(PlanningExplorerScraper): 

    _authority_name = 'Charnwood'
    _search_url = 'https://portal.charnwood.gov.uk/Northgate/PlanningExplorerAA/GeneralSearch.aspx'
    _search_form = '0'
    detail_tests = [
        { 'uid': 'P/11/1816/2', 'len': 22 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 48 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 10 } ]
        
    _html_subs = { 
        r'<script\s.*?</script>': r'',
        r'<form\s[^>]*?"search2"[^>]*?>.*?</form>': r''
    }
    _scrape_next_link = '<a href="{{ next_link }}"> <img title="Go to next page "> </a>' # note space
    _BADCHARS_REGEX = re.compile(r'%0D|%0A|%09|&#194;&#160;|&#xD;|&#xA;|&#x9;|\r\n\t+')
        
class ConwyScraper(PlanningExplorerScraper):

    _authority_name = 'Conwy'
    _search_url = 'http://npe.conwy.gov.uk/Northgate/EnglishPlanningExplorer/generalsearch.aspx'
    _search_form = '#M3Form'
    _scrape_next_link = '<a href="{{ next_link }}" title="Go to next page"> </a>'
    detail_tests = [
        { 'uid': '0/38507', 'len': 16 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 17 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 8 } ]
    
class EastStaffordshireScraper(PlanningExplorerScraper):

    _authority_name = 'EastStaffordshire'
    _search_url = 'http://www.eaststaffsbc.gov.uk/Northgate/PlanningExplorer/GeneralSearch.aspx'
    detail_tests = [
        { 'uid': 'P/2012/00774', 'len': 22 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 13 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ]
        
class EppingForestScraper(PlanningExplorerScraper):

    _authority_name = 'EppingForest'
    _search_url = 'http://plan1.eppingforestdc.gov.uk/Northgate/PlanningExplorer/GeneralSearch.aspx'
    _scrape_dates_link = '<h1 /> <a href="{{ dates_link }}"> Application Dates </a>'
    _scrape_next_link = '<h1 /> <a href="{{ next_link }}"> <img title="Go to next page"> </a>'
    detail_tests = [
        { 'uid': 'EPF/1680/11', 'len': 21 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 40 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 6 } ]
        
"""class ForestHeathScraper(PlanningExplorerScraper): now Idox West Suffolk

    _authority_name = 'ForestHeath'
    _search_url = 'http://www.eplan.forest-heath.gov.uk/Northgate/PlanningExplorer/GeneralSearch.aspx'
    _disabled = True
    _comment = 'Now WestSuffolk Idox (jointly with St Edmundsbury)'
    detail_tests = [
        { 'uid': 'F/2011/0509/LBC', 'len': 21 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 11 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 4 } ]"""
        
class HackneyScraper(PlanningExplorerScraper):

    _authority_name = 'Hackney'
    _search_url = 'http://planning.hackney.gov.uk/Northgate/PlanningExplorer/GeneralSearch.aspx'
    detail_tests = [
        { 'uid': '2011/2184', 'len': 20 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 42 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 11 } ]
        
class IslingtonScraper(PlanningExplorerScraper):

    _authority_name = 'Islington'
    _search_url = 'http://planning.islington.gov.uk/Northgate/PlanningExplorer/GeneralSearch.aspx'
    _comment = 'Was SwiftLG'
    detail_tests = [
        { 'uid': 'P121406', 'len': 18 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 61 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 12 } ]
        
"""class LincolnScraper(PlanningExplorerScraper): # now Idox

    _authority_name = 'Lincoln'
    _search_url = 'http://online.lincoln.gov.uk/Northgate/PlanningExplorer/GeneralSearch.aspx'
    detail_tests = [
        { 'uid': '2011/1030/F', 'len': 21 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 25 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 6 } ]"""
        
class LiverpoolScraper(PlanningExplorerScraper): # solves problem with expired results by reloading pages multiple times

    _authority_name = 'Liverpool'
    _search_url = 'http://northgate.liverpool.gov.uk/PlanningExplorer17/GeneralSearch.aspx?'
    _scrape_expired = '<span id="lblPagePosition"> The Results have expired. {{ expired }} </span>'
    _search_form = '0'
    detail_tests = [
        { 'uid': '11F/1844', 'len': 20 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 65 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 12 } ]
        
    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s", response.read())

        fields = self._search_fields
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        #self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._search_submit)
        html = response.read()
        sub_html = self._BADCHARS_REGEX.sub(' ', html)
                    
        expired = scrapemark.scrape(self._scrape_expired, sub_html)
        while expired:
            response = self.br.reload()
            html = response.read()
            sub_html = self._BADCHARS_REGEX.sub(' ', html)
            expired = scrapemark.scrape(self._scrape_expired, sub_html)
            
        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        while response and page_count < max_pages:
            url = response.geturl()
            ##self.logger.debug("ID batch page html: %s", sub_html)
            result = scrapemark.scrape(self._scrape_ids, sub_html, url)
            if result and result.get('records'):
                page_count += 1
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            else:
                self.logger.debug("Empty result after %d pages", page_count)
                break
            try:
                result = scrapemark.scrape(self._scrape_next_link, sub_html, url)
                next_url = myutils.GAPS_REGEX.sub('', result['next_link'])
                self.logger.debug("ID next url: %s", next_url)
                response = self.br.open(next_url)
                html = response.read()
                sub_html = self._BADCHARS_REGEX.sub(' ', html)
                    
                expired = scrapemark.scrape(self._scrape_expired, sub_html)
                while expired:
                    response = self.br.reload()
                    html = response.read()
                    sub_html = self._BADCHARS_REGEX.sub(' ', html)
                    expired = scrapemark.scrape(self._scrape_expired, sub_html)
            except: # normal failure to find next page link at end of page sequence here
                self.logger.debug("No next link after %d pages", page_count)
                break
        
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
        
        return final_result
        
    def get_html_from_uid (self, uid):     
        response = self.br.open(self._search_url)
        #self.logger.debug("ID detail start html: %s", response.read())
        fields = self._applic_fields
        fields [ self._ref_field ] = uid
        scrapeutils.setup_form(self.br, self._search_form, fields)
        response = scrapeutils.submit_form(self.br, self._search_submit)
        html = response.read()
        sub_html = self._BADCHARS_REGEX.sub(' ', html)
        #self.logger.debug("detail page html: %s", sub_html)     
        expired = scrapemark.scrape(self._scrape_expired, sub_html)
        while expired:
            response = self.br.reload()
            html = response.read()
            sub_html = self._BADCHARS_REGEX.sub(' ', html)
            expired = scrapemark.scrape(self._scrape_expired, sub_html)
        url = response.geturl()
        result = scrapemark.scrape(self._scrape_ids, sub_html, url)
        if result and result.get('records'):
            self._clean_ids(result['records'])
            for r in result['records']:
                if r.get('uid', '') == uid and r.get('url'):
                    self.logger.debug("Scraped url: %s", r['url'])
                    return self.get_html_from_url(r['url'])
        return None, None

    def _get_details(self, html, this_url):
        """ Scrapes detailed information for one record given html and url 
        - this is an optional hook to allow data from multiple linked pages to be merged """
        sub_html = self._BADCHARS_REGEX.sub(' ', html)
        expired = scrapemark.scrape(self._scrape_expired, sub_html)
        while expired:
            response = self.br.reload()
            html, this_url = self._get_html(response)
            sub_html = self._BADCHARS_REGEX.sub(' ', html)
            expired = scrapemark.scrape(self._scrape_expired, sub_html)
        result = self._get_detail(sub_html, this_url)
        if result and 'scrape_error' not in result and self._scrape_dates_link:
            try:
                date_result = scrapemark.scrape(self._scrape_dates_link, sub_html, this_url)
                dates_url = myutils.GAPS_REGEX.sub('', date_result['dates_link'])
                self.logger.debug("Dates url: %s", dates_url)
                response = self.br.open(dates_url)
                html, url = self._get_html(response)
                sub_html = self._BADCHARS_REGEX.sub(' ', html)
                expired = scrapemark.scrape(self._scrape_expired, sub_html)
                while expired:
                    response = self.br.reload()
                    html, url = self._get_html(response)
                    sub_html = self._BADCHARS_REGEX.sub(' ', html)
                    expired = scrapemark.scrape(self._scrape_expired, sub_html)
            except:
                self.logger.warning("No link to dates page found")
            else:
                #self.logger.debug("Html obtained from dates url: %s", html)
                result2 = self._get_detail(sub_html, url, self._scrape_dates_block, self._scrape_min_dates, self._scrape_optional_dates)
                if result2 and 'scrape_error' not in result2:
                    result.update(result2)
                else:
                    self.logger.warning("No information found on dates page")
        return result
        
"""class MendipScraper(PlanningExplorerScraper): # now Idox

    _authority_name = 'Mendip'
    _search_url = 'http://planning.mendip.gov.uk/northgate/planningexplorer/generalsearch.aspx'
    _scrape_data_block = '<body> Search Details {{ block|html }} </body>'
    detail_tests = [
        { 'uid': '2011/2111', 'len': 18 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 38 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ]"""
        
class MertonScraper(PlanningExplorerScraper):

    _authority_name = 'Merton'
    _search_url = 'http://planning.merton.gov.uk/Northgate/PlanningExplorerAA/GeneralSearch.aspx'
    detail_tests = [
        { 'uid': '11/P2351', 'len': 20 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 45 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 11 } ]
        
class NorthYorkMoorsScraper(PlanningExplorerScraper): # National Park

    _authority_name = 'NorthYorkMoors'
    _search_url = 'http://planning.northyorkmoors.org.uk/Northgate/PlanningExplorer/GeneralSearch.aspx'
    _scrape_data_block = '<body> Details for {{ block|html }} </body>'
    _scrape_dates_block = '<body> Dates for {{ block|html }} </body>'
    detail_tests = [
        { 'uid': 'NYM/2012/0543/FL', 'len': 19 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 13 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 4 } ]
        
class RunnymedeScraper(PlanningExplorerScraper):

    _authority_name = 'Runnymede'
    _search_url = 'http://planning.runnymede.gov.uk/Northgate/PlanningExplorer/GeneralSearch.aspx'
    _scrape_data_block = '<body> Application Details {{ block|html }} </body>'
    _scrape_dates_link = None
    _scrape_min_data = """
    <li> <span> Application Number </span> {{ reference }} </li>
    <li> <span> Site Address </span> {{ address }} </li>
    <li> <span> Proposal </span> {{ description }} </li>
    <li> <span> Valid Date </span> {{ date_validated }} </li>
    """
    # min field list used in testing only
    _min_fields = [ 'reference', 'address', 'description' ]
    detail_tests = [
        { 'uid': 'RU.11/1249', 'len': 14 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 19 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 6 } ]
        
class SouthLanarkshireScraper(PlanningExplorerScraper):
    
    url_first = False # by default tries to access applications from uid before url
    _authority_name = 'SouthLanarkshire'
    _search_url = 'http://pbsportal.southlanarkshire.gov.uk/Northgate/PlanningExplorer/GeneralSearch.aspx'
    detail_tests = [
        { 'uid': 'CL/11/0401', 'len': 21 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 36 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 7 } ]
        
    def get_html_from_uid (self, uid): # note gives 500 error if do not handle Referer explicitly as below (also see Tamworth)
        response = self.br.open(self._search_url)
        self._adjust_response(response)
        #self.logger.debug("ID detail start html: %s", response.read())
        fields = self._applic_fields
        fields [ self._ref_field ] = uid
        scrapeutils.setup_form(self.br, self._search_form, fields)
        response = scrapeutils.submit_form(self.br, self._search_submit)
        html, url = self._get_html(response)
        sub_html = self._BADCHARS_REGEX.sub(' ', html)
        #self.logger.debug("Detail page html: %s", sub_html)
        result = scrapemark.scrape(self._scrape_ids, sub_html, url)
        #print result
        if result and result.get('records'):
            self._clean_ids(result['records'])
            for r in result['records']:
                if r.get('uid', '') == uid and r.get('url'):
                    self.logger.debug("Scraped url: %s", r['url'])
                    headers = {}
                    headers.update(self._headers)
                    headers['Referer'] = url
                    self.br.addheaders = headers.items() 
                    return self.get_html_from_url(r['url'])
        return None, None
        
#class SouthNorfolkScraper(PlanningExplorerScraper): # now Idox
#
#    _authority_name = 'SouthNorfolk' # uid = 2011/1357
#    _search_url = 'http://planning.south-norfolk.gov.uk/Northgate/PlanningExplorer/GeneralSearch.aspx'

class SouthTynesideScraper(PlanningExplorerScraper):

    _authority_name = 'SouthTyneside'
    _search_url = 'http://planning.southtyneside.info/Northgate/PlanningExplorer/GeneralSearch.aspx'
    _search_form = '0'
    _html_subs = { 
        r'<script\s.*?</script>': r'',
        r'<form\s[^>]*?"subForm"[^>]*?>.*?</form>': r''
    }
    _scrape_ids = """
    <table class="display_table"> <tr />
    {* <tr>
    <td> <a href="{{ [records].url|abs }}"> <span /> {{ [records].uid }} </a> </td>
    </tr> *}
    </table>
    """
    detail_tests = [
        { 'uid': 'ST/1355/11/FUL', 'len': 17 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 11 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ]
        
#class SwanseaScraper(PlanningExplorerScraper): # now WAM
#
#    _authority_name = 'Swansea' # uid = 2011/1134
#    _search_url = 'http://www2.swansea.gov.uk/Northgate/PlanningExplorer/GeneralSearch.aspx'
        
class TamworthScraper(PlanningExplorerScraper):

    url_first = False # by default tries to access applications from uid before url
    _authority_name = 'Tamworth'
    _search_url = 'http://planning.tamworth.gov.uk/Northgate/PlanningExplorer/GeneralSearch.aspx'
    detail_tests = [
        { 'uid': '0424/2011', 'len': 21 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 3 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 1 } ]
        
    def get_html_from_uid (self, uid): # note gives 500 error if do not handle Referer explicitly as below (also see S. Lanark)
        response = self.br.open(self._search_url)
        self._adjust_response(response)
        #self.logger.debug("ID detail start html: %s", response.read())
        fields = self._applic_fields
        fields [ self._ref_field ] = uid
        scrapeutils.setup_form(self.br, self._search_form, fields)
        response = scrapeutils.submit_form(self.br, self._search_submit)
        html, url = self._get_html(response)
        sub_html = self._BADCHARS_REGEX.sub(' ', html)
        #self.logger.debug("Detail page html: %s", sub_html)
        result = scrapemark.scrape(self._scrape_ids, sub_html, url)
        #print result
        if result and result.get('records'):
            self._clean_ids(result['records'])
            for r in result['records']:
                if r.get('uid', '') == uid and r.get('url'):
                    self.logger.debug("Scraped url: %s", r['url'])
                    headers = {}
                    headers.update(self._headers)
                    headers['Referer'] = url
                    self.br.addheaders = headers.items() 
                    return self.get_html_from_url(r['url'])
        return None, None
        
"""class TraffordScraper(PlanningExplorerScraper): now Idox

    _authority_name = 'Trafford'
    _search_url = 'http://planning.trafford.gov.uk/Northgate/PlanningExplorerAA/GeneralSearch.aspx'
    detail_tests = [
        { 'uid': '77342/HHA/2011', 'len': 17 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 23 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]"""
        
"""class WalthamForestScraper(PlanningExplorerScraper): now Civica?

    _authority_name = 'WalthamForest'
    data_start_target = '2003-10-01' # gathers id data by working backwards from the current date towards this one
    batch_size = 28 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 28 # min number of days to get when gathering current ids
    _search_url = 'http://planning.walthamforest.gov.uk/PlanningExplorer/GeneralSearch.aspx'
    detail_tests = [
        { 'uid': '2011/1234', 'len': 19 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 27 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 8 } ]"""
        
class WandsworthScraper(PlanningExplorerScraper):

    _authority_name = 'Wandsworth'
    _search_url = 'https://planning1.wandsworth.gov.uk/Northgate/PlanningExplorer/GeneralSearch.aspx'
    _scrape_data_block = '<body> Page for Planning Application {{ block|html }} </body>'
    detail_tests = [
        { 'uid': '2011/2375', 'len': 19 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 112 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 16 } ]
        
class WiltshireScraper(PlanningExplorerScraper): # now covers Salisbury and Devizes (and Chippenham and Trowbridge after June/July 2013)
    # AcolNet = North = Chippenham before 2013
    # Idox = West = Trowbridge before 2013
    _authority_name = 'Wiltshire'
    _search_url = 'http://planning.wiltshire.gov.uk/Northgate/PlanningExplorer/GeneralSearch.aspx'
    _scrape_ids = """
    <table summary="Results of the Search"> <tr />
    {* <tr>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    </tr> *}
    </table>"""
    _scrape_next_link = '<a href="{{ next_link }}" title="Go to the next page" />'
    _scrape_data_block = '<div id="article"> {{ block|html }} </div>'
    _scrape_min_data = """
    <h2> Planning application {{ reference }} </h2>
    <dt> Registered </dt> <dd> {{ date_validated }} </dd>
    <dt> Site Address </dt> <dd> {{ address }} </dd>
    <dt> Proposed Development </dt> <dd> {{ description }} </dd>
    """
    _scrape_dates_link = None
    _min_fields = [ 'reference', 'address', 'description' ] # min field list used in testing only
    _scrape_optional_data = [
    "<dt> Application Type </dt> <dd> {{ application_type }} </dd>",
    "<dt> Decision </dt> <dd> {{ decision_date }} ( {{ decision }} ) </dd>",
    "<dt> Current Status </dt> <dd> {{ status }} </dd>",
    "<dt> Applicant </dt> <dd> {{ applicant_name }} </dd>",
    "<dt> Applicant </dt> <dt> Applicant Address </dt> <dd> {{ applicant_address }} </dd>",
    "<dt> Agent </dt> <dd> {{ agent_name }} </li>",
    "<dt> Agent </dt> <dt> Agent Address </dt> <dd> {{ agent_address }} </dd>",
    "<dt> Wards </dt> <dd> {{ ward_name }} </dd>",
    "<dt> Parishes </dt> <dd> {{ parish }} </dd>",
    "<dt> Development Type </dt> <dd> {{ development_type }} </dd>",
    "<dt> Case Officer </dt> <dd> {{ case_officer }} </dd>",
    "<dt> Target Date For Decision </dt> <dd> {{ target_decision_date }} </dd>",
    "<dt> Consultation Expiry </dt> <dd> {{ consultation_end_date }} </dd>",
    "<dt> Committee Date </dt> <dd> {{ meeting_date }} </dd>",
    '<li class="commentlink"> <a href="{{ comment_url|abs }}" /> </li>'
    ]
    detail_tests = [
        { 'uid': '13/00688/FUL', 'len': 14 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 130 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 20 } ]

