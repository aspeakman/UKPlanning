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
from datetime import timedelta, date, datetime
import weakref
from BeautifulSoup import BeautifulSoup
import lxml
try:
    from ukplanning import scrapeutils
except ImportError:
    import scrapeutils
try:
    from ukplanning import scrapemark
except ImportError:
    import scrapemark
try:
    from ukplanning import myutils
except ImportError:
    import myutils
import logging
import requests
import os
import mechanize
try:
    from ukplanning import geo
except ImportError:
    import geo
import urlparse

class BaseScraper(object): # scraper template class to be subclassed by all children

    # default read only class variables for all scrapers
    __instance = None # holds a weak reference to the one possible instance of this class
    _log_directory = 'logs'
    _disabled = False # set to True if this class should not be found or activated
    _comment = None
    _test_class = 'BaseScraperTest' # defines class used for testing this scraper
    _authority_name = None
    _headers = None
    _proxy = ''
    _request_date_format = '%d/%m/%Y'
    _response_date_format = None
    _scrape_data_block = None # scrapemark config to capture HTML block encompassing all fields to be gathered
    _scrape_min_data = None # scrapemark config to get the minimum acceptable valid dataset on an application page
    _scrape_optional_data = [] # list of scrapemark configs to get other optional parameters that can appear on an application page
    _scrape_invalid_format = None # scrapemark config to signal the returned page is not a valid application record
    _min_fields = [ 'reference', 'address', 'description' ] # min fields list used in testing only
    _logfile = None
    _search_url = None
    _detail_page = None
    _base_type = None
    _scraper_type = None
    _default_log_level = logging.INFO
    _default_timeout = 20
    _handler = '' # mechanize default handler - other options are 'etree' and 'soup'
    _cookies = None
    _uid_only = False # by default assume applications can be accessed via uid AND url (but some can only go via uid)
    _uid_num_sequence = False # uid by default is the local authority reference (but some can use a numeric sequence value)
    
    # default public class variables for all scrapers
    data_start_target = None # the earliest sequence value to work back to (date string or integer)
    min_id_goal = 600 # min target for application ids to fetch in one go
    logger = None
    batch_size = None # number of dates/sequences to ask for in successive requests to target web site
    current_span = None # overall number of dates/sequences requested if gathering the most recent or highest sequence
    url_first = True # by default tries to access applications from url if exists - then uid
    
    # scrape error codes when retrieving application details
    FETCH_FAIL = 'FETCH_FAIL'
    GET_ERROR = 'GET_ERROR'
    INVALID_FORMAT = 'INVALID_FORMAT'
    NO_DATA = 'NO_DATA'
    NO_DETAIL = 'NO_DETAIL'
    OTHER_ERROR = 'OTHER_ERROR'
    EMPTY = 'EMPTY'
    NO_UID = 'NO_UID'
    errors = {
        'FETCH_FAIL': "Failed to fetch scrape data - Http/URL error",
        'GET_ERROR': "Exception during data scrape",
        'INVALID_FORMAT': "Scraped data was a known invalid format", # means website is working but query failed
        'NO_DATA': "No data block found in scrape data",
        'NO_DETAIL': "Minimum detail not found in scrape data",
        'OTHER_ERROR': "Unknown scraper error",
        'EMPTY': "Empty details record returned",
        'NO_UID': "Record has no uid field",
    }
    
    @classmethod
    def create(cls, verbose=False, *args, **kwargs):
        if cls.__instance is None or not cls.__instance():
            obj = cls(*args, **kwargs)
            cls.__instance = weakref.ref(obj)
            return obj
        else:
            if verbose: print "Error: an instance of %s already exists" % cls.__name__
            return None
            
    @classmethod
    def destroy(cls, verbose=False):
        if cls.__instance is not None:
            obj = cls.__instance()
            cls.__instance = None
            if obj:
                obj = None
                return
        if verbose: print "Error: no instance of %s already exists" % cls.__name__

    @classmethod
    def instance(cls, verbose=False):
        if cls.__instance is not None:
            obj = cls.__instance()
            if obj:
                return obj
        if verbose: print "Error: no instance of %s already exists" % cls.__name__
        return None 
        
    """ alternative to the class methods defined above - enforces singleton via normal __init__
    def __new__(cls, *args, **kwargs): 
        # Check to see if a __instance exists already for this class
        # Compare class types instead of just looking for None so
        # that subclasses will create their own __instance objects
        if cls.__instance is None or cls != type(cls.__instance()):
            obj = object.__new__(cls, *args, **kwargs)
            cls.__instance = weakref.ref(obj)
            return obj
        else:
            return None"""

    def __init__(self, authority_name = None, 
        log_level = None, log_name = None, log_directory = None, timeout = None):
        if authority_name:
            self._authority_name = authority_name
        if not self._authority_name:
            raise ValueError("undefined authority name")
        if log_level is False: # NOTE if log_level is explicitly False, then logging is to root logger at default level
            self.logger = logging.getLogger('', level=self._default_log_level)
        else:
            if not log_level:
                log_level = self._default_log_level
            if not log_name:
                log_name = self._authority_name
            if not log_directory:
                log_directory = self._log_directory
            self._logfile = myutils.log_path(log_name, directory=log_directory)
            fh = myutils.frotate_handler(self._logfile)
            self.logger = myutils.setup_logger(self._authority_name, fh, level=log_level)
        self.logger.info("Instance of %s %s %s started" % (self._authority_name, ( self._scraper_type if self._scraper_type else 'Custom' ), self._base_type))
        if not timeout:
            timeout = self._default_timeout
        self.br, self.cj = scrapeutils.get_browser(self._headers, self._handler, self._proxy, float(timeout))
        if self._cookies:
            for ck in self._cookies:
                scrapeutils.set_cookie(self.cj, ck.get('name', ''), ck.get('value', ''), ck.get('domain'), ck.get('path', '/'))   
        self._timeout = self.br._timeout
        
    #def __del__(self):
    #    self.logger.info("Scraper dead") 
        
    # callable run function for all scrapers, gets the most recent ids from the scraper
    def __call__(self):
        return gather_ids() 
        
    def __str__(self):
        return self._authority_name
        
    @property
    def authority_name(self):
        ' Name of authority this scraper targets '
        return self._authority_name
        
    @property
    def search_url(self):
        ' URL for search interface to planning applications '
        return self._search_url
        
    @property
    def scraper_type(self):
        ' Generic type of this scraper '
        return self._scraper_type if self._scraper_type else 'Custom'
        
    @property
    def base_type(self):
        ' Base type of this scraper '
        return self._base_type
        
    @property
    def log_file(self):
        ' Path to the log file for this scraper '
        return self._logfile
        
    @property
    def max_sequence(self): # current max record sequence number = date/number
        return None
        
    def get_max_sequence(self): # callable version
        return self.max_sequence
        
    @property
    def min_sequence(self): # current min record sequence number = date/number
        return None
        
    @property
    def timeout(self): 
        return self._timeout
        
    @classmethod
    def can_run(cls):
        # override this in sub classes if there are times or conditions
        # when a scraper should not collect data - for example if not to be run overnight
        return True
        
    def gather_ids(self, sequence_from=None, sequence_to=None):
        """gathers a batch of IDs, template function to be implemented in the children
        if two parameters are supplied this is a request to gather backwards from 'to' towards 'from', returning the real range found
        if one parameter is supplied it's a request to gather forwards beyond 'from', returning the real range found
        if no parameters are supplied it tries to gather the most recent/ or highest sequence numbers known
        note always expects to gather some data - empty 'result' is an error
        supplied and returned sequence numbers are either integers or date objects"""
        return { 'from': None, 'to': None, 'result': [], 'scrape_error': self.errors[self.OTHER_ERROR] }
    
    def show_application(self, uid, url=None, make_abs=False):
        """gets display html for an application record from source using url or uid 
        result is a dict with a an 'html' page for display and a 'url' indicating the target if successful 
        otherwise the dict has a 'scrape_error' code  """
        page = None
        if self.url_first and not self._uid_only:
            if url:
                page = self._get_html_wrapper(url, 'url')
            if not page or 'scrape_error' in page:
                page = self._get_html_wrapper(uid, 'uid') 
        else:
            page = self._get_html_wrapper(uid, 'uid')
            if (not page or 'scrape_error' in page) and url:
                page = self._get_html_wrapper(url, 'url')
        if not page:
            self.logger.warning("Error getting html page from application: %s" % (self.EMPTY))
            return { 'scrape_error': self.errors[self.EMPTY] }
        elif 'scrape_error' in page: 
            return { 'scrape_error': page['scrape_error'] }
        else:
            if make_abs:
                doc = lxml.html.fromstring(page['html'])
                doc.make_links_absolute(page['url'])
                abs_html = lxml.etree.tostring(doc, pretty_print=True, method="html")
                page['html'] = abs_html
            return page
        
    def _get_html_wrapper(self, uidurl, param_type=None):
        ' wrapper to catch all errors related to html request failure '
        try:
            if param_type not in ['uid', 'url']:
                param_type = 'url'
            self.logger.debug("Trying to get html using %s %s" % (uidurl, param_type))
            if param_type == 'uid':
                html, url = self.get_html_from_uid(uidurl)
            else:
                html, url = self.get_html_from_url(uidurl)
            if not html:
                self.logger.warning("Error getting html using %s %s: %s" % (uidurl, param_type, self.errors[self.EMPTY]))
                return { 'scrape_error': self.errors[self.EMPTY] }
            else:
                return { 'html': html, 'url': url } 
        except (requests.exceptions.RequestException, mechanize.HTTPError, mechanize.URLError) as e:
            self.logger.warning("Error getting html using %s %s: %s: %s" % (uidurl, param_type, self.errors[self.FETCH_FAIL], str(e)))
            return { 'scrape_error': self.errors[self.FETCH_FAIL] }
        except Exception:
            self.logger.exception("Error getting html using %s %s: %s" % (uidurl, param_type, self.errors[self.GET_ERROR]))
            return { 'scrape_error': self.errors[self.GET_ERROR] } 
        
    def fetch_application(self, uid, url=None):
        """fetches an application record from source using url or uid 
        result is always a dict with a non-empty 'record' if successful 
        otherwise with a 'scrape_error' code  """
        applic = None
        if self.url_first and not self._uid_only:
            if url:
                applic = self._get_detail_wrapper(url, 'url')
            if not applic or 'scrape_error' in applic:
                applic = self._get_detail_wrapper(uid, 'uid')
        else:
            applic = self._get_detail_wrapper(uid, 'uid')
            if (not applic or 'scrape_error' in applic) and url:
                applic = self._get_detail_wrapper(url, 'url')
        if not applic:
            self.logger.warning("Error fetching application: %s" % (self.EMPTY))
            return { 'scrape_error': self.errors[self.EMPTY] }
        elif 'scrape_error' in applic: 
            return { 'scrape_error': applic['scrape_error'] }
        else:
            self._process_applic(applic)
            return { 'record': applic }
            
    def _process_applic(self, applic):
        """ post process an applic: set start_date, extract postcode/location (without external lookup)
        , add extra info inc datestamp, source details etc """
        pc = None
        if applic.get('postcode'):
            pc = myutils.extract_postcode(applic['postcode']) # note full postcodes only
        if not pc and applic.get('address'):
            pc = myutils.extract_postcode(applic['address']) # note full postcodes only
            if not pc and applic.get('applicant_address') and applic['applicant_address'].startswith(applic['address']):
                pc = myutils.extract_postcode(applic['applicant_address']) # see Cannock - no postcode in main address but in applicant address
        if pc:
            applic['postcode'] = pc
        lnglat = geo.lnglat_from_applic(applic)
        if lnglat:
            applic['lat'] = lnglat[1]
            applic['lng'] = lnglat[0]
        else:
            applic.pop('lat', '') # float lat/lng values only present if valid and derived from easting/northing or latitude/longitude fields
            applic.pop('lng', '')
        if applic.get('date_received') and applic.get('date_validated'):
            if applic['date_received'] < applic['date_validated']:
                applic['start_date'] = applic['date_received']
            else:
                applic['start_date'] = applic['date_validated']
        elif applic.get('date_received'):
            applic['start_date'] = applic['date_received']
        elif applic.get('date_validated'):
            applic['start_date'] = applic['date_validated']
        applic['date_scraped'] = datetime.now().isoformat()
        applic['authority'] = self.authority_name
        applic['source_url'] = self.search_url

    def update_application(self, applic):
        """updates an application record in place, preserving any existing fields which are not 
        returned from the remote source this time around
        result is always a dict with a non-empty 'record' if successful 
        otherwise with a 'scrape_error' code  """
        if not applic.get('uid'):
            return { 'scrape_error': self.errors[self.NO_UID] }
        result = self.fetch_application(applic['uid'], applic.get('url'))
        if result.get('record'):
            applic.update(result['record']) # this bit ensures any old data is preserved if there is nothing new
            return { 'record': applic }
        else:
            return result
            
    def _get_detail_wrapper(self, uidurl, param_type=None):
        ' wrapper to catch all errors related to scrape request failure '
        try:
            if param_type not in ['uid', 'url']:
                param_type = 'url'
            self.logger.debug("Trying to get detail using %s %s" % (uidurl, param_type))
            if param_type == 'uid':
                result = self.get_detail_from_uid(uidurl)
            else:
                result = self.get_detail_from_url(uidurl)
            if not result:
                self.logger.warning("Error getting detail using %s %s: %s" % (uidurl, param_type, self.errors[self.EMPTY]))
                return { 'scrape_error': self.errors[self.EMPTY] }
            elif 'scrape_error' in result: 
                self.logger.warning("Error getting detail using %s %s: %s" % (uidurl, param_type, result['scrape_error']))
                return { 'scrape_error': result['scrape_error'] }
            else:
                return result
        except (requests.exceptions.RequestException, mechanize.HTTPError, mechanize.URLError) as e:
            self.logger.warning("Error getting detail using %s %s: %s: %s" % (uidurl, param_type, self.errors[self.FETCH_FAIL], str(e)))
            return { 'scrape_error': self.errors[self.FETCH_FAIL] }
        except Exception:
            self.logger.exception("Error getting detail using %s %s: %s" % (uidurl, param_type, self.errors[self.GET_ERROR]))
            return { 'scrape_error': self.errors[self.GET_ERROR] } 
            
    def get_detail_from_uid(self, uid):
        """ Scrapes detailed information for one record given its UID
        returns a cleaned dict with application information if finds correctly configured data
        or a dict with a 'scrape_error' key if there is a problem
        NOTE does not set 'url' field c by default
        """
        html, url = self.get_html_from_uid(uid) 
        if html and url:
            if self._uid_only:
                return self._get_full_details(html, url, False) # NOTE does not not update the 'url' field
            else:
                return self._get_full_details(html, url, True) # updates the 'url' field from the page URL
        else:
            return None
        
    def get_detail_from_url(self, url):
        """ Scrapes detailed information for one record given its URL
        returns a cleaned dict with application information if finds correctly configured data
        or a dict with a 'scrape_error' key if there is a problem
        """
        html, url = self.get_html_from_url(url) 
        if html and url:
            return self._get_full_details(html, url, True) # updates the 'url' field from the page URL
        else:
            return None
        
    def get_html_from_uid(self, uid):
        """ Get the html and url for one record given its UID - to be implemented in sub-classes """
        return None, None
        
    def get_html_from_url(self, url):
        """ Get the html and url for one record given a URL """
        if self._uid_only:
            return None, None
        if self._search_url and self._detail_page:
            url_parts = urlparse.urlsplit(url)
            url = urlparse.urljoin(self._search_url, self._detail_page)
            if url_parts.query:
                url = url + '?' + url_parts.query
        response = self.br.open(url) # use mechanize, to get same handler interface as elsewhere
        return self._get_html(response)
        
    def _adjust_html(self, html):
        """ Hook to adjust application html if necessary before scraping """
        return html
        
    def _adjust_data_block(self, data_block):
        """ Hook to adjust application data_block if necessary before scraping """
        return data_block
        
    def _get_full_details(self, html, real_url, update_url=False):
        """ Return scraped record with optional update of base url using the website response """
        self.logger.debug("Real url: %s", real_url)
        result = self._get_details(html, real_url)
        if not update_url or not real_url or 'scrape_error' in result or result.get('url'):
            return result
        result['url'] = real_url # this is where the 'url' field is updated from page source - ie only if if successful
        return result
        
    def _get_details(self, html, this_url):
        """ Scrapes detailed information for one record given html and url 
        - this is an optional hook to allow e.g. data from multiple linked pages to be merged
        OR to interpolate a JSON decoder """
        return self._get_detail(html, this_url)
        
    def _get_html(self, response):
        """ Return HTML and URL given the website response """
        return response.read(), response.geturl()

    def _get_detail(self, html, url, data_block = None, min_data = None, optional_data = [], invalid_format = None):
        """ Scrapes detailed information for one record given its HTML and URL and scrapemark config strings
        returns a cleaned dict with application information if finds correctly configured data
        otherwise a dict with a 'scrape_error' key if there is a problem
        """
        scrape_data_block = data_block or self._scrape_data_block # use class defaults if none supplied
        scrape_min_data = min_data or self._scrape_min_data
        scrape_optional_data = optional_data or self._scrape_optional_data
        scrape_invalid_format = invalid_format or self._scrape_invalid_format
        html = self._adjust_html(html)
        #self.logger.debug("Html to scrape: %s", html)
        result = scrapemark.scrape(scrape_data_block, html, url)
        if result and result.get('block'):
            data_block = result['block']
            data_block = self._adjust_data_block(data_block)
            #self.logger.debug("Scraped data block: %s", data_block)
            result = scrapemark.scrape(scrape_min_data, data_block, url)
            if result:
                self.logger.debug("Scraped %d min data items", len(result))
                opt_count = 0
                for i in scrape_optional_data:
                    next_val = scrapemark.scrape(i, data_block, url)
                    if next_val:
                        result.update(next_val)
                        opt_count += 1
                if opt_count:
                    self.logger.debug("Scraped %d optional data items", opt_count)
                elif scrape_optional_data:
                    self.logger.warning("Scraped no optional data items")
                self._clean_record(result)
                return result
            elif scrape_invalid_format:
                result = scrapemark.scrape(scrape_invalid_format, data_block, url)
                if result:
                    return { 'scrape_error': self.errors[self.INVALID_FORMAT] } 
            return { 'scrape_error': self.errors[self.NO_DETAIL] }     
        return { 'scrape_error': self.errors[self.NO_DATA] }
        
    def _get_detail_json(self, json_dict, url, data_block = None, min_data = None, optional_data = [], invalid_format = None):
        """ Scrapes detailed information for one record given a JSON decoded dict and URL and mapping dicts
        returns a cleaned dict with application information if finds correctly configured data
        otherwise a dict with a 'scrape_error' key if there is a problem
        """
        scrape_data_block = data_block or self._scrape_data_block # use class defaults if none supplied
        scrape_min_data = min_data or self._scrape_min_data
        scrape_optional_data = optional_data or self._scrape_optional_data
        scrape_invalid_format = invalid_format or self._scrape_invalid_format
        #self.logger.debug("JSON to scrape: %s", str(json_dict))
        result = self._scrape_lookup(json_dict, scrape_data_block)
        if result:
            data_block = result
            #self.logger.debug("Scraped data block: %s", str(data_block))
            result = {}
            min_data_ok = True
            for k, v in scrape_min_data.items():
                next_val = self._scrape_lookup(data_block, v)
                if not next_val:
                    min_data_ok = False
                else:
                    if '{{' not in k:
                        result[k] = next_val
                    else:
                        next_val2 = scrapemark.scrape(k, next_val, url)
                        if not next_val2:
                            min_data_ok = False
                        else:
                            result.update(next_val2)
            if min_data_ok:
                self.logger.debug("Scraped %d min data items", len(result))
                opt_count = 0
                for k, v in scrape_optional_data.items():
                    next_val = self._scrape_lookup(data_block, v)
                    if next_val:
                        if '{{' not in k:
                            result[k] = next_val
                        else:
                            next_val2 = scrapemark.scrape(k, next_val, url)
                            if next_val2:
                                result.update(next_val2)
                        opt_count += 1
                if opt_count:
                    self.logger.debug("Scraped %d optional data items", opt_count)
                elif scrape_optional_data:
                    self.logger.warning("Scraped no optional data items")
                self._clean_record(result)
                return result
            elif scrape_invalid_format:
                result = self._scrape_lookup(json_dict, scrape_invalid_format)
                if result:
                    return { 'scrape_error': self.errors[self.INVALID_FORMAT] } 
            return { 'scrape_error': self.errors[self.NO_DETAIL] }     
        return { 'scrape_error': self.errors[self.NO_DATA] }
    
    def _scrape_lookup(self, json_dict, scrape_data):
        if not scrape_data:
            return json_dict
        elif isinstance(scrape_data, list):
            return myutils.dict_lookup(json_dict, *scrape_data)
        else:
            return myutils.dict_lookup(json_dict, scrape_data)
        
    def _clean_record(self, record):
        """ clean up a scraped record immediately after scraping
        parses dates, converts to ISO8601 format, strips spaces, tags etc """
        #self.logger.debug("Raw record to clean: %s", str(record))
        for k, v in record.items(): 
            if v:
                if isinstance(v, list):
                    v = ' '.join(v)
                if not v or not myutils.GAPS_REGEX.sub('', v): # always remove any empty fields
                    v = None
                elif k == 'uid':
                    v = myutils.GAPS_REGEX.sub('', v) # strip any spaces in uids
                elif k == 'url' or k.endswith('_url'):
                    text = myutils.GAPS_REGEX.sub('', v) # strip any spaces in urls
                    v = scrapeutils.JSESS_REGEX.sub('', text) # strip any jsessionid parameter
                elif k.endswith('_date') or k.startswith('date_'):
                    dt = myutils.get_dt(v, self._response_date_format)
                    if not dt:
                        v = None
                    else:
                        v = dt.isoformat()
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

    def _clean_ids(self, records):
        """ post process a batch of uid/url records: strips spaces in the uid etc - now uses _clean_record() """
        for record in records:
            self._clean_record(record)

class DateScraper(BaseScraper): # for those sites that can return applications between two arbitrary search dates 

    _test_class = 'DateScraperTest' # defines class used for testing this scraper
    _base_type = 'DateScraper'
    
    data_start_target = '2000-01-05' # gathers id data by working backwards from the current date towards this one
    batch_size = 14 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 14 # start this number of days ago when gathering current ids
    
    @property
    def max_sequence(self):
        """ returns current max record sequence number = current date in this case """
        return date.today()
        
    @property
    def min_sequence(self):
        """ returns current min record sequence number = 'data_start_target converted to date object """
        return myutils.get_dt(self.data_start_target)
        
    def gather_ids(self, sequence_from = None, sequence_to = None):
        """get successive date batches working through a date sequence
        if two parameters are supplied this is a request to gather backwards BELOW 'to' towards 'from', returning the real date range found
        if one parameter is supplied it's a request to gather forwards BEYOND 'from' towards today, returning the real date range found
        always expects to gather some data - empty 'result' is an error
        supplied and returned sequences are dates"""
        output = { 'from': None, 'to': None, 'result': [] }
        if not sequence_from: sequence_from = None
        if not sequence_to: sequence_to = None
        if not sequence_to: # gathering current dates - going forward
            move_forward = True
            target = self.max_sequence
            start = myutils.get_dt(sequence_from)
            if sequence_from is not None and start is None:
                raise ValueError("Non date supplied as sequence_from value")
            span = self.current_span
            remainder = span % self.batch_size
            if remainder: # current span should be a whole multiple of batch_size, so round up
                span = span + self.batch_size - remainder
            current_period_begins = target - timedelta(days=span)
            if not start or start > current_period_begins:
                start = current_period_begins
            start = start + timedelta(days=1) # always begin one day after supplied date
        else: # gathering early dates - going backward
            move_forward = False
            start = myutils.get_dt(sequence_to)
            if sequence_to is not None and start is None:
                raise ValueError("Non date supplied as sequence_to value")
            target = myutils.get_dt(sequence_from)
            if sequence_from is not None and target is None:
                raise ValueError("Non date supplied as sequence_from value")
            if not start or start > self.max_sequence:
                start = self.max_sequence
            if target and target >= start:
                raise ValueError("Sequence_from value should be less than sequence_to value")
            start = start - timedelta(days=1) # always begin one day before supplied date
            if not target or target < self.min_sequence:
                target = self.min_sequence
        current = start
        ok_current = start
        full_result = []
        while len(full_result) < self.min_id_goal and ((not move_forward and current >= target) or (move_forward and current <= target)): 
            if not move_forward:
                next = current - timedelta(days=self.batch_size-1)
                if next < self.min_sequence:
                    next = self.min_sequence
                result = self._get_id_batch_wrapper(next, current)
                if next > self.min_sequence and 'scrape_error' in result and result ['scrape_error'] == self.errors[self.NO_DATA]:
                    next = current - timedelta(days=(self.batch_size*2)-1) # try temp expanding the interval if no data found going backwards
                    if next < self.min_sequence:
                        next = self.min_sequence
                    result = self._get_id_batch_wrapper(next, current)
                    if 'scrape_error' in result and result ['scrape_error'] == self.errors[self.NO_DATA]:
                        next = current - timedelta(days=(int(self.batch_size/2))) # finally try temp contracting the interval if no data found going backwards
                        if next < self.min_sequence:
                            next = self.min_sequence
                        result = self._get_id_batch_wrapper(next, current)
            else:
                next = current + timedelta(days=self.batch_size-1)
                if next > self.max_sequence:
                    next = self.max_sequence
                result = self._get_id_batch_wrapper(current, next)
            if 'scrape_error' in result:
                if not full_result: # only exit with error condition if there are no previous complete batches without error
                    output ['scrape_error'] = result ['scrape_error']
                break
            else:
                self.logger.debug("%d ids gathered from %s to %s" % (len(result['result']), result['from'], result['to']))
                full_result.extend(result['result'])
                ok_current = next
                if not move_forward:
                    current = next - timedelta(days=1)
                else:
                    current = next + timedelta(days=1)
        for res in full_result:
            res['authority'] = self._authority_name
        output ['result'] = full_result
        if not move_forward:
            output ['from'] = ok_current
            output ['to'] = start
        else:
            if ok_current > self.max_sequence:
                ok_current = self.max_sequence
            output ['from'] = start
            output ['to'] = ok_current
        return output

    # wrapper to catch all errors from requests or mechanize related to http request failure
    # note dates here are real objects - so may need formatting
    def _get_id_batch_wrapper(self, date_from, date_to):
        try:
            result = self.get_id_batch(date_from, date_to)
            if result:
                for res in result:
                    if not res.get('uid'):
                        self.logger.warning("Error getting ids from %s to %s: %s" % (date_from, date_to, self.errors[self.NO_UID]))
                        return { 'scrape_error': self.errors[self.NO_UID] }
                return { 'result': result, 'from': date_from, 'to': date_to }
            else:
                self.logger.warning("Error getting ids from %s to %s: %s" % (date_from, date_to, self.errors[self.NO_DATA]))
                return { 'scrape_error': self.errors[self.NO_DATA] }
        except (requests.exceptions.RequestException, mechanize.HTTPError, mechanize.URLError) as e:
            self.logger.warning("Error getting ids from %s to %s: %s: %s" % (date_from, date_to, self.errors[self.FETCH_FAIL], str(e)))
            return { 'scrape_error': self.errors[self.FETCH_FAIL] }
        except Exception:
            self.logger.exception("Error getting ids from %s to %s: %s" % (date_from, date_to, self.errors[self.GET_ERROR]))
            return { 'scrape_error': self.errors[self.GET_ERROR] }
            
    # retrieves a batch of IDs betwen two sequence dates, to be implemented in the children
    # NB dates should be inclusive and are real date objects
    def get_id_batch(self, date_from, date_to):
        return [] # empty or None is an invalid result - means try again next time
        
# annual = Weymouth - now date scraper - see dorsetforyou
# monthly = Wokingham, Sedgemoor, Wychavon, Peak District
# 20 days = Gosport
# weekly = Kensington, Tower Hamlets, West Lothian, Colchester, Nottingham, Stevenage, Hastings, Copeland (PDFs), Swale (some PDFs), Isle of Man, Solihull, Exmoor
# weekly and monthly = Cotswold
class PeriodScraper(BaseScraper): # for those sites that return a fixed period of applications (weekly, monthly) around a search date

    _period_type = None
    #_period_type = 'Month' # calendar month including the specified date
    #_period_type = 'Saturday' # 7 day week ending on the specified day and including the supplied date
    #_period_type = '-Saturday' # 7 day week beginning on the specified day and including the supplied date
    #_period_type = '14' # 2 weeks beginning on the specified date
    #_period_type = '-14' # 2 weeks ending on the specified date
    _test_class = 'PeriodScraperTest' # defines class used for testing this scraper
    _base_type = 'PeriodScraper'
    
    data_start_target = '2000-01-05' # gathers id data by working backwards from the current date towards this one
    current_span = 14 # start this number of days ago when gathering current ids
    # note batch_size does not apply to period scrapers
    
    @property
    def max_sequence(self):
        """ returns current max record sequence number = current date in this case """
        return date.today()
        
    @property
    def min_sequence(self):
        """ returns current min record sequence number = 'data_start_target converted to date object """
        return myutils.get_dt(self.data_start_target)
        
    def gather_ids(self, sequence_from = None, sequence_to = None):
        """get successive date batches working through a date sequence
        if two parameters are supplied this is a request to gather backwards BELOW 'to' towards 'from', returning the real date range found
        if one parameter is supplied it's a request to gather forwards BEYOND 'from' towards today, returning the real date range found
        empty 'result' is not always an error, see below can be empty
        supplied and returned sequences are dates"""
        output = { 'from': None, 'to': None, 'result': [] }
        if not sequence_from: sequence_from = None
        if not sequence_to: sequence_to = None
        if not sequence_to: # gathering current dates - going forward
            move_forward = True
            target = self.max_sequence
            start = myutils.get_dt(sequence_from)
            if sequence_from is not None and start is None:
                raise ValueError("Non date supplied as sequence_from value")
            current_period_begins = target - timedelta(days=self.current_span)
            if not start or start > current_period_begins:
                start = current_period_begins
            start = start + timedelta(days=1) # always begin one day after supplied date
        else: # gathering early dates - going backward
            move_forward = False
            start = myutils.get_dt(sequence_to)
            if sequence_to is not None and start is None:
                raise ValueError("Non date supplied as sequence_to value")
            target = myutils.get_dt(sequence_from)
            if sequence_from is not None and target is None:
                raise ValueError("Non date supplied as sequence_from value")
            if not start or start > self.max_sequence:
                start = self.max_sequence
            if target and target >= start:
                raise ValueError("Sequence_from value should be less than sequence_to value")
            start = start - timedelta(days=1) # always begin one day before supplied date
            if not target or target < self.min_sequence:
                target = self.min_sequence
        current = start
        ok_current = start
        full_result = []
        while len(full_result) < self.min_id_goal and ((not move_forward and current > target) or (move_forward and current < target)): 
            result = self._get_id_period_wrapper(current)
            if 'scrape_error' in result:
                if not full_result: # only exit with error condition if there are no previous complete batches without error
                    output ['scrape_error'] = result ['scrape_error']
                break	   
            else:
                if result.get('result'):
                    self.logger.debug("%d ids gathered from %s to %s" % (len(result['result']), result['from'], result['to']))
                    full_result.extend(result['result'])
                else:
                    self.logger.warning("0 ids gathered from %s to %s" % (result['from'], result['to']))
                if not move_forward: 
                    ok_current = result['from']
                    current = result['from'] - timedelta(days=1)
                else:
                    ok_current = result['to']
                    current = result['to'] + timedelta(days=1)
        for res in full_result:
            res['authority'] = self._authority_name
        output ['result'] = full_result
        if not move_forward:
            output ['from'] = ok_current
            output ['to'] = start
        else:
            if ok_current > self.max_sequence:
                ok_current = self.max_sequence
            output ['from'] = start
            output ['to'] = ok_current
        return output
        
    # wrapper to catch all errors from requests or mechanize related to http request failure
    # note dates here are real objects - so may need formatting
    def _get_id_period_wrapper(self, date):
        try:
            result, from_dt, to_dt = self.get_id_period(date)
            if from_dt and to_dt:
                for res in result:
                    if not res.get('uid'):
                        self.logger.warning("Error getting ids from period around %s: %s" % (date, self.errors[self.NO_UID]))
                        return { 'scrape_error': self.errors[self.NO_UID] }
                return { 'result': result, 'from': from_dt, 'to': to_dt } # note result can be legitimately empty (if return dates are set)
            else:
                self.logger.warning("Error getting ids from period around %s: %s" % (date, self.errors[self.NO_DATA]))
                return { 'scrape_error': self.errors[self.NO_DATA] }
        except (requests.exceptions.RequestException, mechanize.HTTPError, mechanize.URLError) as e:
            self.logger.warning("Error getting ids from period around %s: %s: %s" % (date, self.errors[self.FETCH_FAIL], str(e)))
            return { 'scrape_error': self.errors[self.FETCH_FAIL] }
        except Exception:
            self.logger.exception("Error getting ids from period around %s: %s" % (date, self.errors[self.GET_ERROR]))
            return { 'scrape_error': self.errors[self.GET_ERROR] }
            
    # retrieves a batch of IDs around one date, to be implemented in the children
    # can return zero records if no data found for the requested period, but applicable (inclusive) dates must be returned
    # NB supplied and returned dates are real date objects
    def get_id_period(self, date):
        return [], None, None # invalid if return dates are not set - means try again next time

# YYYYNNNN (year + 4/5 digit sequence number) = Waverley, Rotherham, Ashfield, Jersey, Pembrokeshire Coast
# incrementing numeric ids = Isle of Wight, Scilly Isles, Purbeck, Hampshire, 
# fixed one page lists = Derbyshire, Northamptonshire, Planning Inspectorate
class ListScraper(BaseScraper): # for those sites that return a full paged list of all applications 

    _start_point = 1 # the default first scrape point if the scraper is empty (only required if max_sequence is not implemented)
    _test_class = 'ListScraperTest' # defines class used for testing this scraper
    _base_type = 'ListScraper'
    
    data_start_target = 1 # gathering back to this record number
    batch_size = 50 # batch size for each scrape - number of applications requested to produce at least one result each time
    current_span = 50 # min number of records to get when gathering current ids
    
    @property
    def min_sequence(self):
        """ returns current min record sequence number = 'data_start_target' as an integer in this case """
        return int(self.data_start_target)

    def gather_ids(self, sequence_from = None, sequence_to = None):
        """process id batches working through a numeric sequence (where the earliest record is nominally record number 1)
        if two parameters are supplied this is a request to gather backwards BELOW 'to' towards 'from', returning the real sequence range found
        if one parameter is supplied it's a request to gather forwards BEYOND 'from', returning the real sequence range found
        note 'from' is always smaller than 'to' 
        empty 'result' is not always an error see below
        supplied and returned sequences are integers not strings"""
        if sequence_from is not None:
            try:
                sequence_from = int(sequence_from)
            except ValueError:
                raise ValueError("Non integer supplied as sequence_from value")
        if sequence_to is not None:
            try:
                sequence_to = int(sequence_to)
            except ValueError:
                raise ValueError("Non integer supplied as sequence_to value")
        output = { 'from': None, 'to': None, 'result': [] }
        max_result = self._max_sequence_wrapper() # note access max_sequence prop once here (can be expensive to find)
        if 'scrape_error' in max_result:
            output ['scrape_error'] = max_result ['scrape_error']
            return output
        else:
            max_sequence = max_result['result']
        if not sequence_to: # gathering current sequence numbers - going forward
            move_forward = True
            if not sequence_from and self._start_point:
                start = self._start_point - 1
            else:
                start = sequence_from
            target = max_sequence
            span = self.current_span
            remainder = span % self.batch_size
            if remainder: # current span should be a whole multiple of batch_size, so round up
                span = span + self.batch_size - remainder
            current_period_begins = target - span
            if current_period_begins < 0:
                current_period_begins = 0 # sequence numbers can never be -ve
            if not start or start > current_period_begins:
                start = current_period_begins
            start = start + 1 # always begin one after any supplied sequence number
        else: # gathering early sequence numbers - going backward
            move_forward = False
            start = sequence_to
            target = sequence_from
            if not start or start > max_sequence:
                start = max_sequence
            if target and target >= start:
                raise ValueError("Sequence_from value should be less than sequence_to value")
            start = start - 1 # always begin one before any supplied sequence number
            if not target or target < self.min_sequence:
                target = self.min_sequence
        current = start
        ok_current = start
        full_result = []
        while len(full_result) < self.min_id_goal and ((not move_forward and current >= target) or (move_forward and current <= target)): 
            if not move_forward:
                next = current - self.batch_size + 1
                if next < self.min_sequence:
                    next = self.min_sequence
                result = self._get_id_records_wrapper(next, current, max_sequence)
                """if next > self.min_sequence and 'scrape_error' in result and result ['scrape_error'] == self.errors[self.NO_DATA]:
                    next = current - ((self.batch_size*2)-1) # try temp expanding the interval if no data found going backwards
                    if next < self.min_sequence:
                        next = self.min_sequence
                    result = self._get_id_records_wrapper(next, current, max_sequence)
                    if next > self.min_sequence and 'scrape_error' in result and result ['scrape_error'] == self.errors[self.NO_DATA]:
                        next = current - ((self.batch_size*4)-1) # try further expanding the interval if no data found going backwards
                        if next < self.min_sequence:
                            next = self.min_sequence
                        result = self._get_id_records_wrapper(next, current, max_sequence)"""
            else:
                next = current + self.batch_size - 1
                if next > max_sequence:
                    next = max_sequence
                result = self._get_id_records_wrapper(current, next, max_sequence)
            if 'scrape_error' in result:
                if not full_result:
                    if not move_forward or result['scrape_error'] <> self.errors[self.NO_DATA]: 
                        # Exit with error condition if there are no previous complete batches without error
                        # AND we are not moving forward in annual list scrapers by skipping non existent year end appplications
                        output ['scrape_error'] = result ['scrape_error']
                    else:
                        # moving forward and no data found - which is not an error here
                        # but must adjust returned start point to the state before it was incremented by 1
                        start = start - 1
                        ok_current = start
                break 
            else:
                if result.get('result'):
                    self.logger.debug("%d ids gathered from %s to %s" % (len(result['result']), result['from'], result['to']))
                    full_result.extend(result['result'])
                else:
                    self.logger.warning("0 ids gathered from %s to %s" % (result['from'], result['to']))
                if not move_forward:
                    ok_current = result['from']
                    current = result['from'] - 1
                else:
                    ok_current = result['to']
                    current = result['to'] + 1
        for res in full_result:
            res['authority'] = self._authority_name
        output ['result'] = full_result
        if not move_forward:
            output ['from'] = ok_current
            output ['to'] = start
        else:
            if ok_current > max_sequence:
                ok_current = max_sequence
            output ['from'] = start
            output ['to'] = ok_current
        return output
        
    # wrapper to catch all errors from requests or mechanize related to http request failure
    def _get_id_records_wrapper(self, from_rec, to_rec, max_recs):
        try:
            result, found_from, found_to = self.get_id_records(from_rec, to_rec, max_recs)
            if found_from and found_to:
                for res in result:
                    if not res.get('uid'):
                        self.logger.warning("Error getting ids from %d to %d: %s" % (from_rec, to_rec, self.errors[self.NO_UID]))
                        return { 'scrape_error': self.errors[self.NO_UID] }
                return { 'result': result, 'from': found_from, 'to': found_to } # note result can be legitimately empty (if return sequences are set)
            else:
                self.logger.warning("Error getting ids from %d to %d: %s" % (from_rec, to_rec, self.errors[self.NO_DATA]))
                return { 'scrape_error': self.errors[self.NO_DATA] }
        except (requests.exceptions.RequestException, mechanize.HTTPError, mechanize.URLError) as e:
            self.logger.warning("Error getting ids from %d to %d: %s: %s" % (from_rec, to_rec, self.errors[self.FETCH_FAIL], str(e)))
            return { 'scrape_error': self.errors[self.FETCH_FAIL] }
        except Exception:
            self.logger.exception("Error getting ids from %d to %d: %s" % (from_rec, to_rec, self.errors[self.GET_ERROR]))
            return { 'scrape_error': self.errors[self.GET_ERROR] }
            
    # wrapper to catch all errors from requests or mechanize related to http request failure
    def _max_sequence_wrapper(self):
        try:
            max_s = int(self.max_sequence)
            if max_s:
                return { 'result': max_s }
            else:
                self.logger.warning("Error getting max sequence value: %s" % (self.errors[self.NO_DATA]))
                return { 'scrape_error': self.errors[self.NO_DATA] }
        except (requests.exceptions.RequestException, mechanize.HTTPError, mechanize.URLError) as e:
            self.logger.warning("Error getting max sequence value: %s: %s" % (self.errors[self.FETCH_FAIL], str(e)))
            return { 'scrape_error': self.errors[self.FETCH_FAIL] }
        except Exception:
            self.logger.exception("Error getting max sequence value: %s" % (self.errors[self.GET_ERROR]))
            return { 'scrape_error': self.errors[self.GET_ERROR] }

    # retrieves records between two sequence numbers - to be defined in the children
    # can return zero records if no data found for the requested interval, but applicable (inclusive) sequences must be returned
    # supplied and returned sequence numbers are integers
    def get_id_records(self, from_rec, to_rec, max_recs):
        return [], None, None # invalid if return sequences are not set - means try again next time

