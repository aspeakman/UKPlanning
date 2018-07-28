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
import urllib, urlparse
from datetime import date

# base list scraper for sites that scrape the sequence of application
# uids with YYYY NNNN type information in them

# see Rotherham, Waverley, North Somerset, Dartmoor, Jersey, Stroud, Broxtowe, North Lincs

class AnnualListScraper(base.ListScraper):

    min_id_goal = 200 # min target for application ids to fetch in one go
    current_span = 30 # min number of records to get when gathering current ids
    data_start_target = 20000001
    
    _disabled = True
    _scraper_type = 'AnnualList'
    _max_index = 1000 # maximum records per year
    _index_digits = 4 # digits in sequence for index value
    _start_point = (date.today().year * 10000) + 1 # default start if no other indication = see base.py
    _scrape_invalid_format = None
    _scrape_invalid_format2 = None
    
    def get_id_records (self, request_from, request_to, max_recs):
        if not request_from or not request_to or not max_recs:
            return [], None, None # if any parameter invalid - try again next time
        from_rec = int(request_from)
        to_rec = int(request_to)
        num_recs = int(max_recs)
        # print from_rec, to_rec
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
        # print n # OK
        if self.over_sequence(to_rec): # at max sequence and gathering forward
            ii, yy, from_rec = self.split_sequence(from_rec, True)
        else: 
            ii, yy, from_rec = self.split_sequence(from_rec, False)
        to_rec = from_rec + n - 1
        in_current_year = False
        this_year = date.today().year
        # print 'Gathering forward from', from_rec, 'to', to_rec
        for i in range(from_rec, to_rec + 1):
            index, year, new_seq = self.split_sequence(i)
            if year == this_year and index > 0:
                in_current_year = True
            if rfrom is None:
                rfrom = i
            rto = new_seq
            uid =  self.get_uid(index, year)
            html, url = self.get_html_from_uid(uid)
            if not html:
                self.logger.debug("No html from uid %s" % uid)
                return [], None, None # no html to work on - something is wrong - exit
            result = scrapemark.scrape(self._scrape_min_data, html)
            if result and result.get('reference'):
                final_result.append( { 'url': url, 'uid': uid } )
            else:
                result = scrapemark.scrape(self._scrape_invalid_format, html)
                if result and result.get('invalid_format'):
                    self.logger.debug("No valid record for uid %s" % uid)
                else:
                    if self._scrape_invalid_format2:
                        result = scrapemark.scrape(self._scrape_invalid_format2, html)
                        if result and result.get('invalid_format'):
                            self.logger.debug("No valid record for uid %s" % uid)
                        else:
                            self.logger.error("Unrecognised record for uid %s: %s" % (uid, html))
                            return [], None, None # not recognised as bad data - something is wrong - exit
                    else:
                        self.logger.error("Unrecognised record for uid %s: %s" % (uid, html))
                        return [], None, None # not recognised as bad data - something is wrong - exit
            
        if not in_current_year or final_result:
            #print rfrom, rto
            return final_result, rfrom, rto
        else:
            return [], None, None # empty result is invalid if any of the results are in the current year

    def split_sequence(self, sequence, forward=True):
        # partition a sequence integer into an upper year and lower index e.g. 20059998
        # note the sequence value rolls over into the next year when going forwards and the index reaches _max_index
        # when going backward the index value rolls back into the preceding year at zero
        max_year = pow(10, self._index_digits)
        index = sequence % max_year
        year = int(sequence / max_year)
        if index >= self._max_index:
            if forward:
                year += int(index / self._max_index) 
                index = index % self._max_index
            else:
                year -= int((max_year - index) / self._max_index)
                index = self._max_index - ((max_year - index) % self._max_index)
        return index, year, (year * max_year) + index
    
    def over_sequence(self, sequence):
        max_year = pow(10, self._index_digits)
        index = sequence % max_year
        if index >= self._max_index:
            return True
        else:
            return False
        
    def get_uid(self, index, year):
        # create a uid from year and index integer values
        # to be implemented in the children
        return None
        
    # note max_sequence here is not exact
    @property
    def max_sequence (self):
        max_year = pow(10, self._index_digits)
        return (date.today().year * max_year) + self._max_index - 1
        #return self.max_in_year()
        
    def max_in_year (self, year=None): 
        if not year:
            year = date.today().year
        index = self._max_index - 1
        while index >= 0:
            uid =  self.get_uid(index, year)
            html, url = self.get_html_from_uid(uid)
            if html:
                result = scrapemark.scrape(self._scrape_min_data, html)
                if result and result.get('reference'):
                    # stop at this uid if there are application details
                    break
            index -= 1
        if index >= 0:
            max_year = pow(10, self._index_digits)
            return (max_year * year) + index
        else:
            return None
        


