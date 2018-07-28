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
import unittest
from datetime import timedelta
try:
    from ukplanning import myutils
except ImportError:
    import myutils
import logging

logger = logging.getLogger(__name__)

dummy_records = [
    {"authority": 'x', "uid": 'y',  "url": 'z', "date_scraped": '2000-01-01T12:00:00', "start_date": '2000-01-01'},
    {"authority": 'x', "uid": 'b',  "url": 'c', "date_scraped": '2000-01-01T12:00:01', "start_date": '2000-01-01'}
]

# Unit test classes for UK planning
# Note the _get_ and _gather_ tests are not strictly unit tests as they can fail if the target website changes (not just for internal reasons)
# as they depend on matching to expected numbers of records or fields scraped.

class BaseScraperTest(unittest.TestCase):
    
    test_groups = {
        'run': [],
        'working': ["test_get_detail"],
        'internal': ["test_get_applic"],
        'base': [ "test_clean_record", "test_process_applic" ]
    }
    
    def __init__(self, methodName='runTest', scraper_class=None, kwargs={}):
        super(BaseScraperTest, self).__init__(methodName)
        if not scraper_class:
            raise AttributeError("No scraper class supplied")
        self.scraper_class = scraper_class
        self.scraper_name = scraper_class._authority_name
        self.kwargs = kwargs
        
    def setUp(self):
        #self._scraper = run.get_scraper(self.scraper_name, **self.kwargs)
        self._scraper = self.scraper_class.create(**self.kwargs)

    def tearDown(self):
        self._scraper = None
        
    def test_setup(self):
        self.assertIsNotNone(self._scraper.br, 'No mechanize browser')
        
    def test_clean_record(self):
        cleaned = {
        'uid': ['  xxx  ', '   yyy  '],
        'url': '  http://   www.google.co.uk;jsessionid=12345?x=1&y=2    ',
        'bad_date': '  not a date    ',
        'good_date': '  23rd March 1980    ',
        'description': '  &amp; <div></div> &eacute; ',}
        self._scraper._clean_record(cleaned)
        self.assertEqual(cleaned['uid'], 'xxxyyy', '%s: Not cleaning uids' % self.scraper_name)
        self.assertEqual(cleaned['url'], 'http://www.google.co.uk?x=1&y=2', '%s: Not cleaning urls' % self.scraper_name)
        self.assertNotIn('bad_date', cleaned.keys(), '%s: Not removing bad dates' % self.scraper_name)
        self.assertEqual(cleaned['good_date'], '1980-03-23', '%s: Not parsing dates' % self.scraper_name)
        self.assertEqual(cleaned['description'], u'& ' + unichr(233), '%s: Not dealing with html markup' % self.scraper_name)
        
    def test_process_applic(self):
        applic = {
        'date_validated': '1980-03-04',
        'date_received': '1990-11-01',
        'address': 'abcdfgh n16        5Je    y92dfg',
        'easting': ' 11111111 ',
        'northing': '   18624311    '  # should end up with six digits 186243.11 -> Lat 51.501
        }
        self._scraper._process_applic(applic)
        self.assertEqual(applic['postcode'], 'N16 5JE', '%s: Not extracting postcodes' % self.scraper_name)
        self.assertEqual(applic['start_date'], '1980-03-04', '%s: Not setting start dates' % self.scraper_name)
        self.assertAlmostEqual(applic['lat'], 51.501, 3, '%s: Not extracting E/N vals with both > 6 digits' % self.scraper_name)
        #applic['easting'] = '  53405   '; applic['northing'] = '   11111    '  # should right pad to 534050 -> Lng -0.096
        #del applic['lat']; del applic['lng']
        #self._scraper._process_applic(applic)
        #self.assertAlmostEqual(applic['lng'], -0.096, 3, '%s: Not extracting E/N vals with both < 6 digits' % self.scraper_name)
        applic['easting'] = '  53405   '; applic['northing'] = '   111111    '  # should not pad == 053405 -> Lng -6.920
        del applic['lat']; del applic['lng']
        self._scraper._process_applic(applic)
        self.assertAlmostEqual(applic['lng'], -6.92, 3, '%s: Not extracting E/N vals with one < 6 digits' % self.scraper_name)
        
    def test_timeout(self):
        if hasattr (self._scraper, 'detail_tests') and self._scraper.detail_tests: 
            for test in self._scraper.detail_tests:
                self._scraper._timeout = 0.001
                self._scraper.br._timeout = 0.001
                result = self._scraper._get_detail_wrapper(test['uid'], 'uid')
                self.assertIn('scrape_error', result, '%s: No error result from scrape timeout' % (self.scraper_name))
                self._scraper._timeout = 30
                self._scraper.br._timeout = 30
                result = self._scraper._get_detail_wrapper(test['uid'], 'uid')
                self.assertNotIn('scrape_error', result, '%s: Error during scrape with 30s timeout: %s' % (self.scraper_name, result.get('scrape_error')))
                
    def test_get_detail(self):
        if hasattr (self._scraper, 'detail_tests') and self._scraper.detail_tests: 
            for test in self._scraper.detail_tests:
                result = self._scraper._get_detail_wrapper(test['uid'], 'uid')
                #print result
                self.assertNotIn('scrape_error', result, '%s: Error during scrape: %s' % (self.scraper_name, result.get('scrape_error')))
                self.assertTrue(result, '%s: Empty detail record' % self.scraper_name)
                if self._scraper._min_fields:
                    for f in self._scraper._min_fields:
                        self.assertIn(f, result, '%s: No %s field in detail record' % (self.scraper_name, f))
                else:
                    self.assertIn('reference', result, '%s: No reference field in detail record' % self.scraper_name)
                    self.assertIn('address', result, '%s: No address field in detail record' % self.scraper_name)
                    self.assertIn('description', result, '%s: No description field in detail record' % self.scraper_name)
                #print result
                if 'len' in test:
                    self.assertEqual(len(result), test['len'], 
                        '%s: Number of fields (%d) gathered from detail record %s does not match target (%d)' % 
                        (self.scraper_name, len(result), test['uid'], test['len']))
                    
    def test_get_applic(self):
        if hasattr (self._scraper, 'detail_tests') and self._scraper.detail_tests: 
            for test in self._scraper.detail_tests:
                result = self._scraper.fetch_application(uid=test['uid'])
                #print result
                self.assertNotIn('scrape_error', result, '%s: Error during scrape: %s' % (self.scraper_name, result.get('scrape_error')))
                self.assertIn('record', result, '%s: Empty result returned' % self.scraper_name)
                self.assertTrue(result['record'], '%s: Empty application record' % self.scraper_name)
                self.assertIn('start_date', result['record'], '%s: No start_date field in application record' % self.scraper_name)
                self.assertIn('date_scraped', result['record'], '%s: No date_scraped field in application record' % self.scraper_name)
                self.assertIn('authority', result['record'], '%s: No authority field in application record' % self.scraper_name)
                if 'len' in test: 
                    self.assertGreaterEqual(len(result['record']), test['len'] + 3, 
                        '%s: Number of fields (%d) gathered from application record %s is less than target (%d)' % 
                        (self.scraper_name, len(result['record']), test['uid'], test['len'] + 3))

class DateScraperTest(BaseScraperTest):
    
    test_groups = {
        'working': ["test_get_detail", "test_get_id_batch"],
        'internal': ["test_get_applic",
            "test_gather_ids_backward", "test_gather_ids_forward"],
        'base': [ "test_clean_record", "test_process_applic" ]
    }
    
    def test_get_id_batch(self):
        if hasattr (self._scraper, 'batch_tests') and self._scraper.batch_tests: 
            # the class can define its own test array
            test_list = self._scraper.batch_tests
        else: # otherwise do some default tests on a week in September 2012
            test_list = [ 
                { 'from': '13/09/2012', 'to': '19/09/2012' }, { 'from': '13/08/2012', 'to': '13/08/2012' }]
        for test in test_list:
            from_date = myutils.get_dt(test['from'])
            to_date = myutils.get_dt(test['to'])
            result_dic = self._scraper._get_id_batch_wrapper(from_date, to_date)
            self.assertNotIn('scrape_error', result_dic, '%s: Error during scrape: %s' % (self.scraper_name, result_dic.get('scrape_error')))
            result = result_dic['result']
            self.assertGreater(len(result), 0, '%s: No ids got from %s to %s' % (self.scraper_name, test['from'], test['to']))
            self.assertIn('uid', result[0].keys(), '%s: No uid field in first id record' % self.scraper_name)
            #self.assertIn('url', result[0].keys(), '%s: No url field in first id record' % self.scraper_name)
            if 'len' in test:
                self.assertEqual(len(result), test['len'], 
                    '%s: Number of ids (%d) got from %s to %s does not match target (%d)' % 
                    (self.scraper_name, len(result), test['from'], test['to'], test['len']))

    def test_gather_ids_backward(self):
        if hasattr (self._scraper, 'batch_tests') and self._scraper.batch_tests: 
            # the class can define its own test array
            test_list = self._scraper.batch_tests
        else: # otherwise do some default tests on a week in September 2012
            test_list = [ 
                { 'from': '13/09/2012', 'to': '19/09/2012' }, { 'from': '13/08/2012', 'to': '13/08/2012' }]
        for test in test_list: # moving backward
            from_date = myutils.get_dt(test['from'])
            to_date = myutils.get_dt(test['to']) + timedelta(days=1)
            self._scraper.batch_size = (to_date - from_date).days
            self._scraper.min_id_goal = 1 # low number so we only get 1 batch
            result_dic = self._scraper.gather_ids(from_date.isoformat(), to_date.isoformat())
            self.assertNotIn('scrape_error', result_dic, '%s: Error during scrape: %s' % (self.scraper_name, result_dic.get('scrape_error')))
            result = result_dic['result']
            self.assertGreater(len(result), 0, '%s: No ids gathered back from %s to %s' % (self.scraper_name, test['from'], test['to']))
            if 'len' in test:
                self.assertEqual(len(result), test['len'], 
                    '%s: Number of ids (%d) gathered back from %s to %s does not match target (%d)' % 
                    (self.scraper_name, len(result), test['from'], test['to'], test['len']))
            
    def test_gather_ids_forward(self):
        if hasattr (self._scraper, 'batch_tests') and self._scraper.batch_tests: 
            # the class can define its own test array
            test_list = self._scraper.batch_tests
        else: # otherwise do some default tests on a week in September 2012
            test_list = [ 
                { 'from': '13/09/2012', 'to': '19/09/2012' }, { 'from': '13/08/2012', 'to': '13/08/2012' }]
        for test in test_list: # moving forward
            from_date = myutils.get_dt(test['from']) - timedelta(days=1)
            to_date = myutils.get_dt(test['to'])
            self._scraper.batch_size = (to_date - from_date).days
            self._scraper.min_id_goal = 1 # low number so we only get 1 batch
            result_dic = self._scraper.gather_ids(from_date.isoformat(), None)
            self.assertNotIn('scrape_error', result_dic, '%s: Error during scrape: %s' % (self.scraper_name, result_dic.get('scrape_error')))
            result = result_dic['result']
            self.assertGreater(len(result), 0, '%s: No ids gathered forward from %s to %s' % (self.scraper_name, test['from'], test['to']))
            if 'len' in test:
                self.assertEqual(len(result), test['len'], 
                    '%s: Number of ids (%d) gathered forward from %s to %s does not match target (%d)' % 
                    (self.scraper_name, len(result), test['from'], test['to'], test['len']))

class PeriodScraperTest(BaseScraperTest):
    
    test_groups = {
        'working': ["test_get_detail", "test_get_id_period"],
        'internal': ["test_get_applic",
            "test_gather_ids_backward", "test_gather_ids_forward"],
        'base': [ "test_clean_record", "test_process_applic" ]
    }
    
    def test_get_id_period(self):
        if hasattr (self._scraper, 'batch_tests') and self._scraper.batch_tests: 
            # the class can define its own test array
            test_list = self._scraper.batch_tests
        else: # otherwise do some default tests on 2012 dates
            test_list = [ 
                { 'date': '15/09/2012' },  { 'date': '15/10/2012' },]
        for test in test_list:
            this_date = myutils.get_dt(test['date'])
            result_dic = self._scraper._get_id_period_wrapper(this_date)
            self.assertNotIn('scrape_error', result_dic, '%s: Error during scrape: %s' % (self.scraper_name, result_dic.get('scrape_error')))
            result = result_dic['result']
            #print result_dic
            self.assertGreater(len(result), 0, '%s: No ids got from %s ' % (self.scraper_name, test['date']))
            self.assertIn('uid', result[0].keys(), '%s: No uid field in first id record' % self.scraper_name)
            #self.assertIn('url', result[0].keys(), '%s: No url field in first id record' % self.scraper_name)
            if 'len' in test:
                self.assertEqual(len(result), test['len'], 
                    '%s: Number of ids (%d) got from %s does not match target (%d)' % 
                    (self.scraper_name, len(result), test['date'], test['len']))

class ListScraperTest(BaseScraperTest):
    
    test_groups = {
        'working': ["test_get_detail", "test_get_id_records"],
        'internal': ["test_get_applic",
            "test_gather_ids_backward", "test_gather_ids_forward"],
        'base': [ "test_clean_record", "test_process_applic" ]
    }
    
    def test_get_id_records(self):
        if hasattr (self._scraper, 'batch_tests') and self._scraper.batch_tests: 
            # the class can define its own test array
            test_list = self._scraper.batch_tests
        else: # otherwise do some default tests 
            test_list = [ 
                  { 'from': 600, 'to': 700 }, { 'from': 750, 'to': 751 }]
        for test in test_list:
            result_dic = self._scraper._get_id_records_wrapper(int(test['from']), int(test['to']), self._scraper.max_sequence)
            self.assertNotIn('scrape_error', result_dic, '%s: Error during scrape: %s' % (self.scraper_name, result_dic.get('scrape_error')))
            result = result_dic['result']
            self.assertGreater(len(result), 0, '%s: No ids got starting from %s to %s' % (self.scraper_name, test['from'], test['to']))
            self.assertIn('uid', result[0].keys(), '%s: No uid field in first id record' % self.scraper_name)
            #self.assertIn('url', result[0].keys(), '%s: No url field in first id record' % self.scraper_name)
            if 'len' in test:
                self.assertEqual(len(result), test['len'], 
                    '%s: Number of ids (%d) got from %s to %s does not match target (%d)' % 
                    (self.scraper_name, len(result), test['from'], test['to'], test['len']))

    def test_gather_ids_backward(self):
        if hasattr (self._scraper, 'batch_tests') and self._scraper.batch_tests: 
            # the class can define its own test array
            test_list = self._scraper.batch_tests
        else: # otherwise do some default tests on a week in September 2012
            test_list = [ 
                { 'from': 600, 'to': 700 }, { 'from': 750, 'to': 751 }]
        for test in test_list: # moving backward
            from_seq = int(test['from'])
            to_seq = int(test['to']) + 1
            self._scraper.batch_size = to_seq - from_seq
            self._scraper.min_id_goal = 1 # low number so we only get 1 batch
            result_dic = self._scraper.gather_ids(from_seq, to_seq)
            self.assertNotIn('scrape_error', result_dic, '%s: Error during scrape: %s' % (self.scraper_name, result_dic.get('scrape_error')))
            result = result_dic['result']
            self.assertGreater(len(result), 0, '%s: No ids gathered back from %s to %s' % (self.scraper_name, test['from'], test['to']))
            if 'len' in test:
                self.assertEqual(len(result), test['len'], 
                    '%s: Number of ids (%d) gathered back from %s to %s does not match target (%d)' % 
                    (self.scraper_name, len(result), test['from'], test['to'], test['len']))
            
    def test_gather_ids_forward(self):
        if hasattr (self._scraper, 'batch_tests') and self._scraper.batch_tests: 
            # the class can define its own test array
            test_list = self._scraper.batch_tests
        else: # otherwise do some default tests on a week in September 2012
            test_list = [ 
                { 'from': 600, 'to': 700 }, { 'from': 750, 'to': 751 }]
        for test in test_list: # moving forward
            from_seq = int(test['from']) - 1
            to_seq = int(test['to'])
            self._scraper.batch_size = to_seq - from_seq
            self._scraper.min_id_goal = 1 # low number so we only get 1 batch
            result_dic = self._scraper.gather_ids(from_seq, None)
            self.assertNotIn('scrape_error', result_dic, '%s: Error during scrape: %s' % (self.scraper_name, result_dic.get('scrape_error')))
            result = result_dic['result']
            self.assertGreater(len(result), 0, '%s: No ids gathered forward from %s to %s' % (self.scraper_name, test['from'], test['to']))
            if 'len' in test:
                self.assertEqual(len(result), test['len'], 
                    '%s: Number of ids (%d) gathered forward from %s to %s does not match target (%d)' % 
                    (self.scraper_name, len(result), test['from'], test['to'], test['len']))

    
if __name__ == '__main__':
    try: unittest.main()
    except SystemExit: pass
