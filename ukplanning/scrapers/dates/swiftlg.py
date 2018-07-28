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
import re

class SwiftLGScraper(base.DateScraper):

    min_id_goal = 200 # min target for application ids to fetch in one go
    
    _scraper_type = 'SwiftLG'
    _handler = 'etree' # note HTML is pretty disastrous
    _date_from_field = 'REGFROMDATE.MAINBODY.WPACIS.1'
    _date_to_field = 'REGTODATE.MAINBODY.WPACIS.1'
    _search_form = '0'
    _scrape_ids = """
    <form> <table> <tr />
    {* <tr>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    </tr> *}
    </table> </form>
    """
    _scrape_next_link = """ 
        <form> Pages <a href="{{ next_link }}"> </form>
        """ # note single quotes and the link parameters are adjusted below
    _detail_page = 'WPHAPPDETAIL.DisplayUrl'
    _scrape_max_recs = [
        'returned {{ max_recs }} matches',
        'found {{ max_recs }} matching',
        '<p> Search results: {{ max_recs }} <br>',
        'returned {{ max_recs }} matche(s).',
        'Matches returned {{ max_recs }} .'
    ]
    
    _BACKURL_REGEX1 = re.compile(r'<a href="([^"]*?)&(?:amp;)*[bB]ackURL=[^"]*?">', re.U|re.S|re.I) # unicode|dot matches new line|ignore case
    _BACKURL_REGEX2 = re.compile(r"<a href='([^']*?)&(?:amp;)*[bB]ackURL=[^']*?'>", re.U|re.S|re.I) # unicode|dot matches new line|ignore case
    _SUBURL = r'<a href="\1">'
    _html_subs = { }  
    _map_suffixes = [ 'View Map', '( see map, if available )', 'View location map' ]
    
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = '<form action="WPHAPPDETAIL"> {{ block|html }} </form>'

    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s", response.read())

        fields = {}
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        
        html = response.read()
        url = response.geturl()
    
        sub_html = self._BACKURL_REGEX1.sub(self._SUBURL, html)
        sub_html = self._BACKURL_REGEX2.sub(self._SUBURL, sub_html)
        
        max_recs = 0
        for scrape in self._scrape_max_recs:
            try:
                result = scrapemark.scrape(scrape, sub_html)
                max_recs = int(result['max_recs'])
                self.logger.debug("max_recs: %d", max_recs)
                break
            except:
                pass
        
        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        while response and len(final_result) < max_recs and page_count < max_pages:
            result = scrapemark.scrape(self._scrape_ids, sub_html, url)
            if result and result.get('records'):
                page_count += 1
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            else:
                self.logger.debug("Empty result after %d pages", page_count)
                break
            if len(final_result) >= max_recs:
                break
            try:
                result = scrapemark.scrape(self._scrape_next_link, sub_html, url)
                next_batch = len(final_result) + 1
                replacement = '&StartIndex=' + str(next_batch) + '&SortOrder'
                next_url = re.sub(r'&StartIndex=\d+&SortOrder', replacement, result['next_link'])
                response = self.br.open(next_url)
                html = response.read()
                url = response.geturl()
                sub_html = self._BACKURL_REGEX1.sub(self._SUBURL, html)
                sub_html = self._BACKURL_REGEX2.sub(self._SUBURL, sub_html)
            except:
                self.logger.debug("No next link after %d pages", page_count)
                break
                
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
               
        return final_result

    def get_html_from_uid(self, uid):
        url = urlparse.urljoin(self._search_url, self._detail_page) + '?theApnID=' + urllib.quote_plus(uid)
        return self.get_html_from_url(url)
        
    def _clean_record(self, record): 
        super(SwiftLGScraper, self)._clean_record(record)
        address = record.get('address', '')
        if address:
            for m in self._map_suffixes:
                if address.endswith(m):
                    alen = len(m)
                    record['address'] = address[:-alen] # strip out any suffix
                    break
        
    def _adjust_html(self, html): 
        """ Hook to adjust application html if necessary before scraping """
        if self._html_subs:
            for k, v in self._html_subs.items():
                html = re.sub(k, v, html, 0, re.U|re.S|re.I) # unicode|dot matches new line|ignore case
        return html
    
class SwiftLGSpanScraper(SwiftLGScraper):
    
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <span> Application Ref: </span> <p> {{ reference }} </p>
    <span> Registration Date: </span> <p> {{ date_validated }} </p>
    <span> Main Location: </span> <p> {{ address|html }} </p>
    <span> Full Description: </span> <p> {{ description }} </p>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [ 
    '<span> Web Reference: </span> <p> {{ planning_portal_id }} </p>',
    '<span> Application Date: </span> <p> {{ date_received }} </p>',
    '<span> Application Type: </span> <p> {{ application_type }} </p>',
    '<span> Community </span> <p> {{ parish }} </p>',
    '<span> Parish: </span> <p> {{ parish }} </p>',
    '<span> Electoral Division: </span> <p> {{ ward_name }} </p>',
    '<span> Ward </span> <p> {{ ward_name }} </p>',
    '<span> Decision Date: </span> <p> {{ decision_date }} </p>',
    '<span> Committee Date </span> <p> {{ meeting_date }} </p>',
    '<span> Target Date for Decision </span> <p> {{ target_decision_date }} </p>',
    '<span> Despatch Date: </span> <p> {{ decision_issued_date }} </p>',
    '<span> Decision Despatched: </span> <p> {{ decision_issued_date }} </p>',
    '<span> Case Officer: </span> <p> {{ case_officer }} </p>',
    '<span> Decision: </span> <p> {{ decision }} </p>',
    '<span> Area: </span> <p> {{ district }} </p>',
    '<span> District: </span> <p> {{ district }} </p>',
    '<span> Publicity Start Date: </span> <p> {{ consultation_start_date }} </p>',
    '<span> Publicity End Date: </span> <p> {{ consultation_end_date }} </p>',
    '<h2> Applicant Details </h2> {* <span /> <p> {{ [applicant_name] }} </p> *} <span> Address: </span>',
    '<h2> Agent Details </h2> {* <span /> <p> {{ [agent_name] }} </p> *} <span> Address: </span>',
    '<h2> Applicant Details </h2> <span> Address: </span> <p> {{ applicant_address }} </p>',
    '<h2> Agent Details </h2> <span> Address: </span> <p> {{ agent_address }} </p>',
    '{* <span> Status </span> <p> {{ [status] }} </p> *}',
    '<span> Comment: </span> <p> <a href="{{ comment_url|abs }}" /> </p>',
    ]
        
class SwiftLGLabelScraper(SwiftLGScraper):

    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <div class="fieldset_data"> <label> Application Ref: </label> {{ reference }} </div>
    <div class="fieldset_data"> <label> Registration Date: </label> {{ date_validated }} </div>
    <div class="fieldset_data"> <label> Main Location: </label> {{ address|html }} </div>
    <div class="fieldset_data"> <label> Full Description: </label> {{ description }} </div>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [ 
    '<div class="fieldset_data"> <label> Web Reference: </label> {{ planning_portal_id }} </div>',
    '<div class="fieldset_data"> <label> Application Date: </label> {{ date_received }} </div>',
    '<div class="fieldset_data"> <label> Application Type: </label> {{ application_type }} </div>',
    '<div class="fieldset_data"> <label> Parish: </label> {{ parish }} </div>',
    '<div class="fieldset_data"> <label> Community </label> {{ parish }} </div>',
    '<div class="fieldset_data"> <label> Electoral Division: </label> {{ ward_name }} </div>',
    '<div class="fieldset_data"> <label> Ward </label> {{ ward_name }} </div>',
    '<div class="fieldset_data"> <label> Decision Date: </label> {{ decision_date }} </div>',
    '<div class="fieldset_data"> <label> Despatch Date: </label> {{ decision_issued_date }} </div>',
    '<div class="fieldset_data"> <label> Case Officer: </label> {{ case_officer }} </div>',
    '<div class="fieldset_data"> <label> Decision: </label> {{ decision }} </div>',
    '<div class="fieldset_data"> <label> Area: </label> {{ district }} </div>',
    '<div class="fieldset_data"> <label> District: </label> {{ district }} </div>',
    '<div class="fieldset_data"> <label> Publicity Start Date </label> {{ consultation_start_date }} </div>',
    '<div class="fieldset_data"> <label> Publicity End Date </label> {{ consultation_end_date }} </div>',
    '<h2> Applicant Details </h2> {* <div class="fieldset_data"> <label /> {{ [applicant_name] }} </div> *} <div class="fieldset_data"> <label> Address: </label> </div>',
    '<h2> Agent Details </h2> {* <div class="fieldset_data"> <label /> {{ [agent_name] }} </div> *} <div class="fieldset_data"> <label> Address: </label> </div>',
    '<h2> Applicant Details </h2> <div class="fieldset_data"> <label> Address: </label> {{ applicant_address }} </div>',
    '<h2> Agent Details </h2> <div class="fieldset_data"> <label> Address: </label> {{ agent_address }} </div>',
    '{* <div class="fieldset_data"> <label> Status </label> {{ [status] }} </div> *}',
    '<div class="fieldset_data"> <label> Comment: </label> <a href="{{ comment_url|abs }}" /> </div>',
    ]
    
class SwiftLGSpan2Scraper(SwiftLGScraper):

    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <div class="fieldset_divdata"> <span> Reference Number: </span> {{ reference }} </div>
    <div class="fieldset_divdata"> <span> Site Address: </span> {{ address|html }} </div>
    <div class="fieldset_divdata"> <span> Description: </span> {{ description }} </div>
    <div class="fieldset_divdata"> <span> Registration Date: </span> {{ date_validated }} </div>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [ 
    '<div class="fieldset_divdata"> <span> Web Reference: </span> {{ planning_portal_id }} </div>',
    '<div class="fieldset_divdata"> <span> Application Date: </span> {{ date_received }} </div>',
    '<div class="fieldset_divdata"> <span> Application Type: </span> {{ application_type }} </div>',
    '<div class="fieldset_divdata"> <span> Parish: </span> {{ parish }} </div>',
    '<div class="fieldset_divdata"> <span> Community </span> {{ parish }} </div>',
    '<div class="fieldset_divdata"> <span> Electoral Division: </span> {{ ward_name }} </div>',
    '<div class="fieldset_divdata"> <span> Ward </span> {{ ward_name }} </div>',
    '<div class="fieldset_divdata"> <span> Decision Date: </span> {{ decision_date }} </div>',
    '<div class="fieldset_divdata"> <span> Despatch Date: </span> {{ decision_issued_date }} </div>',
    '<div class="fieldset_divdata"> <span> Case Officer: </span> {{ case_officer }} </div>',
    '<div class="fieldset_divdata"> <span> Decision: </span> {{ decision }} </div>',
    '<div class="fieldset_divdata"> <span> Area: </span> {{ district }} </div>',
    '<div class="fieldset_divdata"> <span> District: </span> {{ district }} </div>',
    '<div class="fieldset_divdata"> <span> Publicity Start Date </span> {{ consultation_start_date }} </div>',
    '<div class="fieldset_divdata"> <span> Publicity End Date </span> {{ consultation_end_date }} </div>',
    '<div class="fieldset_divdata"> <span> Applicant Details </span> {{ applicant_address }} </div>',
    '<div class="fieldset_divdata"> <span> Agent Details </span> {{ agent_address }} </div>',
    '<h2> Applicant Details </h2> {* <div class="fieldset_divdata"> <label /> {{ [applicant_name] }} </div> *} <div class="fieldset_divdata"> <span> Address: </span> </div>',
    '<h2> Agent Details </h2> {* <div class="fieldset_divdata"> <label /> {{ [agent_name] }} </div> *} <div class="fieldset_divdata"> <span> Address: </span> </div>',
    '<h2> Applicant Details </h2> <div class="fieldset_divdata"> <span> Address: </span> {{ applicant_address }} </div>',
    '<h2> Agent Details </h2> <div class="fieldset_divdata"> <span> Address: </span> {{ agent_address }} </div>',
    '{* <div class="fieldset_divdata"> <span> Status </span> {{ [status] }} </div> *}',
    '<div class="fieldset_divdata"> <span> Comment: </span> <a href="{{ comment_url|abs }}" /> </div>',
    ]
    
class SwiftLGLabel2Scraper(SwiftLGScraper):

    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <label> Application Ref: </label> <p> {{ reference }} </p>
    <label> Registration Date: </label> <p> {{ date_validated }} </p>
    <label> Main Location: </label> <p> {{ address|html }} </p>
    <label> Full Description: </label> <p> {{ description }} </p>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [ 
    '<label> Web Reference: </label> <p> {{ planning_portal_id }} </p>',
    '<label> Application Date: </label> <p> {{ date_received }} </p>',
    '<label> Application Type: </label> <p> {{ application_type }} </p>',
    '<label> Parish: </label> <p> {{ parish }} </p>',
    '<label> Community </label> <p> {{ parish }} </p>',
    '<label> Electoral Division: </label> <p> {{ ward_name }} </p>',
    '<label> Ward </label> <p> {{ ward_name }} </p>',
    '<label> Decision Date: </label> <p> {{ decision_date }} </p>',
    '<label> Despatch Date: </label> <p> {{ decision_issued_date }} </p>',
    '<label> Case Officer: </label> <p> {{ case_officer }} </p>',
    '<label> Decision: </label> <p> {{ decision }} </p>',
    '<label> Area: </label> <p> {{ district }} </p>',
    '<label> District: </label> <p> {{ district }} </p>',
    '<label> Publicity Start Date </label> <p> {{ consultation_start_date }} </p>',
    '<label> Publicity End Date </label> <p> {{ consultation_end_date }} </p>',
    '<h2> Applicant Details </h2> {* <label /> <p> {{ [applicant_name] }} </p> *} <label> Address: </label> <p/>',
    '<h2> Agent Details </h2> {* <label /> <p> {{ [agent_name] }} </p> *} <label> Address: </label> <p/>',
    '<h2> Applicant Details </h2> <label> Address: </label> <p> {{ applicant_address }} </p>',
    '<h2> Agent Details </h2> <label> Address: </label> <p> {{ agent_address }} </p>',
    '{* <label> Status </label> <p> {{ [status] }} </p> *}',
    '<label> Comment: </label> <p> <a href="{{ comment_url|abs }}" /> </p>',
    ]
    
class SwiftLGLabel3Scraper(SwiftLGScraper):

    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <td> <label> Application Reference: </label> </td> <td> {{ reference }} </td>
    <td> <label> Proposal: </label> </td> <td> {{ description }} </td>
    <td> <label> Registration Date: </label> </td> <td> {{ date_validated }} </td>
    <td> <label> Location: </label> </td> <td> {{ address|html }} </td>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [ 
    '<td> <label> Web Reference: </label> </td> <td> {{ planning_portal_id }} </td>',
    '<td> <label> Application Date: </label> </td> <td> {{ date_received }} </td>',
    '<td> <label> Application Type: </label> </td> <td> {{ application_type }} </td>',
    '<td> <label> Parish: </label> </td> <td> {{ parish }} </td>',
    '<td> <label> Community </label> </td> <td> {{ parish }} </td>',
    '<td> <label> Electoral Division: </label> </td> <td> {{ ward_name }} </td>',
    '<td> <label> Ward </label> </td> <td> {{ ward_name }} </td>',
    '<td> <label> Decision Date: </label> </td> <td> {{ decision_date }} </td>',
    '<td> <label> Despatch Date: </label> </td> <td> {{ decision_issued_date }} </td>',
    '<td> <label> Case Officer: </label> </td> <td> {{ case_officer }} </td>',
    '<td> <label> Decision: </label> </td> <td> {{ decision }} </td>',
    '<td> <label> Area: </label> </td> <td> {{ district }} </td>',
    '<td> <label> District: </label> </td> <td> {{ district }} </td>',
    '<td> <label> Publicity Start Date </label> </td> <td> {{ consultation_start_date }} </td>',
    '<td> <label> Publicity End Date </label> </td> <td> {{ consultation_end_date }} </td>',
    '<h2> Applicant Details </h2> {* <td> <label /> {{ [applicant_name] }} </td> *} <td> <label> Address: </label> </td> <td> </td>',
    '<h2> Agent Details </h2> {* <td> <label /> {{ [agent_name] }} </td> *} <td> <label> Address: </label> </td> <td> </td>',
    '<h2> Applicant Details </h2> <td> <label> Address: </label> </td> <td> {{ applicant_address }} </td>',
    '<h2> Agent Details </h2> <td> <label> Address: </label> </td> <td> {{ agent_address }} </td>',
    '{* <td> <label> Status </label> </td> <td> {{ [status] }} </td> *}',
    '<td> <label> Comment: </label> </td> <td> <a href="{{ comment_url|abs }}" /> </td>',
    ]
    
class SwiftLGBoldScraper(SwiftLGScraper):

    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <td> <b> Application Reference: </b> </td> <td> {{ reference }} </td>
    <td> <b> Registration Date: </b> </td> <td> {{ date_validated }} </td>
    <td> <b> Main Location: </b> </td> <td> {{ address|html }} </td>
    <td> <b> Proposal </b> </td> <td> {{ description }} <a /> </td>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [ 
    '<td> <b> Web Reference </b> </td> <td> {{ planning_portal_id }} </td>',
    '<td> <b> Application Date: </b> </td> <td> {{ date_received }} </td>',
    '<td> <b> Application Type: </b> </td> <td> {{ application_type }} </td>',
    '<td> <b> Parish: </b> </td> <td> {{ parish }} </td>',
    '<td> <b> Community </b> </td> <td> {{ parish }} </td>',
    '<td> <b> Electoral Division: </b> </td> <td> {{ ward_name }} </td>',
    '<td> <b> Ward </b> </td> <td> {{ ward_name }} </td>',
    '<td> <b> Decision Date: </b> </td> <td> {{ decision_date }} </td>',
    '<td> <b> Final Grant Date:  </b> </td> <td> {{ decision_issued_date }} </td>',
    '<td> <b> Decision: </b> </td> <td> {{ decision }} </td>',
    '<td> <b> Area: </b> </td> <td> {{ district }} </td>',
    '<td> <b> District: </b> </td> <td> {{ district }} </td>',
    '<td> <b> Publicity Start Date </b> </td> <td> {{ consultation_start_date }} </td>',
    '<td> <b> Last Date for Observations: </b> </td> <td> {{ consultation_end_date }} </td>',
    '<td> <b> Status </b> </td> <td> {{ status }} </td>',
    # not working below
    '<tr> <b> Applicant </b> </tr> {* <td> {{ [applicant_name] }} </td> *} <td> Address </td> <td> </td>',
    '<tr> <b> Agent </b> </tr> {* <td> {{ [agent_name] }} </td> *} <td> Address </td> <td> </td>',
    '<tr> <b> Applicant </b> </tr> <tr> <td> Address </td> <td> {{ applicant_address }} </td> </tr>',
    '<tr> <b> Agent </b> </tr> <tr> <td> Address </td> <td> {{ agent_address }} </td> </tr>',
    '<tr> <b> Applicant </b> </tr> <tr> <td> Case Officer </td> <td> {{ case_officer }} </td> </tr>',
    ]
    
class SwiftLGLabel4Scraper(SwiftLGScraper):

    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <label> Application Reference Number: </label> {{ reference }} <br/>
    <label> Site Location: </label> {{ address|html }} <br/>
    <label> Registration Date: </label> {{ date_validated }} <br/>
    <label> Proposal: </label> {{ description }} <br/>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [ 
    '<label> Portal Reference Number: </label> {{ planning_portal_id }} <br/>',
    '<label> Application Date: </label> {{ date_received }} <br/>',
    '<label> Application Type: </label> {{ application_type }} <br/>',
    '<label> Parish: </label> {{ parish }} <br/>',
    '<label> Community </label> {{ parish }} <br/>',
    '<label> Electoral Division: </label> {{ ward_name }} <br/>',
    '<label> Ward </label> {{ ward_name }} <br/>',
    '<label> Decision Date: </label> {{ decision_date }} <br/>',
    '<label> Despatch Date: </label> {{ decision_issued_date }} <br/>',
    '<label> Case Officer: </label> {{ case_officer }} <br/>',
    '<label> Decision: </label> {{ decision }} <br/>',
    '<label> Area: </label> {{ district }} <br/>',
    '<label> District: </label> {{ district }} <br/>',
    '<label> Publicity Start Date </label> {{ consultation_start_date }} <br/>',
    '<label> Publicity End Date </label> {{ consultation_end_date }} <br/>',
    '<h2> Applicant Details </h2> {* <label /> {{ [applicant_name] }} <br/> *} <label> Address: </label> <br/>',
    '<h2> Agent Details </h2> {* <label /> {{ [agent_name] }} <br/> *} <label> Address: </label> <br/>',
    '<h2> Applicant Details </h2> <label> Address: </label> {{ applicant_address }} <br/>',
    '<h2> Agent Details </h2> <label> Address: </label> {{ agent_address }} <br/>',
    '{* <label> Status </label> {{ [status] }} <br/>*}',
    '<label> Comment: </label> <a href="{{ comment_url|abs }}" /> <br/>',
    ]
    
class SwiftLGStrongScraper(SwiftLGScraper):

    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <p> <strong> Application Ref: </strong> {{ reference }} </p>
    <p> <strong> Registration Date: </strong> {{ date_validated }} </p>
    <p> <strong> Main Location: </strong> {{ address|html }} </p>
    <p> <strong> Full Description: </strong> {{ description }} </p>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [ 
    '<p> <strong> Web Reference: </strong> {{ planning_portal_id }} </p>',
    '<p> <strong> Application Date: </strong> {{ date_received }} </p>',
    '<p> <strong> Application Type: </strong> {{ application_type }} </p>',
    '<p> <strong> Parish: </strong> {{ parish }} </p>',
    '<p> <strong> Community </strong> {{ parish }} </p>',
    '<p> <strong> Electoral Division: </strong> {{ ward_name }} </p>',
    '<p> <strong> Ward </strong> {{ ward_name }} </p>',
    '<p> <strong> Decision Date: </strong> {{ decision_date }} </p>',
    '<p> <strong> Despatch Date: </strong> {{ decision_issued_date }} </p>',
    '<p> <strong> Case Officer: </strong> {{ case_officer }} </p>',
    '<p> <strong> Decision: </strong> {{ decision }} </p>',
    '<p> <strong> Area: </strong> {{ district }} </p>',
    '<p> <strong> District: </strong> {{ district }} </p>',
    '<p> <strong> Publicity Start Date </strong> {{ consultation_start_date }} </p>',
    '<p> <strong> Publicity End Date </strong> {{ consultation_end_date }} </p>',
    '<h2> Applicant Details </h2> {* <p> <strong /> { [applicant_name] }} </p> *} <p> <strong> Address: </strong> </p>',
    '<h2> Agent Details </h2> {* <p> <strong /> {{ [agent_name] }} </p> *} <p> <strong> Address: </strong> </p>',
    '<h2> Applicant Details </h2> <p> <strong> Address: </strong> {{ applicant_address }} </p>',
    '<h2> Agent Details </h2> <p> <strong> Address: </strong> {{ agent_address }} </p>',
    '{* <p> <strong> Status </strong> {{ [status] }} </p> *}',
    '<p> <strong> Comment: </strong> <a href="{{ comment_url|abs }}" /> </p>',
    ]
    
class CambridgeshireScraper(SwiftLGLabel2Scraper): 

    batch_size = 42 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 42 # start this number of days ago when gathering current ids
    
    _search_url = 'http://planning.cambridgeshire.gov.uk/swift/apas/run/wphappcriteria.display'
    _authority_name = 'Cambridgeshire'
    _comment = 'was AcolNet'
    _date_from_field = 'REGFROMDATE.MAINBODY.WPACIS'
    _date_to_field = 'REGTODATE.MAINBODY.WPACIS'
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <label> Application Reference: </label> <p> {{ reference }} </p>
    <label> Start Date: </label> <p> {{ date_validated }} </p>
    <label> Location: </label> <p> {{ address|html }} </p>
    <label> Description: </label> <p> {{ description }} </p>
    """
    _scrape_optional_data = list(SwiftLGLabel2Scraper._scrape_optional_data) # copies the original
    _scrape_optional_data.extend([ 
    '<label> Parish </label> <p/> <p> {{ parish }} </p>',
    '<label> Electoral Division: </label> <p/> <p> {{ ward_name }} </p>',
    ])
    
    detail_tests = [
        { 'uid': 'H/05018/12/CC', 'len': 14 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 3 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 1 } ]

class CannockChaseScraper(SwiftLGLabel2Scraper): 

    _search_url = 'http://planning.cannockchasedc.com/swiftlg/apas/run/wphappcriteria.display'
    _authority_name = 'CannockChase'
    
    detail_tests = [
        { 'uid': 'CH/11/0274', 'len': 17 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 15 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]
        
class DaventryScraper(SwiftLGLabel4Scraper):

    batch_size = 28 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 28 # start this number of days ago when gathering current ids
    _search_url = 'http://selfservice.daventrydc.gov.uk/swiftlg/apas/run/wphappcriteria.display'
    _authority_name = 'Daventry'
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <label> Reference Number: </label> {{ reference }} <br>
    <label> Registration Date: </label> {{ date_validated }} <br>
    <label> Main Location: </label> {{ address|html }} <p/>
    <label> Proposal: </label> {{ description }} <br>
    """
    _scrape_optional_data = list(SwiftLGLabel4Scraper._scrape_optional_data) # copies the original
    _scrape_optional_data.extend([ 
    '<label> Decision Date: </label> {{ decision_date }} <br> <label> Appeal </label>',
    '<label> Decision: </label> {{ decision }} <br> <label> Appeal </label>',
    '<label> Appeal Lodged Date: </label> {{ appeal_date }} <br>',
    '<label> Appeal Decision: </label> {{ appeal_result }} <br>',
    '<label> Appeal Decision Date: </label> {{ appeal_decision_date }} <br>',
    ])
    
    detail_tests = [
        { 'uid': 'DA/2010/0002', 'len': 15 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 20 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ]

class DublinNewScraper(SwiftLGBoldScraper): # no location provided and not all fields returned

    _search_url = 'http://www.dublincity.ie/swiftlg/apas/run/wphappcriteria.display'
    _authority_name = 'DublinNew'
    _comment = 'Ireland'
       
    detail_tests = [
        { 'uid': 'WEB1166/12', 'len': 11 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 69 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 9 } ]
        
class DudleyScraper(SwiftLGSpanScraper): 

    _search_url = 'https://www5.dudley.gov.uk/swiftlg/apas/run/Wphappcriteria.display'
    _authority_name = 'Dudley'
    _search_form = '1'
    
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <span> Application Ref: </span> <p> {{ reference }} </p>
    <span> Registration Date: </span> <p> {{ date_validated }} </p>
    <span> Main Location: </span> <p> {{ address|html }} </p>
    <span> Proposal: </span> <p> {{ description }} </p>
    """
    
    detail_tests = [
        { 'uid': 'P13/0122', 'len': 20 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 28 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ]
    
"""class EssexOldScraper(SwiftLGLabel2Scraper): 

    batch_size = 28 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 28 # start this number of days ago when gathering current ids
    _search_url = 'https://planning.essex.gov.uk/swiftlg/apas/run/wphappcriteria.display'
    _authority_name = 'EssexOld'
    _SUBURL = r'<a href="\1&theTabNo=3">'
    
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = ""
    <label> Application Ref: </label> <p> {{ reference }} </p>
    <label> Date of Validation: </label> <p> {{ date_validated }} </p>
    <label> Main Location: </label> <p> {{ address|html }} </p>
    <label> Full Description: </label> <p> {{ description }} </p>
    ""
    _scrape_optional_data = list(SwiftLGLabel2Scraper._scrape_optional_data) # copies the original
    _scrape_optional_data.extend([ 
    '<label> District(s): </label> <p> {{ district }} </p>',
    '<label> Electoral Division(s): </label> <p> {{ ward_name }} </p>',
    '<label> Parish(es): </label> <p> {{ parish }} </p>',
    ])
    
    detail_tests = [
        { 'uid': 'ESS/58/12/CHL', 'len': 16 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 26 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 1 } ]
        
    def get_html_from_uid(self, uid):
        url = urlparse.urljoin(self._search_url, self._detail_page) + '?theTabNo=3&theApnID=' + urllib.quote_plus(uid)
        return self.get_html_from_url(url)"""
        
class GwyneddScraper(SwiftLGLabel4Scraper): 

    _search_url = 'https://diogel.cyngor.gwynedd.gov.uk/swiftlg/apas/run/wphappcriteria.display?langid=1'
    _authority_name = 'Gwynedd'
    _search_form = '1'
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = '<div id="cynllunioCynhwysydd"> {{ block|html }} </div>'
    _scrape_optional_data = list(SwiftLGLabel4Scraper._scrape_optional_data) # copies the original
    _scrape_optional_data.extend([ 
    '<span> Applicant </span> {* <label /> {{ [applicant_name] }} <br/> *} <label> Address: </label>',
    '<span> Agent </span> {* <label /> {{ [agent_name] }} <br/> *} <label> Address: </label>',
    '<span> Applicant </span> <label> Address: </label> {{ applicant_address }} <br/>',
    '<span> Agent </span> <label> Address: </label> {{ agent_address }} <input/>',
    ])
    
    detail_tests = [
        { 'uid': 'C11/0643/11/CT', 'len': 14 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 21 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 4 } ]
        
class LakeDistrictScraper(SwiftLGLabel2Scraper):

    _search_url = 'http://www.lakedistrict.gov.uk/swiftlg/apas/run/wphappcriteria.display'
    _authority_name = 'LakeDistrict'
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <label> Planning Reference: </label> <p> {{ reference }} </p>
    <label> Proposal: </label> <p> {{ description }} </p>
    <label> Registration Date: </label> <p> {{ date_validated }} </p>
    <label> Location: </label> <p> {{ address|html }} </p>
    """
    _scrape_optional_data = list(SwiftLGLabel2Scraper._scrape_optional_data) # copies the original
    _scrape_optional_data.extend([ 
    '<label> Progress: </label> <p> {{ status }} </p>',
    '<label> Applicant Name: </label> <p> {{ applicant_name }} </p>',
    '<label> Agent Name: </label> <p> {{ agent_name }} </p>',
    '<label> Applicant Address: </label> <p> {{ applicant_address }} </p>',
    '<label> Agent Address: </label> <p> </label> {{ agent_address }} </p>',
    
    ])
    detail_tests = [
        { 'uid': '7/2011/5408', 'len': 14 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 22 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 4 } ]
        
class LondonLegacyScraper(SwiftLGSpanScraper): 

    data_start_target = '2006-09-06'
    _search_url = 'http://planningregister.londonlegacy.co.uk/swift/apas/run/wphappcriteria.display'
    _authority_name = 'LondonLegacy'
    
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <span> Application Ref: </span> <p> {{ reference }} </p>
    <span> Valid Date: </span> <p> {{ date_validated }} </p>
    <span> Main Location: </span> <p> {{ address|html }} </p>
    <span> Full Description: </span> <p> {{ description }} </p>
    """
    _scrape_optional_data = list(SwiftLGSpanScraper._scrape_optional_data) # copies the original
    _scrape_optional_data.extend([ 
    '<span> Borough: </span> <p> {{ district }} </p>',
    ])
    
    detail_tests = [
        { 'uid': '10/90356/AODODA', 'len': 16 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2011', 'to': '19/09/2011', 'len': 17 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 1 } ]
    
class MoleValleyScraper(SwiftLGLabelScraper):

    _search_url = 'http://www.molevalley.gov.uk/swiftlg/apas/run/wphappcriteria.display'
    _authority_name = 'MoleValley'
    _html_subs = { 
        r'<script.*?</script>': r'',
    }
    _scrape_optional_data = list(SwiftLGLabelScraper._scrape_optional_data) # copies the original
    _scrape_optional_data.extend([ 
    '<div class="fieldset_data"> <label> Publicity End Date </label> {{ consultation_end_date }} <b/> </div>',
    ])
    
    detail_tests = [
        { 'uid': 'MO/2012/0800', 'len': 18 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 30 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 5 } ]

class NewportScraper(SwiftLGLabel2Scraper):

    _search_url = 'http://planning.newport.gov.uk/swift/apas/run/wphappcriteria.display'
    _authority_name = 'Newport'
    
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <label> Application Ref: </label> <p> {{ reference }} </p>
    <label> Valid Date: </label> <p> {{ date_validated }} </p>
    <label> Main Location: </label> <p> {{ address|html }} </p>
    <label> Application Description: </label> <p> {{ description }} </p>
    """
    _scrape_optional_data = list(SwiftLGLabel2Scraper._scrape_optional_data) # copies the original
    _scrape_optional_data.extend([ 
    '<label> Submitted Date: </label> <p> {{ date_received }} </p>',
    ])
    
    detail_tests = [
        { 'uid': '12/0356', 'len': 17 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 28 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 5 } ]

class OxfordshireScraper(SwiftLGLabel2Scraper):

    data_start_target = '2008-06-01'
    batch_size = 60 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 42 # start this number of days ago when gathering current ids
    _search_url = 'http://myeplanning.oxfordshire.gov.uk/swiftlg/apas/run/Wphappcriteria.display'
    _authority_name = 'Oxfordshire'
    
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <label> Application Ref: </label> <p> {{ reference }} </p>
    <label> Valid Date: </label> <p> {{ date_validated }} </p>
    <label> Main Location: </label> <p> {{ address|html }} </p>
    <label> Description of Development: </label> <p> {{ description }} </p>
    """
    _scrape_optional_data = list(SwiftLGLabel2Scraper._scrape_optional_data) # copies the original
    _scrape_optional_data.extend([ 
    '<label> Applicant Name: </label> <p> {{ applicant_name }} </p>',
    '<label> Agent Name: </label> <p> {{ agent_name }} </p>',
    ])

    detail_tests = [
        { 'uid': 'MW.0123/11', 'len': 17 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 16 }, 
        { 'from': '15/08/2012', 'to': '15/08/2012', 'len': 1 } ]
        
class PembrokeshireScraper(SwiftLGLabel2Scraper):

    data_start_target = '2000-01-11'
    batch_size = 38 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 38 # min number of days to get when gathering current ids
    
    _search_url = 'http://planning.pembrokeshire.gov.uk/swiftlg/apas/run/wphappcriteria.display'
    _authority_name = 'Pembrokeshire'
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <label> Application Ref: </label> <p> {{ reference }} </p>
    <label> Validated Date: </label> <p> {{ date_validated }} </p>
    <label> Main Location: </label> <p> {{ address|html }} </p>
    <label> Full Description: </label> <p> {{ description }} </p>
    """
    _scrape_optional_data = list(SwiftLGLabel2Scraper._scrape_optional_data) # copies the original
    _scrape_optional_data.extend([ 
    '<label> Site Notice End: </label> <p> {{ site_notice_end_date }} </p>',
    '<label> Publicity Notice End: </label> <p> {{ consultation_end_date }} </p>',
    '<div id="fieldset_data"> <label> Case Officer: </label> {{ case_officer }} </div>',
    '<h2> Applicant Details </h2> {* <div id="fieldset_data"> <label /> {{ [applicant_name] }} </div> *} <div id="fieldset_data"> <label> Address: </label> </div>',
    '<h2> Agent Details </h2> {* <div id="fieldset_data"> <label /> {{ [agent_name] }} </div> *} <div id="fieldset_data"> <label> Address: </label> </div>',
    '<h2> Applicant Details </h2> <div id="fieldset_data"> <label> Address: </label> {{ applicant_address }} </div>',
    '<h2> Agent Details </h2> <div id="fieldset_data"> <label> Address: </label> {{ agent_address }} </div>',
    ])
    
    detail_tests = [
        { 'uid': '11/0454/PA', 'len': 17 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 24 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 6 } ]
        
class PrestonScraper(SwiftLGSpan2Scraper): 

    _search_url = 'http://publicaccess.preston.gov.uk/swift/apas/run/wphappcriteria.display'
    _authority_name = 'Preston'
    _comment = 'Was AppSearchServ'
    _search_form = '1'
    _scrape_ids = """
    <form action="WPHAPPSEARCHRES"> <table> <tr />
    {* <tr>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    </tr> *}
    </table> </form>
    """
    _scrape_next_link = """
    <p> Pages : <a href="{{ next_link }}"> </p>
    """
    _scrape_max_recs = [
        'returned {{ max_recs }} matches',
        'found {{ max_recs }} matching',
        '<p> Search results: {{ max_recs }} <br>',
        'returned {{ max_recs }} matche(s).',
        'Matches returned - {{ max_recs }} .'
    ]
    
    detail_tests = [
        { 'uid': '06/2012/0630', 'len': 12 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 14 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]
        
class RedbridgeScraper(SwiftLGLabel2Scraper): 

    _search_url = 'http://planning.redbridge.gov.uk/swiftlg/apas/run/wphappcriteria.display'
    _authority_name = 'Redbridge'
    _search_form = '1'
    _scrape_next_link = """ 
        <form> Pages <a /> <a href="{{ next_link }}"> </form>
        """
    
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <label> Application Ref: </label> <p> {{ reference }} </p>
    <label> Site Location: </label> <p> {{ address|html }} </p>
    <label> Registration Date: </label> <p> {{ date_validated }} </p>
    <label> Full Description: </label> <p> {{ description }} </p>
    """
    _scrape_optional_data = list(SwiftLGLabel2Scraper._scrape_optional_data) # copies the original
    _scrape_optional_data.extend([ 
    '<label> Details of Progress: </label> <p> {{ status }} </p>',
    '<h3> Applicant Details </h3> {* <label /> <div> {{ [applicant_name] }} </div> *} <label> Address: </label> <div/>',
    '<h3> Agent Details </h3> {* <label /> <div> {{ [agent_name] }} </div> *} <label> Address: </label> <div/>',
    '<h3> Applicant Details </h3> <label> Address: </label> <div> {{ applicant_address }} </div>',
    '<h3> Agent Details </h3> <label> Address: </label> <div> {{ agent_address }} </div>',
    ])
    
    detail_tests = [
        { 'uid': '1631/11', 'len': 13 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 49 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 20 } ]

class RutlandScraper(SwiftLGLabel2Scraper): 

    _search_url = 'http://planningonline.rutland.gov.uk/swift/apas/run/wphappcriteria.display'
    _authority_name = 'Rutland'
    _comment = 'Was AppSearchServ'
    
    detail_tests = [
        { 'uid': 'APP/2012/0552', 'len': 17 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 18 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ]
        
class SloughScraper(SwiftLGLabel2Scraper):

    _search_url = 'http://www2.slough.gov.uk/swiftlg/apas/run/wphappcriteria.display'
    _authority_name = 'Slough'
    
    detail_tests = [
        { 'uid': 'P/00162/056', 'len': 15 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 16 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 4 } ]
        
class SnowdoniaScraper(SwiftLGLabel2Scraper): 

    _search_url = 'http://planning.snowdonia-npa.gov.uk/swiftlg_snpa/apas/run/wphappcriteria.display'
    _authority_name = 'Snowdonia'
    
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <label> Application Ref: </label> <p> {{ reference }} </p>
    <label> Registration Date: </label> <p> {{ date_validated }} </p>
    <label> Location </label> <p> {{ address|html }} </p>
    <label> Proposal: </label> <p> {{ description }} </p>
    """
    
    detail_tests = [
        { 'uid': 'NP5/66/230', 'len': 17 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 33 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 2 } ]
        
class SouthCambridgeshireScraper(SwiftLGLabel2Scraper):

    _search_url = 'http://plan.scambs.gov.uk/swiftlg/apas/run/wphappcriteria.display'
    _authority_name = 'SouthCambridgeshire'
    _search_form = '1'
    
    detail_tests = [
        { 'uid': 'S/01021/12NM', 'len': 14 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 50 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 16 } ]
        
class WalsallScraper(SwiftLGSpanScraper):

    _search_url = 'http://planning.walsall.gov.uk/swift/apas/run/wphappcriteria.display'
    _authority_name = 'Walsall'
    _comment = 'was Custom'
    
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <span> Application Number: </span> <p> {{ reference }} </p>
    <span> Proposal: </span> <p> {{ description }} </p>
    <span> Site Address: </span> <p> {{ address|html }} </p>
    <span> Valid Date: </span> <p> {{ date_validated }} </p>
    """
    
    detail_tests = [
        { 'uid': '12/1038/FL', 'len': 17} ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 48 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 4 } ]
        
    def _clean_record(self, record):
        dr = record.get('date_received') # swap these two dates as they are the wrong way round on this site
        dv = record.get('date_validated')
        record['date_received'] = dv
        record['date_validated'] = dr
        super(WalsallScraper, self)._clean_record(record)
        
class WarringtonScraper(SwiftLGStrongScraper):

    _search_url = 'http://planning.warrington.gov.uk/swiftlg/apas/run/wphappcriteria.display'
    _authority_name = 'Warrington'
    _search_form = '2'
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <h2> Application&#160;Number: {{ reference }} </h2>
    <p> <strong> Registration Date: </strong> {{ date_validated }} </p>
    <p> <strong> Main Location: </strong> </p> <p> {{ address|html }} </p>
    <p> <strong> Proposal: </strong> {{ description }} </p>
    """
    
    detail_tests = [
        { 'uid': '2011/18599', 'len': 14 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 27 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 6 } ]
        
class WarwickshireScraper(SwiftLGSpanScraper):

    batch_size = 60 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 60 # start this number of days ago when gathering current ids
    _search_url = 'https://planning.warwickshire.gov.uk/swiftlg/apas/run/wphappcriteria.display'
    _authority_name = 'Warwickshire'
    _search_form = '1'
    
    detail_tests = [
        { 'uid': 'WDC/11CC015', 'len': 21} ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '13/11/2012', 'len': 12 }, 
        { 'from': '15/08/2012', 'to': '15/08/2012', 'len': 1 } ]
        
class WorcestershireScraper(SwiftLGSpanScraper):
    
    data_start_target = '2004-12-01'
    batch_size = 60 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 60 # start this number of days ago when gathering current ids
    _search_url = 'http://e-planning.worcestershire.gov.uk/swift/apas/run/wphappcriteria.display'
    _authority_name = 'Worcestershire'
    _comment = 'Was PublicAccess'
    
    detail_tests = [
        { 'uid': '15/000025/CL', 'len': 20} ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '13/10/2012', 'len': 6 }, 
        { 'from': '15/08/2012', 'to': '15/08/2012', 'len': 3 } ]
        
""" # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = '<body> {{ block|html }} </body>'
    # flags defining field boundaries
    _start_flag = '<label>'
    _mid_flag = '</label>'
    _end_flag = '<label/>'
    # config scrape templates for all fields
    _scrape_config = {
    'reference': "__start__ Application Reference __mid__ {{ __field__ }} __end__",
    'planning_portal_id': "__start__ Web Reference __mid__ {{ __field__ }} __end__",
    'date_validated': "__start__ Registration __mid__ {{ __field__ }} __end__",
    'address': "__start__ Location __mid__ {{ __field__ }} __end__",
    'application_type': "__start__ Application Type __mid__ {{ __field__ }} __end__",
    'date_received': "__start__ Application Date __mid__ {{ __field__ }} __end__",
    'description': "__start__ Proposal __mid__ {{ __field__ }} __end__",
    'status': "__start__ Status __mid__ {{ __field__ }} __end__",
    'ward_name': "__start__ Ward __mid__ {{ __field__ }} __end__",
    'parish': "__start__ Parish __mid__ {{ __field__ }} __end__",
    'district': "__start__ Area __mid__ {{ __field__ }} __end__",
    'case_officer': "__start__ Case Officer __mid__ {{ __field__ }} __end__",
    'planning_portal_id': "__start__ Web reference __mid__ {{ __field__ }} __end__",
    'applicant_name': "Applicant Details __start__ Company __mid__ {{ __field__ }} __end__", 
    'agent_name': "Agent Details __start__ Company __mid__ {{ __field__ }} __end__",
    #'applicant_name': "Applicant Details {* __start__ __mid__ {{ [__field__] }} __end__ *} __start__ Address __mid__ ",
    #'agent_name': "Agent Details {* __start__ __mid__ {{ [__field__] }} __end__ *}  __start__ Address __mid__ ",
    'applicant_address': "Applicant Details __start__ Address __mid__ {{ __field__ }} __end__",
    'agent_address': "Agent Details __start__ Address __mid__ {{ __field__ }} __end__",
    'decision_date': "__start__ Decision Date __mid__ {{ __field__ }} __end__",
    'decision': "__start__ Decision: __mid__ {{ __field__ }} __end__",
    'consultation_start_date': "__start__ Publicity Start Date __mid__ {{ __field__ }} __end__",
    'consultation_end_date': "__start__ Publicity End Date __mid__ {{ __field__ }} __end__",
    'comment_url': '__start__ Comment __mid__ <a href="{{ __field__|abs }}"> Comment </a>',
    }

    def __init__(self, *args, **kwargs):
        super(SwiftLGScraper, self).__init__(*args, **kwargs)
        self._scrape_optional_data = []
        for k, v in self._scrape_config.items():
            v = v.replace('__start__', self._start_flag)
            v = v.replace('__mid__', self._mid_flag)
            v = v.replace('__end__', self._end_flag)
            v = v.replace('__field__', k)
            if k == 'reference':
                self._scrape_min_data = v
            else:
                self._scrape_optional_data.append(v)"""

"""class BostonScraper(SwiftLGScraper): # now custom ASP website

    # note fixed IP address was 194.72.114.25
    _search_url = 'http://93.93.220.239/swiftlg/apas/run/wphappcriteria.display'
    _authority_name = 'Boston'
    _end_flag = "<br>"
    _scrape_config = dict(SwiftLGScraper._scrape_config) # copies the original
    _scrape_config.update({
        'address': "__start__ Location __mid__ {{ __field__ }} <p/>",
        'case_officer': "__start__ Case Officer __mid__ {{ __field__ }} <h2/>",
    })
    detail_tests = [
        { 'uid': 'B/13/0192', 'len': 12 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 14 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 } ]
        
class EastHertfordshireScraper(SwiftLGScraper): now Idox

    search_url = 'http://online.eastherts.gov.uk/swiftlg/apas/run/wphappcriteria.display'
    TABLE_NAME = 'EastHertfordshire'
    ID_ORDER = "CASE uid WHEN substr(uid, 3, 2) < '50' THEN '20' || uid ELSE '19' || uid END desc"
    scrape_ids = ""
    <form> <table /> <table> <tr />
    {* <tr>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    </tr> *}
    </table> </form>
    ""
    start_flag = '<b>'
    mid_flag = '</b>'
    end_flag = '<b/>'
    scrape_variants = {
        'status': "__start__ Status __mid__ <td> {{ __field__|html }} </td>",
        'consultation_start_date': "<label> Publicity Start Date </label> {{ __field__ }} <br>",
        'consultation_end_date': "<label> Publicity End Date </label> {{ __field__ }} <br>",
        'applicant_name': "Applicant __start__ Company __mid__ <td> {{ __field__ }} </td>",
        'agent_name': "Agent __start__ Company __mid__ <td> {{ __field__ }} </td>",
        'applicant_address': "Applicant __start__ Address __mid__ <td> {{ __field__ }} </td>",
        'agent_address': "Agent __start__ Address __mid__ <td> {{ __field__ }} </td>",
    }

class EnfieldScraper(SwiftLGScraper): now Idox

    search_url = 'http://forms.enfield.gov.uk/swiftlg/apas/run/wphappcriteria.display'
    TABLE_NAME = 'Enfield'
    field_dot_suffix = True
    end_flag = "<br>"
    scrape_variants = {
        'case_officer': "__start__ Case Officer __mid__ {{ __field__ }} <h2/>",
    }
    
class IslingtonScraper(SwiftLGScraper): now Planning Explorer

    _search_url = 'https://www.islington.gov.uk/onlineplanning/apas/run/wphappcriteria.display'
    _authority_name = 'Islington'
    _disabled = True
    _field_dot_suffix = True
    _html_subs = {
    r'</(t[dhr]) class=".*?">': r'</\1>',
    r"<a href='([^']*?)&(?:amp;)*[bB]ackURL=[^']*?'>": r"<a href='\1'>",
    r'<a href="([^"]*?)&(?:amp;)*[bB]ackURL=[^"]*?">': r'<a href="\1">',
    }
    _scrape_config = dict(SwiftLGScraper._scrape_config) # copies the original
    _scrape_config.update({
        'reference': "__start__ Application Number __mid__ {{ __field__ }} __end__",
        'date_validated': "__start__ Date Valid __mid__ {{ __field__ }} __end__",
        'status': "__start__ Status __mid__ <td> {{ __field__|html }} </td>",
        'consultation_start_date': "__start__ Consultation Start __mid__ {{ __field__ }} __end__",
        'consultation_end_date': "__start__ Consultation End __mid__ {{ __field__ }} __end__",
        'applicant_address': "Applicant Details __start__ Address __mid__ {{ __field__ }} <h2/>",
        'agent_address': "Agent Details__start__ Address __mid__ {{ __field__ }} <h2/>",
        'decision_date': "__start__ Decision Date __mid__ {{ __field__ }} __start__ Decision __mid__ Consultation",
        'decision': "__start__ Decision Date __mid__ __start__ Decision __mid__ {{ __field__ }} __end__ Consultation", 
    })
    detail_tests = [
        { 'uid': 'P081406(MA01)', 'len': 15 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 74 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 6 } ]

class MaidstoneScraper(SwiftLGScraper): # now Idox MidKent

    _search_url = 'http://www.maidstone.gov.uk/swiftlg/apas/run/wphappcriteria.display'
    _authority_name = 'Maidstone'
    field_dot_suffix = True
    scrape_variants = {
        'reference': "__start__ Application Ref __mid__ {{ __field__ }} __end__",
        'description': "__start__ Full Description __mid__ {{ __field__ }} __end__",
        'status': "__start__ Status Description __mid__ {{ __field__ }} __end__",
        'case_officer': "__start__ Case Officer __mid__ {{ __field__ }} <h2/>",
        'agent_address': "Agent Details __start__ Address __mid__ <p> {{ __field__ }} </p>",
    }

class NorthDorsetScraper(SwiftLGScraper): # now Idox

    _search_url = 'http://plansearch.north-dorset.gov.uk/swiftlg/apas/run/wphappcriteria.display'
    _authority_name = 'NorthDorset'
    ID_ORDER = 'uid desc'
    scrape_variants = {
        'reference': "__start__ Application Ref __mid__ {{ __field__ }} __end__",
        'description': "__start__ Full Description __mid__ {{ __field__ }} __end__",
        'status': "__start__ Status Description __mid__ <p> {{ __field__ }} </p>",
        'case_officer': "__start__ Case Officer __mid__ {{ __field__ }} <h2/>",
        'agent_address': "Agent Details __start__ Address __mid__ <p> {{ __field__ }} </p>",
    }

class RochdaleScraper(SwiftLGScraper): # note no applications after 28 May 2012 - it's Idox after that

    search_url = 'http://online.rochdale.gov.uk/swiftlg/apas/run/wphappcriteria.display'
    TABLE_NAME = 'Rochdale'
    field_dot_suffix = True
    end_flag = '<br>'
    scrape_variants = {
        'address': "__start__ Location __mid__ {{ __field__ }} <p/>",
        'description': "__start__ Description __mid__ {{ __field__ }} __end__",
        'case_officer': "__start__ Case Officer __mid__ {{ __field__ }} <h2/>",
    }"""
    





