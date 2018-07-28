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
import urllib

# Note records are scraped from 11 separate paged district tables of all results
# each is given a page and record number (most recent first), which is an indication of sequence position BUT is not unique
# Note there is also a separate table (not used) of applications still open for consultation (OpenForConsultation=True)

# Error on this site when using python 2.7.6/mechanize/urllib2 interface
# <urlopen error [Errno 10054] An existing connection was forcibly closed by the remote host>
# This is because 2.7.6 does not include the TLSv1.2 SSL protocol suite which is the only one the site accepts
# see https://www.ssllabs.com/ssltest/analyze.html
# Solution is to upgrade to python 2.7.10 or greater
# Also see RibbleValley and Broadland
    
class HampshireScraper(base.ListScraper):

    data_start_target = 211 # gathering back to this record number
    min_id_goal = 220 # min target for application ids to fetch in one go
    batch_size = 110 # batch size for each scrape - number of applications requested to produce at least one result each time
    current_span = 110 # min number of records to get when gathering current ids
    
    _start_point = 3500 # default start if no other indication = see base.py
    _authority_name = 'Hampshire'
    _districts = [ 'TV', 'BA', 'HR', 'EH', 'WR', 'HV', 'FA', 'EA', 'NF', 'RM', 'GP' ]
    _d_maxrecs = {}
    _all_maxrecs = None
    _results_url = 'https://planning.hants.gov.uk/SearchResults.aspx'
    _search_url = 'https://planning.hants.gov.uk/'
    _applic_url = 'https://planning.hants.gov.uk/ApplicationDetails.aspx?AppNo='
    _disclaimer_url = 'https://planning.hants.gov.uk/Disclaimer.aspx?returnURL=%2f'
    _disclaimer_form = '1'
    _result_form = '1'
    _scrape_max_recs = '<div class="rdpWrap"> {{ max_recs }} search results returned </div>'
    _scrape_next_submit = '<input type="submit" name="{{ next_submit }}" title="Next" />'
    _scrape_ids = """
    <h2> Search Results </h2> <div id="ctl00_mainContentPlaceHolder_lvResults_topPager" /> <div>
    {*
        <table class="searchResult>
        <tr> <td> <strong> Application No: </strong>
        <a href="{{ [records].url|abs }}"> {{ [records].uid }} </td> </tr>
        </table>
    *}
    </div>
    """
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = """
    <table class="applicationDetails"> {{ block|html }} </table>
    """
    # the minimum acceptable valid dataset on an application page
    _scrape_min_data = """
    <td> Application no: </td> <td> {{ reference }} </td>
    <td> Location: </td> <td> {{ address }} </td>
    <td> Proposal: </td> <td> {{ description }} </td>
    <td> Received: </td> <td> {{ date_received }} </td>
    <td> Validated: </td> <td> {{ date_validated }} </td>
    """
    # other optional parameters that can appear on an application page
    _scrape_optional_data = [
    #'<td> Site Reference: </td> <td> {{ reference }} </td>', this is the site not the application
    '<td> Start of Public Consultation: </td> <td> {{ consultation_start_date }} </td>',
    '<td> Public Consultation Expiry: </td> <td> {{ consultation_end_date }} </td>',
    '<td> Status / decision: </td> <td> {{ status }} </td>',
    '<td> Decision: </td> <td> {{ decision }} </td> <td> Decision date: </td> <td> {{ decision_date }} </td>',
    '<td> Applicant </td> <td> {{ applicant_name }} </td>',
    '<td> Agent </td> <td> {{ agent_name }} </td>',
    """<td> Agent </td> <td> {{ agent_name }} </td>
    <td> Agent </td> <td> {{ agent_address|html }} </td>""", # nb for now ignore unicode apostrophe in agent's name
    """<td> Applicant </td> <td> {{ applicant_name }} </td>
    <td> Applicant </td> <td> {{ applicant_address|html }} </td>""", # nb for now ignore unicode apostrophe in agent's name
    '<td> Appeal status: </td> <td> {{ appeal_status }} </td>',
    '<td> Case Officer: </td> <td> {{ case_officer }} </td>',
    ]
    detail_tests = [
        { 'uid': 'HDC23999', 'len': 13 }, 
        { 'uid': '14/11530', 'len': 17 },  ]
    batch_tests = [ 
        { 'from': '3515', 'to': '3526', 'len': 12 }, ]

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
            
        response = self.br.open(self._disclaimer_url) 
        scrapeutils.setup_form(self.br, self._disclaimer_form)
        #self.logger.debug("Disclaimer form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        
        #page_zero = self._get_results_pages ('OpenForConsultation=True')
        #n_old = max_recs - len(page_zero)
        #print 'n_old', n_old
        #if current_result and from_rec > n_old:
        #    cfrom_rec = from_rec - n_old
        #    cto_rec = to_rec - n_old
        #    return current_result[cfrom_rec-1:cto_rec], from_rec, to_rec
        
        max_page, min_rec = self._find_max_pages(from_rec)
        
        #print 'mp', max_page, min_rec
        for d in self._districts:
            interim_result = self._get_results_pages ('District=' + d, max_page)
            if interim_result:
                #print d, len(interim_result)
                final_result.extend(interim_result)
            else:
                #print 'Empty'
                return [], None, None # list scraper - so individual empty result is also invalid
        
        if final_result:
            #print 'x', len(final_result)
            fret = sorted(final_result, key=lambda k: (k['pageno'], k['recno'], k['uid']), reverse=True)
            #self.logger.debug("From: %d To: %d" % (from_rec, to_rec))
            new_fret = fret[from_rec-min_rec:to_rec-min_rec+1]
            for f in new_fret:
                del f['pageno']; del f['recno']
            return new_fret, from_rec, to_rec
        else:
            return [], None, None # list scraper - so empty result is always invalid
            
    def _get_results_pages (self, result_param, final_page = None):
        # note returns dictionary of records (+ page number) keyed by uid
        final_result = []
        
        response = self.br.open(self._results_url + '?' + result_param) 
        html = response.read()
        #self.logger.debug("Batch html: %s" % html)
        
        try:
            result = scrapemark.scrape(self._scrape_max_recs, html)
            max_recs = int(result['max_recs'])
        except:
            max_recs = 0
            
        page_count = 0
        max_pages = (4 * self.min_id_goal / 10) + 20 # guard against infinite loop
        if not final_page:
            end_page = max_pages
        else:
            end_page = final_page
        while html and len(final_result) < max_recs and page_count < end_page:
            url = response.geturl()
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                page_count += 1
                self._clean_ids(result['records'])
                recno = 0
                for r in result['records']:
                    recno += 1
                    r['pageno'] = page_count
                    r['recno'] = recno
                final_result.extend(result['records'])
            else:
                self.logger.debug("Empty result after %d pages", page_count)
                break
            if len(final_result) >= max_recs: break
            try:
                result = scrapemark.scrape(self._scrape_next_submit, html, url)
                scrapeutils.setup_form(self.br, self._result_form)
                #self.logger.debug("Next form: %s", str(self.br.form))
                response = scrapeutils.submit_form(self.br, result['next_submit'])
                html = response.read()
            except: # note this should never happen as we know the max_recs value
                self.logger.error("No next button after %d pages", page_count)
                return []

        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - possible run away loop" % page_count)
            
        return final_result
    
    @property
    def max_sequence (self):
        response = self.br.open(self._disclaimer_url) 
        scrapeutils.setup_form(self.br, self._disclaimer_form, {} )
        #self.logger.debug("Disclaimer form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        self._d_maxrecs = {}
        self._all_maxrecs = None
        try:
            total = 0
            for d in self._districts:
                response = self.br.open(self._results_url + '?District=' + d) # one fixed page of records
                html = response.read()
                result = scrapemark.scrape(self._scrape_max_recs, html)
                intr = int(result['max_recs'])
                total += intr
                self._d_maxrecs[d] = intr
            #print 'max_recs', total
            self._all_maxrecs = total
            return total
        except:
            pass
        return None
        
    def n_on_page(self, page, district = None):
        # number of records from districts on each 'page'
        if not self._d_maxrecs:
            mx = self.max_sequence
        rmax = page * 10
        rmin = rmax - 9
        on_all_pages = 0
        for d, n in self._d_maxrecs.items():
            on_this_page = 0
            if rmin <= n and rmax > n: # on end page find remainder
                on_this_page = n % 10
            elif rmax <= n: # all other pages within range
                on_this_page = 10
            if district and d == district:
                return on_this_page
            on_all_pages += on_this_page
        return on_all_pages
        
    """def _last_page (self, district = None):
        # last page with records for each district
        if not self._d_maxrecs:
            mx = self.max_sequence
        last_page = 1
        for d, n in self._d_maxrecs.items():
            this_last_page = ((n - 1) / 10) + 1
            if district and d == district:
                return this_last_page
            if this_last_page > last_page:
                last_page = this_last_page
        return last_page"""
        
    def _find_max_pages(self, from_rec):
        # note from_rec determines the max number of pages that need scraping
        # if it is 1 = all pages; if it is max_recs = first page only
        if not self._all_maxrecs:
            mx = self.max_sequence
        max_recs = self._all_maxrecs
        if not max_recs or max_recs <= 0 or not from_rec or from_rec <= 0 or from_rec > max_recs:
            return None, None
        max_page = 0
        min_rec = max_recs + 1
        while min_rec > 1 and min_rec > from_rec:
            max_page += 1
            n_page = self.n_on_page(max_page)
            if not n_page: 
                max_page -= 1
                break
            min_rec = min_rec - n_page
        return max_page, min_rec
        
    """@property
    def current_max_sequence (self):
        response = self.br.open(self._disclaimer_url) 
        scrapeutils.setup_form(self.br, self._disclaimer_form)
        #self.logger.debug("Disclaimer form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        response = self.br.open(self._results_url + '?OpenForConsultation=True') 
        try:
            html = response.read()
            result = scrapemark.scrape(self._scrape_max_recs, html)
            return int(result['max_recs'])
        except:
            pass
        return None"""
        
    # post process a set of uid/url records: 
    def _clean_record(self, record):
        if record.get('uid'): # remove any uid items after the space ( = map link on some records)
            plist = record['uid'].split()
            if plist:
               record['uid'] = plist[0]
        if record.get('reference'): # remove any uid items after the space ( = map link on some records)
            plist = record['reference'].split()
            if plist:
               record['reference'] = plist[0]
        super(HampshireScraper, self)._clean_record(record) # do this after (strips spaces)
    
    def get_html_from_uid (self, uid): # works
        response = self.br.open(self._disclaimer_url) 
        scrapeutils.setup_form(self.br, self._disclaimer_form)
        #self.logger.debug("Disclaimer form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        #self.logger.debug("Start page: %s" % response.read())
        url = self._results_url + '?Criteria=' + urllib.quote_plus(uid)
        html, url = self.get_html_from_url(url)
        result = scrapemark.scrape(self._scrape_ids, html)
        if result and result.get('records'):
            self._clean_ids(result['records'])
            for r in result['records']:
                if r.get('uid', '') == uid and r.get('url'):
                    self.logger.debug("uid: %s, url: %s" % (r['uid'], r['url']))
                    return self.get_html_from_url(r['url'])
            return None, None
        else:
            return html, url


