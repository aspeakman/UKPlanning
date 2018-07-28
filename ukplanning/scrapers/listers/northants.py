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
from datetime import date, datetime
try:
    from ukplanning import myutils
except ImportError:
    import myutils
import re

class NorthamptonshireScraper(base.ListScraper):
    
    current_span = 10 # min number of records to get when gathering current ids

    _start_point = 1 # default start if no other indication = see base.py
    _authority_name = 'Northamptonshire'
    _comment = 'Current planning applications only - not historical'
    #_search_url = 'http://www.northamptonshire.gov.uk/en/councilservices/Environ/planning/planapps/Pages/currentapps_details.aspx'
    _search_url = 'http://www3.northamptonshire.gov.uk/councilservices/environment-and-planning/planning/planning-applications/current-planning-applications/Pages/default.aspx'
    _districts = [ 'Corby', 'Daventry', 'East Northamptonshire', 'Kettering', 'Northampton', 'South Northamptonshire', 'Wellingborough' ]
    _scrape_ids = """
    <h1> Current applications </h1> <div>
    {* <table> 
    <tr> Application Number {{ [records].uid }} </tr>
    <tr> <td> Location </td> <td> {{ [records].address|html }} </td> </tr>
    <tr> <td> Proposal </td> <td> {{ [records].description }} </td> </tr>
    <tr> <td> Case Officer </td> <td> {{ [records].case_officer }} </td> </tr>
    <tr> <td> Received </td> <td> {{ [records].date_received }} </td> </tr>
    <tr> <td> Valid </td> <td> {{ [records].date_validated }} </td> </tr>
    <tr> <td> Target for Decision </td> <td> {{ [records].target_decision_date }} </td> </tr>
    <tr> <td> Consultation Start </td> <td> {{ [records].consultation_start_date }} </td> </tr>
    <tr> <td> Consultation End </td> <td> {{ [records].consultation_end_date }} </td> </tr>
    <tr> <a href="{{ [records].url|abs }}" /> </tr>
    </table> *}
    </div>
    """
    batch_tests = [ 
        { 'from': '6', 'to': '13', 'len': 5 }, ]

    def get_id_records (self, request_from, request_to, max_recs):
        if not request_from or not request_to or not max_recs:
            return [], None, None # if any parameter invalid - try again next time
        final_result = []
        from_rec = int(request_from)
        to_rec = int(request_to)
        this_max = int(max_recs)
        if from_rec < 1:
            if to_rec < 1: # both too small
                return [], None, None
            from_rec = 1
        if to_rec > this_max:
            if from_rec > this_max: # both too large
                return [], None, None
            to_rec = this_max
            
        response = self.br.open(self._search_url) # one fixed page of records
        html = response.read()
        url = response.geturl()
        #self.logger.debug("ID batch page html: %s", html)
        
        for d in self._districts:
            response = self.br.follow_link(text=d)
            html = response.read()
            url = response.geturl()
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                for r in result['records']:
                    r['district'] = d
                self._clean_ids(result['records'])
                for r in result['records']:
                    r['address'] = re.sub(r'\([^\)]*\)\s*$', r'', r['address'], 0, re.U|re.I)
                final_result.extend(result['records'])
            self.br.back()
            
        for r in final_result:
            pc = None
            if r.get('address'):
                pc = myutils.extract_postcode(r['address']) # note full postcodes only
            if pc:
                r['postcode'] = pc
            try:
                dt = myutils.get_dt(r['date_received'])
                r['date_received'] = dt.isoformat()
            except:
                if r.get('date_received'):
                    del r['date_received'] # badly formatted dates are removed
            try:
                dt = myutils.get_dt(r['date_validated'])
                r['date_validated'] = dt.isoformat()
            except:
                if r.get('date_validated'):
                    del r['date_validated'] # badly formatted dates are removed
            if r.get('date_received') and r.get('date_validated'):
                if r['date_received'] < r['date_validated']:
                    r['start_date'] = r['date_received']
                else:
                    r['start_date'] = r['date_validated']
            elif r.get('date_received'):
                r['start_date'] = r['date_received']
            elif r.get('date_validated'):
                r['start_date'] = r['date_validated']
            r['date_scraped'] = datetime.now().isoformat()
            r['authority'] = self.authority_name
            r['source_url'] = self.search_url
        
        if final_result:
            fret = sorted(final_result, key=lambda k: k.get('start_date'))
            return fret[from_rec-1:to_rec], from_rec, to_rec
        else:
            return [], None, None # list scraper - so empty result is always invalid
        
    @property
    def max_sequence (self):
        response = self.br.open(self._search_url) 
        html = response.read()
        url = response.geturl()
        total = 0
        for d in self._districts:
            #print d
            response = self.br.follow_link(text=d)
            html = response.read()
            url = response.geturl()
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                #print len(result['records'])
                total += len(result['records'])
            self.br.back()
        return total if total else None
                       
    def get_html_from_url(self, url): # no scrape access at URL level
        return None, None
            

