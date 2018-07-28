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
import urllib
try:
    from ukplanning import myutils
except ImportError:
    import myutils
from BeautifulSoup import BeautifulSoup

# Note Exmoor uids have spaces in them, and some bad dates occur, see customised _clean_record() function below

class ExmoorScraper(base.PeriodScraper):

    data_start_target = '2005-01-01' # gathers id data by working backwards from the current date towards this one
    min_id_goal = 200 # min target for application ids to fetch in one go
    
    _authority_name = 'Exmoor'
    _period_type = 'Friday'
    _next_page_link = 'Next Next'
    _request_date_format = '%m/%d/%Y'
    _result_url = 'http://www.exmoor-nationalpark.gov.uk/planning/planning-searches/weekly-list-search-results?weeklylist='
    _search_url = 'http://www.exmoor-nationalpark.gov.uk/planning/planning-searches'
    _applic_url = 'http://www.exmoor-nationalpark.gov.uk/planning/planning-searches/detailed-results?appNo='
    _scrape_ids = """
    <table id="resultsTab"> <tr />
    {* <tr>
    <td> <a href="{{ [records].url|abs }}">
    {{ [records].uid }} </a> </td>
    </tr> *}
    </table>
    """
    _scrape_no_recs = "<p> No results {{ no_recs }} found </p>"
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <div class="uc"> {{ block|html }} </div>
    """
    # the minimum acceptable valid dataset on the details page
    _scrape_min_data = """
    <tr> <td> Application No </td> <td> {{ reference }} </td> </tr>
    <tr> <td> Address </td> <td> {{ address }} </td> </tr>
    <tr> <td> Proposal </td> <td> {{ description }} </td> </tr>
    <tr> <th> Date Received </th> </tr> <tr> <td> {{ date_received }} </td> <td> {{ date_validated }} </td> </tr>
    """
    # other optional parameters common to all scrapers can appear on the details page
    _scrape_optional_data = [
    '<tr> <td> Application Type </td> <td>  {{ application_type }} </td> </tr>',
    '<tr> <td> County </td> <td>  {{ district }} </td> </tr>',
    '<tr> <td> Parish </td> <td>  {{ parish }} </td> </tr>',
    '<tr> <td> Case Officer </td> <td>  {{ case_officer }} </td> </tr>',
    '<tr> <td> Grid Ref </td> <td> {{ easting }} , {{ northing }} </td> </tr>', 
    '<tr> <td> Status </td> <td>  {{ status }} </td> </tr>',
    '<tr> <td> Neighbours/public Consultees Start </td> <td>  {{ neighbour_consultation_start_date }} </td> </tr>',
    '<tr> <td> Neighbours/public Consultees End </td> <td>  {{ neighbour_consultation_end_date }} </td> </tr>',
    '<tr> <td> Site Notice Start </td> <td>  {{ site_notice_start_date }} </td> </tr>',
    '<tr> <td> Site Notice End </td> <td>  {{ site_notice_end_date }} </td> </tr>',
    '<tr> <th> Consultees Start </th> </tr> <tr> <td /> <td /> <td> {{ consultation_start_date }} </td> <td> {{ consultation_end_date }} </td> </tr>',
    """<tr> <th> Target Date </th> </tr> <tr> <td /> <td /> <td /> <td /> 
    <td> {{ target_decision_date }} </td> <td> {{ decision_date }} </td> <td> {{ decision }} </td> </tr>""",
    ]
    detail_tests = [
        { 'uid': '62/41/12/027', 'len': 21 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'date': '13/09/2012', 'len': 11 }, 
        { 'date': '13/08/2012', 'len': 5 } ]

    def get_id_period (self, this_date):

        final_result = []
        from_dt, to_dt = scrapeutils.inc_dt(this_date, self._period_type)

        url = self._result_url + urllib.quote_plus(to_dt.strftime(self._request_date_format))
        self.logger.debug("Search url: %s" % url)
        response = self.br.open(url)

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
                response = self.br.follow_link(text=self._next_page_link)
            except:
                self.logger.debug("No next link after %d pages", page_count)
                break
                
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
        
        return final_result, from_dt, to_dt # weekly scraper - so empty result can be valid

    def get_html_from_uid (self, uid):
        url = self._applic_url + urllib.quote_plus(uid)
        return self.get_html_from_url(url)
        
    def _clean_record(self, record):
        ' post process a scraped record: parses dates, converts to ISO8601 format, strips spaces, tags etc '
        #self.logger.debug("Raw record to clean: %s", str(record))
        for k, v in record.items(): 
            if v:
                if isinstance(v, list):
                    v = ' '.join(v)
                if not v or not myutils.GAPS_REGEX.sub('', v): # always remove any empty fields
                    v = None
                elif k == 'uid': # note some Exmoor uids have internal spaces
                    #v = myutils.GAPS_REGEX.sub('', v) # strip any spaces in uids
                    text = myutils.GAPS_REGEX.sub(' ', v) # normalise any internal space
                    v = text.strip() # strip leading and trailing space
                elif k == 'url' or k.endswith('_url'):
                    text = myutils.GAPS_REGEX.sub('', v) # strip any spaces in urls
                    v = scrapeutils.JSESS_REGEX.sub('', text) # strip any jsessionid parameter
                elif k.endswith('_date') or k.startswith('date_'):
                    dt = myutils.get_dt(v, self._response_date_format)
                    if not dt:
                        v = None
                    else:
                        v = dt.isoformat()
                        if v <= '1970-01-01': # special processing for bad dates inserted where "N/A" appears on screen
                            v = None
                else:
                    text = scrapeutils.TAGS_REGEX.sub(' ', v) # replace any html tag content with spaces
                    #try:
                    text = BeautifulSoup(text, convertEntities="html").contents[0].string
                    # use beautiful soup to convert html entities to unicode strings
                    #except:
                    #    pass
                    text = myutils.GAPS_REGEX.sub(' ', text) # normalise any internal space
                    v = text.strip() # strip leading and trailing space
            if not v: # delete entry if the final value is empty
                del record[k]
            else:
                record[k] = v
                #self.logger.debug("Cleaned record: %s", record)

