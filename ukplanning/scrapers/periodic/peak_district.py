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

class PeakDistrictScraper(base.PeriodScraper):

    min_id_goal = 250 # min target for application ids to fetch in one go
    data_start_target = '2003-10-01'
    
    _authority_name = 'PeakDistrict'
    _period_type = 'Month'
    _request_date_format = '%m%y'
    _search_url = 'http://pam.peakdistrict.gov.uk/'
    _next_page_link = '>>'
    _scrape_ids = """
    <h3>Search results</h3>
    <table> <tr> Page: </tr> <tr> Reference </tr>
    {* <tr>
    <td> <a href="{{ [records].url|abs }}">
    {{ [records].uid }} </a> </td>
    </tr> *}
    <tr> Page: </tr> </table>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <div id="pamcontent"> {{ block|html }} </div>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <h2> Application Number: {{ reference }} </h2>
    <h3> Proposal:  {{ description }} </h3>
    <span> Development Address </span> {{ address }} <br />
    <span> Date Validated </span> {{ date_validated }} <br />
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    '<span> Application Status </span> {{ status }} <br>',
    '<span> Parish </span> {{ parish }} <br>',
    '<span> Decision </span> {{ decision }} <br>',
    '<p> <span> Planning Officer </span> {{ case_officer }} </p>',
    '<span> Applicant Name </span> {{ applicant_name }} <br>',
    '<p> <span> Applicant Address </span> {{ applicant_address }} </p>',
    '<span> Agent Name </span> {{ agent_name }} <br>',
    '<span> Agent Name </span> <span> Address </span> {{ agent_address }} <br>',
    '<span> Target Date for Decision </span> {{ target_decision_date }} <br>',
    '<p> <span> Decision Issued </span> {{ decision_date }} </p>',
    '<span> End of Public Consultation Period </span> {{ consultation_end_date }} <br>',
    ]
    detail_tests = [
        { 'uid': 'NP/DDD/0913/0818', 'len': 15 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'date': '13/09/2012', 'len': 92 }, 
        { 'date': '13/08/2012', 'len': 78 } ]

    def get_id_period (self, this_date):

        final_result = []
        from_dt, to_dt = scrapeutils.inc_dt(this_date, self._period_type)

        monyear = this_date.strftime(self._request_date_format) # 4 digit MMYY string
        response = self.br.open(self._search_url + '?q=' + monyear)

        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        while response and page_count < max_pages:
            html = response.read()
            url = response.geturl()
            #self.logger.debug("ID batch page html: %s", html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                page_count += 1
                new_result = []
                for rec in result['records']:
                    if '/' + monyear + '/' in rec['uid']: # filter out records where the search term does not appear in the correct part of the uid
                        new_result.append(rec)
                self._clean_ids(new_result)
                final_result.extend(new_result)
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
        
        if final_result:
            return final_result, from_dt, to_dt
        else:
            return [], None, None # monthly scraper - so empty result is always invalid

    def get_html_from_uid (self, uid):
        url = self._search_url + '?r='+ urllib.quote_plus(uid)
        return self.get_html_from_url(url)


