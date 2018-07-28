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
#from .. import base
import urllib, urlparse
from datetime import date
from annuallist import AnnualListScraper

# dates now based on JSON API which does not seem to work externally

# this version works from the sequence of application numbers 
# in this form X/YYYY/NNNN where X is in A,S,SSI,P,PP,RC,RP,RW

class JerseyScraper(AnnualListScraper):

    min_id_goal = 100 # min target for application ids to fetch in one go
    current_span = 30 # min number of records to get when gathering current ids
    data_start_target = 20000001 # gathering back to this record number (in YYYYNNNN format derived from the application number in this format = X/YYYY/NNNN)
    
    _disabled = False
    _authority_name = 'Jersey'
    _max_index = 2500 # maximum records per year
    _handler = 'etree'
    _search_url = 'https://www.mygov.je/Planning/Pages/Planning.aspx'
    _applic_url = 'https://www.mygov.je/Planning/Pages/PlanningApplicationDetail.aspx?s=1&r='
    _scrape_dates_link = '<a href="{{ dates_link|abs }}"> Application timeline </a>'

    _prefixes = [ 'P', 'A', 'RC', 'RP', 'RW', 'S', 'PP', 'SSI' ]
    _scrape_id = '<div class="pln-maincontent"> <th> Application Reference </th> <td> {{ uid }} </td> </div>'
    _scrape_invalid_format = '<h1> Sorry, {{ invalid_format }} went wrong </h1>'
    _scrape_ids = """
    <table id="PlanningApplicationSearchResultASPPanel"> <table>
    {* <table>
    <tr> <td> {{ [records].uid }} </td> </tr>
    <tr> <td /> <td> <a href="{{ [records].url|abs }}"> </a> </td> </tr>
    </table> *}
    </table>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = '<div class="pln-maincontent"> {{ block|html }} </div>'
    _scrape_dates_block = '<div class="pln-maincontent"> {{ block|html }} </div>'
    _scrape_min_data = """
    <th> Application Reference </th> <td> {{ reference }} </td>
    <th> Description </th> <td> {{ description }} </td>
    <th> Property </th> <td> {{ [address] }} </td>
    <th> Road </th> <td> {{ [address] }} </td>
    <th> Parish </th> <td> {{ [address] }} </td>
    <th> Postcode </th> <td> {{ [address] }} </td>
    """
    _scrape_min_dates = """
    <tr> <th> Validated </th> <td> {{ date_validated }} </td> </tr>
    """
    # min field list used in testing only
    _min_fields = [ 'reference', 'address', 'description', 'date_validated' ]
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<tr> <th> Officer Responsible </th> <td> {{ case_officer }} </td> </tr>',
    '<tr> <th> Status </th> <td> {{ status }} </td> </tr>',
    '<tr> <th> Parish </th> <td> {{ parish }} </td> </tr>',
    '<tr> <th> Postcode </th> <td> {{ postcode }} </td> </tr>',
    '<tr> <th> Applicant </th> <td> {{ applicant_name }} </td> </tr>',
    '<tr> <th> Applicant </th> <td> {{ applicant_name }} , {{ applicant_address }} </td> </tr>',
    '<tr> <th> Agent </th> <td> {{ agent_name }} </td> </tr>',
    #'<tr> <th> Constraints </th> <td> {{ constraints }} </td> </tr>',
    '<tr> <th> Agent </th> <td> {{ agent_name }} , {{ agent_address }} </td> </tr>',
    'window.MapCentreLatitude = {{ latitude }}; window.MapCentreLongitude = {{ longitude }};',
    ]
    _scrape_optional_dates = [
    '<tr> <th> Advertised </th> <td> {{ last_advertised_date }} </td> </tr>',
    '<tr> <th> End Publicity </th> <td> {{ consultation_end_date }} </td> </tr>',
    '<tr> <th> Committee </th> <td> {{ meeting_date }} </td> </tr>',
    '<tr> <th> Decision </th> <td> {{ decision_date }} </td> </tr>',
    '<tr> <th> Appeal </th> <td> {{ appeal_date }} </td> </tr>',
    ]
    detail_tests = [
        { 'uid': 'P/2011/0599', 'len': 18 }   ]
    batch_tests = [ 
        { 'from': '20120506', 'to': '20120516', 'len': 9 },
        { 'from': '20119998', 'to': '20120008', 'len': 7 },
        { 'from': '20122490', 'to': '20122510', 'len': 5 }, ]
   
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
            found = False
            for prefix in self._prefixes:
                uid =  prefix + self.get_uid(index, year)
                html, url = self.get_html_from_uid(uid)
                result = scrapemark.scrape(self._scrape_min_data, html)
                if result and result.get('reference'):
                    final_result.append( { 'url': url, 'uid': uid } )
                    found = True
                    break
            if not found:
                result = scrapemark.scrape(self._scrape_invalid_format, html)
                if result and result.get('invalid_format'):
                    self.logger.debug("No valid record for uid ?/%s/%s" % (str(year), str(index).zfill(self._index_digits)))
                else:
                    return [], None, None # not recognised as bad data - something is wrong - exit
                    
        if not in_current_year or final_result:
            return final_result, rfrom, rto
        else:
            return [], None, None # empty result is invalid if any of the results are in the current year
        
    def get_uid(self, index, year):
        # create a uid from year and index integer values
        uid = '/' + str(year) + '/' + str(index).zfill(self._index_digits) 
        return uid  
        
    def get_html_from_uid (self, uid):
        url = self._applic_url + urllib.quote_plus(uid)
        return self.get_html_from_url(url)
        
    def _get_details(self, html, this_url):
        """ Scrapes detailed information for one record given html and url 
        - this is an optional hook to allow data from multiple linked pages to be merged """
        result = self._get_detail(html, this_url)
        if 'scrape_error' in result:
            return result
        try:
            temp_result = scrapemark.scrape(self._scrape_dates_link, html, this_url)
            dates_url = temp_result['dates_link']
            self.logger.debug("Dates url: %s", dates_url)
            response = self.br.open(dates_url)
            html, url = self._get_html(response)
        except:
            self.logger.warning("No link to dates page found")
        else:
            #self.logger.debug("Html obtained from dates url: %s", html)
            result2 = self._get_detail(html, url, self._scrape_dates_block, self._scrape_min_dates, self._scrape_optional_dates)
            if 'scrape_error' not in result2:
                result.update(result2)
            else:
                self.logger.warning("No information found on dates page")
        return result
        
    # test trying to access the JSON data source directly - think the parameters are correct 
    # but does not seem to work (times out) - presumably access to external data requests is forbidden?
    #request = urllib2.Request('https://www.mygov.je/_layouts/PlanningAjaxServices/PlanningSearch.svc/Search')
    #request.add_header('Content-Type', 'application/json; charset=utf-8')
    #url = 'https://www.mygov.je/Planning/Pages/Planning.aspx'
    #data = { 'URL': url,
    #    'CommonParameters': '|05|1||49.21042016382462|-2.1445659365234633|12',
    #    'SearchParameters': '|1301||||0|All|All|8|8|2011|8|9|2011' }
    #dd = json.dumps(data)
    #print dd
    #resp = urllib2.urlopen(request, dd, 30)
    #print resp.info()
    #print json.load(resp)

