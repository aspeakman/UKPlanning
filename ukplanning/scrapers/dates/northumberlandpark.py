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
try:
    from ukplanning import scrapeutils
except ImportError:
    import scrapeutils
import urllib, urlparse

# also see Wychavon, WelwynHatfield, Nottinghamshire, Lancashire, Devon and CCED = Christchurch and East Dorset

class NorthumberlandParkScraper(base.DateScraper):

    data_start_target = '2000-03-01'
    min_id_goal = 150 # min target for application ids to fetch in one go
    batch_size = 28 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 28 # start this number of days ago when gathering current ids
    
    _authority_name = 'NorthumberlandPark'
    _handler = 'etree'
    _search_url = 'http://nnpa.planning-register.co.uk/PlaPlanningAppAdvSearch.aspx?mode=reset'
    _applic_url = 'http://nnpa.planning-register.co.uk/plaPlanningAppDisplay.aspx?AppNo='
    _date_from_field3 = 'ctl00_ContentPlaceHolder1_txtAppValFrom_dateInput_ClientState'
    _date_to_field3 = 'ctl00_ContentPlaceHolder1_txtAppValTo_dateInput_ClientState'
    _date_from_field = 'ctl00$ContentPlaceHolder1$txtAppValFrom$dateInput'
    _date_to_field = 'ctl00$ContentPlaceHolder1$txtAppValTo$dateInput'
    _date_from_field2 = 'ctl00$ContentPlaceHolder1$txtAppValFrom'
    _date_to_field2 = 'ctl00$ContentPlaceHolder1$txtAppValTo'
    _search_fields = { '__EVENTTARGET': '', '__EVENTARGUMENT': '', }
    _search_form = '#form1'
    _search_submit = 'ctl00$ContentPlaceHolder1$btnSubmit'
    _request_date_format3 = '{"enabled":true,"emptyMessage":"","validationText":"%Y-%m-%d-00-00-00","valueAsString":"%Y-%m-%d-00-00-00","minDateStr":"1900-01-01-00-00-00","maxDateStr":"2099-12-31-00-00-00","lastSetTextBoxValue":"%d/%m/%Y"}'
    _request_date_format2 = '%Y-%m-%d'
    _scrape_next_submit = '<input class="rgPageNext" name="{{ next_submit }}">'
    _scrape_max_recs = '<div class="rgWrap rgInfoPart"> <strong> {{ max_recs }} </strong> items </div>'
    _scrape_ids = """
    <table class="rgMasterTable"> <tbody>
    {* <tr>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    </tr> *}
    </tbody> </table>
    """
    _scrape_ids2 = """
    <table class="rgMasterTable"> <tfoot /> <tbody>
    {* <tr>
    <td> <a href="{{ [records].url|abs }}"> {{ [records].uid }} </a> </td>
    </tr> *}
    </tbody> </table>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = '<div id="contentbody"> {{ block|html }} </div>'
    # the minimum acceptable valid dataset on the details page
    _scrape_min_data = """
    <input id="ContentPlaceHolder1_txtAppNum" value="{{ reference }}">
    <textarea id="ContentPlaceHolder1_txtLoc"> {{ address }} </textarea>
    <textarea id="ContentPlaceHolder1_txtProposal"> {{ description }} </textarea>
    <input id="ContentPlaceHolder1_txtRecDate" value="{{ date_received }}">
    <input id="ContentPlaceHolder1_txtValidDate" value="{{ date_validated }}">
    """
    # other optional parameters common to all scrapers can appear on the details page
    _scrape_optional_data = [
    '<input id="ContentPlaceHolder1_txtDistrict" value="{{ district }}">',
    '<input id="ContentPlaceHolder1_txtWard" value="{{ ward_name }}">',
    '<input id="ContentPlaceHolder1_Label4" value="{{ parish }}">',
    '<input id="ContentPlaceHolder1_txtEasting" value="{{ easting }}">',
    '<input id="ContentPlaceHolder1_txtNorthing" value="{{ northing }}">',
    '<input id="ContentPlaceHolder1_txtAppStatus" value="{{ status }}">',
    '<input id="ContentPlaceHolder1_txtAppName" value="{{ applicant_name }}">',
    '<input id="ContentPlaceHolder1_txtAgName" value="{{ agent_name }}">',
    '<textarea id="ContentPlaceHolder1_txtAppAddress"> {{ applicant_address }} </textarea>',
    '<textarea id="ContentPlaceHolder1_txtAgAddress"> {{ agent_address }} </textarea>',
    '<input id="ContentPlaceHolder1_txtDecDate" value="{{ decision_date }}">',
    '<input id="ContentPlaceHolder1_txtDec" value="{{ decision }}">',
    '<input id="ContentPlaceHolder1_txtAplDate" value="{{ appeal_date }}">',
    '<input id="ContentPlaceHolder1_txtAplDec" value="{{ appeal_result }}">',
    '<input id="ContentPlaceHolder1_txtPlanOff" value="{{ case_officer }}">',
    ]
    detail_tests = [
        { 'uid': '11NP0040EL', 'len': 16 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/10/2012', 'len': 14 },
        { 'from': '23/08/2012', 'to': '23/08/2012', 'len': 1 }  ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s" % response.read())
        
        fields = {}
        fields.update(self._search_fields)
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        fields[self._date_from_field2] = date_from.strftime(self._request_date_format2)
        fields[self._date_to_field2] = date_to.strftime(self._request_date_format2)
        fields[self._date_from_field3] = date_from.strftime(self._request_date_format3)
        fields[self._date_to_field3] = date_to.strftime(self._request_date_format3)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br, self._search_submit)
        
        # note max_recs does not appear if there is only one page
        try:
            html = response.read()
            result = scrapemark.scrape(self._scrape_max_recs, html)
            num_recs = int(result['max_recs'])
        except:
            num_recs = 0
            
        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        while response and page_count < max_pages and (len(final_result) < num_recs or num_recs == 0):
            url = response.geturl()
            #self.logger.debug("Batch html: %s" % html)
            if num_recs == 0:
                result = scrapemark.scrape(self._scrape_ids, html, url)
            else:
                result = scrapemark.scrape(self._scrape_ids2, html, url)
            if result and result.get('records'):
                page_count += 1
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            else:
                self.logger.debug("Empty result after %d pages", page_count)
                break
            if len(final_result) >= num_recs or num_recs == 0: break
            try:
                #self.logger.debug(scrapeutils.list_forms(self.br))
                result = scrapemark.scrape(self._scrape_next_submit, html)
                fields = {}
                fields.update(self._search_fields)
                scrapeutils.setup_form(self.br, self._search_form, fields)
                #for control in self.br.form.controls:
                #    if control.type == "submit" and control.name <> result['next_submit']:
                #        control.disabled = True
                self.logger.debug("ID next form: %s", str(self.br.form))
                response = scrapeutils.submit_form(self.br, result['next_submit'])
                html = response.read()
            except: # normal failure to find next page form at end of page sequence here
                self.logger.debug("No next form after %d pages", page_count)
                break
        
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
     
        return final_result

    def get_html_from_uid(self, uid): 
        url =  self._applic_url + urllib.quote_plus(uid)
        return self.get_html_from_url(url)
        

        

