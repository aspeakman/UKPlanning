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
from datetime import date
try:
    from ukplanning import scrapemark
except ImportError:
    import scrapemark
try:
    from ukplanning import scrapeutils
except ImportError:
    import scrapeutils
from .. import base
import re
import urllib

# also see SurreyHeath and Elmbridge

class AstunScraper(base.DateScraper):

    min_id_goal = 300 # min target for application ids to fetch in one go
    
    _scraper_type = 'Astun'
    _search_form = '1'
    _search_fields = { 'maxrecords': '300' }
    _next_link = 'Next >'
    _scrape_ids = """
    <div class="atSearchResults">
    {* <div>
    <p> <a href="{{ [records].url|abs }}" /> </p>
    <p> Application reference: {{ [records].uid }} received </p>
    </div> *}
    </div>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <div class="atSearchDetails"> {{ block|html }} </div>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <dl> <dt> Application Reference: </dt> <dd> {{ reference }} </dd>
    <dt> Address of Proposal: </dt> <dd> {{ address }} </dd>
    <dt> Proposal: </dt> <dd> {{ description }} </dd> </dl>
    <dl> <dt> Date Application Received: </dt> <dd> {{ date_received }} </dd>
    <dt> Date Application Validated: </dt> <dd> {{ date_validated }} </dd> </dl>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<dt> Planning Portal Reference Number </dt> <dd> {{ planning_portal_id }} </dd>',
    '<dt> Type of Application </dt> <dd> {{ application_type }} </dd>',
    '<dt> Status </dt> <dd> {{ status }} </dd> <dt> Appeal Status </dt>',
    """<dt> Decision </dt> <dd> {{ decision }} </dd>
    <dt> Decision Type </dt> <dd> {{ decided_by }} </dd>""",
    '<dt> Ward </dt> <dd> {{ ward_name }} </dd>',
    '<dt> Parish </dt> <dd> {{ parish }} </dd>',
    '<dt> District Reference </dt> <dd> {{ district }} </dd>',
    '<dt> Case Officer </dt> <dd> {{ case_officer }} </dd>',
    '<dt> Appeal Reference </dt> <dd> {{ appeal_reference }} </dd>',
    '<dt> Appeal Status </dt> <dd> {{ appeal_status }} </dd>',
    '<h4> Applicant </h4> <dt> Name </dt> <dd> {{ applicant_name }} </dd> <dt> Address </dt> <dd> {{ applicant_address }} </dd>',
    '<h4> Agent </h4> <dt> Name </dt> <dd> {{ agent_name }} </dd> <dt> Address </dt> <dd> {{ agent_address }} </dd>',
    "<dt> Applicant </dt> <dd> {{ applicant_name }} </dd> <dt> Address </dt> <dd> {{ applicant_address }} </dd>",
    "<dt> Agent </dt> <dd> {{ agent_name }} </dd> <dt> Address </dt> <dd> {{ agent_address }} </dd>",
    '<dt> Target Determination Date </dt> <dd> {{ target_decision_date }} </dd>',
    '<dt> Actual Committee Date </dt> <dd> {{ meeting_date }} </dd>',
    '<dt> Neighbourhood Consultations sent on </dt> <dd> {{ neighbour_consultation_start_date }} </dd>',
    '<dt> Expiry Date for Neighbour Consultations </dt><dd> {{ neighbour_consultation_end_date }} </dd>',
    '<dt> Standard Consultations sent on </dt> <dd> {{ consultation_start_date }} </dd>',
    '<dt> Expiry Date for Standard Consultations </dt> <dd> {{ consultation_end_date }} </dd>',
    '<dt> Last Advertised on </dt> <dd> {{ last_advertised_date }} </dd>',
    '<dt> Expiry Date for Latest Advertisement </dt> <dd> {{ latest_advertisement_expiry_date }} </dd>',
    '<dt> Latest Site Notice posted on </dt> <dd> {{ site_notice_start_date }} </dd>',
    '<dt> Expiry Date for Latest Site Notice </dt> <dd>{{ site_notice_end_date }} </dd>',
    '<dt> Date Decision Made </dt> <dd> {{ decision_date }} </dd>',
    '<dt> Date Decision Issued: </dt> <dd> {{ decision_issued_date }} </dd>',
    '<dt> Permission Expiry Date </dt> <dd> {{ permission_expires_date }} </dd>',
    '<dt> Date Decision Printed </dt> <dd> {{ decision_published_date }} </dd>',
    '<a class="atComments forwardlink" href="{{ comment_url|abs }}"> Comment on this application </a>',
    '<img src="../MapGetImage.aspx?RequestType=Map&amp;MapSource=Spelthorne/publisher_planning&amp;Easting={{easting}}&amp;Northing={{northing}}&amp; />'
    '<dt> Map </dt> <dd> <a href="http://maps.rochford.gov.uk/MyRochford.aspx{{dummy}}"> </a> </dd>'
    ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s", response.read())

        fields = {}
        fields.update(self._search_fields)
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        
        html = response.read()
        #self.logger.debug("ID batch page html: %s", html)
        result = scrapemark.scrape(self._scrape_max_pages, html)
        try:
            page_list = result['max_pages'].split()
            max_pages = len(page_list)
        except:
            max_pages = 1
        
        page_count = 0
        while response and page_count < max_pages:
            url = response.geturl()
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                page_count += 1
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            else:
                self.logger.debug("Empty result after %d pages", page_count)
                break
            if page_count >= max_pages: break
            try:
                next_url = re.sub(r'pageno=\d*&', 'pageno=' + str(page_count+1) + '&', url)
                self.logger.debug("ID next url: %s", next_url)
                response = self.br.open(next_url)
                html = response.read()
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next url after %d pages", page_count)
                break
                
        return final_result

    def get_html_from_uid (self, uid):
        query = self._search_query % (uid)
        url = self._applic_url + "?" + query
        return self.get_html_from_url(url)

class SpelthorneScraper(AstunScraper):

    _authority_name = 'Spelthorne'
    _cookies = [
        { 'name': 'astun:readTerms', 'value': 'true', 'domain': 'my.spelthorne.gov.uk', 'path': '/planning/' }
    ]
    _search_form = '2'
    _date_from_field = 'DATEAPRECV:FROM:DATE'
    _date_to_field = 'DATEAPRECV:TO:DATE'
    _search_url = 'http://my.spelthorne.gov.uk/planning/?requesttype=parsetemplate&template=DCSearchAdv.tmplt'
    _applic_url = 'http://my.spelthorne.gov.uk/planningpublisher.aspx'
    #_applic_fields = { 'basepage': 'default.aspx', 'requesttype': 'parsetemplate', 'template': 'DCApplication.tmplt' }
    _search_query = 'requesttype=parsetemplate&template=DCApplication.tmplt&basepage=planningpublisher.aspx&Filter=^REFVAL^=%%27%s%%27'
    _scrape_max_pages = '<div class="atPageNo"> {{ max_pages }} </div>'
    _scrape_ids = """
    <div id="atResultsList">
    {* <div>
    <p> <a href="{{ [records].url|abs }}" /> </p>
    <p> Reference: {{ [records].uid }} | </p>
    </div> *}
    </div>
    """
    
    detail_tests = [
        { 'uid': '12/01236/FUL', 'len': 28 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 41 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 } ]
        
class RochfordScraper(AstunScraper):

    _authority_name = 'Rochford'
    _search_form = '0'
    _date_from_field = 'DATEAPRECV:FROM:DATE'
    _date_to_field = 'DATEAPRECV:TO:DATE'
    #_search_url = 'http://maps.rochford.gov.uk/DevelopmentControl.aspx?RequestType=ParseTemplate&Template=DevelopmentControlSearch.tmplt'
    _search_url = 'http://maps.rochford.gov.uk/DevelopmentControl.aspx?RequestType=ParseTemplate&template=DevelopmentControlAdvancedSearch.tmplt'
    _applic_url = 'http://maps.rochford.gov.uk/DevelopmentControl.aspx'
    #_applic_fields = { 'basepage': 'default.aspx', 'requesttype': 'parsetemplate', 'template': 'DCApplication.tmplt' }
    _search_query = 'requesttype=parsetemplate&template=DevelopmentControlApplication.tmplt&basepage=DevelopmentControl.aspx&Filter=^REFVAL^=%%27%s%%27'
    _scrape_max_pages = '<div class="atSearchResults"> <div id="atSearchAgain" /> <div> Pages: {{ max_pages }} </div> </div>'
    _next_link = 'Next'
    _scrape_ids = """
    <div id="results"> <dl>
    {* <dt> <a href="{{ [records].url|abs }}" /> </dt>
    <dd class="last"> Application reference: <strong> {{ [records].uid }} </strong> </dd>
    *}
    </dl> </div>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <div class="details"> {{ block|html }} </div>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <dl> <dt> Application Reference: </dt> <dd> {{ reference }} </dd>
    <dt> Address of Proposal: </dt> <dd> {{ address }} </dd>
    <dt> Proposal: </dt> <dd> {{ description }} </dd> </dl>
    """
    _scrape_min_dates = """
    <dl> <dt> Date Application Received: </dt> <dd> {{ date_received }} </dd>
    <dt> Date Application Validated: </dt> <dd> {{ date_validated }} </dd> </dl>
    """
    _scrape_min_applicant = """
    <dt> Name: </dt> <dd> {{ applicant_name }} </dd> <dt> Address: </dt> <dd> {{ applicant_address }} </dd>
    """
    _scrape_min_agent = """
    <dt> Name: </dt> <dd> {{ agent_name }} </dd> <dt> Address: </dt> <dd> {{ agent_address }} </dd>
    """
    # min field list used in testing only
    _min_fields = [ 'reference', 'address', 'description', 'date_received', 'applicant_address', 'agent_address' ]
    
    
    detail_tests = [
        { 'uid': '12/00582/FUL', 'len': 27 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '23/09/2013', 'to': '29/10/2013', 'len': 78 }, 
        { 'from': '08/05/2012', 'to': '08/05/2012', 'len': 3 } ]
        
    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s", response.read())

        fields = {}
        fields.update(self._search_fields)
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        for control in self.br.form.controls:
            if control.name == "dateaprecv_date:FROM:DATE":
                control.disabled = True
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        
        """html = response.read()
        self.logger.debug("ID batch page html: %s", html)
        result = scrapemark.scrape(self._scrape_max_pages, html)
        try:
            page_list = result['max_pages'].split()
            max_pages = len(page_list)
        except:
            max_pages = 1"""
        
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        page_count = 0
        while response and page_count < max_pages:
            html = response.read()
            #self.logger.debug("ID batch page html: %s", html)
            url = response.geturl()
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                page_count += 1
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            else:
                self.logger.debug("Empty result after %d pages", page_count)
                break
            if page_count >= max_pages: break
            try:
                next_url = re.sub(r'pageno=\d*&', 'pageno=' + str(page_count+1) + '&', url)
                self.logger.debug("ID next url: %s", next_url)
                response = self.br.open(next_url)
                #html = response.read()
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next url after %d pages", page_count)
                break
        
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
       
        return final_result

    def _get_details(self, html, this_url):
        """ Scrapes detailed information for one record given html and url 
        - this is an optional hook to allow data from multiple linked pages to be merged """
        result = self._get_detail(html, this_url)
        #self.logger.debug("Html : %s", html)
        if 'scrape_error' in result:
            return result
        try:
            dates_url = this_url.replace('DevelopmentControlApplication', 'DevelopmentControlApplication_Dates')
            self.logger.debug("Dates url: %s", dates_url)
            response = self.br.open(dates_url)
            html, url = self._get_html(response)
        except:
            self.logger.warning("No link to dates page found")
        else:
            #self.logger.debug("Html obtained from dates url: %s", html)
            result2 = self._get_detail(html, url, self._scrape_data_block, self._scrape_min_dates, self._scrape_optional_data)
            if 'scrape_error' not in result2:
                result.update(result2)
            else:
                self.logger.warning("No information found on dates page")
        try:
            applicant_url = this_url.replace('DevelopmentControlApplication', 'DevelopmentControlApplication_Applicant')
            self.logger.debug("Applicant url: %s", applicant_url)
            response = self.br.open(applicant_url)
            html, url = self._get_html(response)
        except:
            self.logger.warning("No link to applicant page found")
        else:
            #self.logger.debug("Html obtained from applicant url: %s", html)
            result3 = self._get_detail(html, url, self._scrape_data_block, self._scrape_min_applicant)
            if 'scrape_error' not in result3:
                result.update(result3)
            else:
                self.logger.warning("No information found on applicant page")
        try:
            agent_url = this_url.replace('DevelopmentControlApplication', 'DevelopmentControlApplication_Agent')
            self.logger.debug("Agent url: %s", agent_url)
            response = self.br.open(agent_url)
            html, url = self._get_html(response)
        except:
            self.logger.warning("No link to agent page found")
        else:
            #self.logger.debug("Html obtained from agent url: %s", html)
            result4 = self._get_detail(html, url, self._scrape_data_block, self._scrape_min_agent)
            if 'scrape_error' not in result4:
                result.update(result4)
            else:
                self.logger.warning("No information found on agent page")
        return result

class BathScraper(AstunScraper): 

    _authority_name = 'Bath'
    _date_from_field = 'dateapval:FROM:DATE'
    _date_to_field = 'dateapval:TO:DATE'
    _search_url = 'http://isharemaps.bathnes.gov.uk/projects/bathnes/developmentcontrol/default.aspx?requesttype=parsetemplate&template=DevelopmentControlSearchAdvanced.tmplt'
    _applic_url = 'http://isharemaps.bathnes.gov.uk/data.aspx'
    #_applic_fields = { 'basepage': 'default.aspx', 'requesttype': 'parsetemplate', 
    #    'template': 'DevelopmentControlApplication.tmplt', 'SearchLayer': 'DCApplications', 'SearchField': 'REFVAL' }
    _search_query = 'requesttype=parsetemplate&template=DevelopmentControlApplication.tmplt&basepage=data.aspx&Filter=^refval^=%%27%s%%27&SearchLayer=DCApplications' 
    _scrape_max_pages = '<div class="atPageNo"> Pages: {{ max_pages }} </div>'
    _search_form = '0'
    
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <body> {{ block|html }} </body>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <h3> Reference: {{ reference }} </h3>
    <tr> <td> Address of Proposal: </td> <td> {{ address }} </td> </tr>
    <tr> <td> Proposal: </td> <td> {{ description }} </td> </tr>
    <tr> <td> Date Application Received: </td> <td> {{ date_received }} </td> </tr>
    <tr> <td> Date Application Validated: </td> <td> {{ date_validated }} </td> </tr>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<tr> <td> Planning Portal Reference Number </td> <td> {{ planning_portal_id }} </td> </tr>',
    '<tr> <td> Type of Application </td> <td> {{ application_type }} </td> </tr>',
    '<tr> <td> Status: </td> <td> {{ status }} </td> </tr>',
    """<tr> <td> Decision: </td> <td> {{ decision }} </td> </tr>
    <tr> <td> Decision Type: </td> <td> {{ decided_by }} </td> </tr>""",
    '<tr> <td> Ward: </td> <td> {{ ward_name }} </td> </tr>',
    '<tr> <td> Parish: </td> <td> {{ parish }} </td> </tr>',
    '<tr> <td> Case Officer </td> <td> {{ case_officer }} </td> </tr>',
    '<tr> <td> Appeal Reference </td> <td> {{ appeal_reference }} </td> </tr>',
    '<tr> <td> Appeal Status </td> <td> {{ appeal_status }} </td> </tr>',
    '<tr> <td> Applicant Name </td> <td> {{ applicant_name }} </td> </tr>',
    '<tr> <td> Agent Name </td> <td> {{ agent_name }} </td> </tr>',
    '<tr> <td> Agent Address </td> <td> {{ agent_address }} </td> </tr>',
    '<tr> <td> Target Decision Date </td> <td> {{ target_decision_date }} </td> </tr>',
    '<tr> <td> Actual Committee Date </td> <td> {{ meeting_date }} </td> </tr>',
    '<tr> <td> Neighbourhood Consultations sent on </td> <td> {{ neighbour_consultation_start_date }} </td> </tr>',
    '<tr> <td> Expiry Date for Neighbour Consultations </td> <td> {{ neighbour_consultation_end_date }} </td> </tr>',
    '<tr> <td> Standard Consultations sent on </td> <td> {{ consultation_start_date }} </td> </tr>',
    '<tr> <td> Expiry Date for Consultation </td> <td> {{ consultation_end_date }} <div /> </td> </tr>',
    '<tr> <td> Last Advertised on </td> <td> {{ last_advertised_date }} </td> </tr>',
    '<tr> <td> Expiry Date for Latest Advertisement </td> <td> {{ latest_advertisement_expiry_date }} </td> </tr>',
    '<tr> <td> Latest Site Notice posted on </td> <td> {{ site_notice_start_date }} </td> </tr>',
    '<tr> <td> Expiry Date for Latest Site Notice </td> <td>{{ site_notice_end_date }} </td> </tr>',
    '<tr> <td> Date Decision Made </td> <td> {{ decision_date }} </td> </tr>',
    '<tr> <td> Date Decision Issued </td> <td> {{ decision_issued_date }} </td> </tr>',
    '<tr> <td> Permission Expiry Date </td> <td> {{ permission_expires_date }} </td> </tr>',
    '<tr> <td> Date Decision Printed </td> <td> {{ decision_published_date }} </td> </tr>',
    '<a class="atComments forwardlink" href="{{ comment_url|abs }}"> Comment on this application </a>',
    "var mapeasting = '{{easting}}'; var mapnorthing = '{{northing}}';"
    ]
    detail_tests = [
        { 'uid': '12/04035/FUL', 'len': 25 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 82 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 13 } ]
        
    def _clean_record(self, record):
        super(BathScraper, self)._clean_record(record)
        if record.get('reference'):
            ref = record['reference']
            space_pos = ref.find(' ') # does the reference contain any spaces?
            if space_pos > 0: # strip out anything after and including the space
                record['reference'] = ref[0:space_pos]


