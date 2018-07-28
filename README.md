UKPlanning
==========

**UKPlanning** provides Python scraper classes to access data from UK planning authority websites. 

Classes
=======

All scraper classes are derived from the BaseScraper and there is one class for each implemented UK planning authority. 
There are three sub-types of scraper, depending on how applications are made available on the authority website:

1. DateScraper - where the applications are fully searchable by date
2. PeriodScraper - where the applications are only accessible in date based batches (e.g. weekly, monthly)
3. ListScraper - where the website just has a sequence of applications received

The scrapers are based on [Mechanize](http://mechanize.readthedocs.io/) for browsing and form handling,
[scrapemark](http://arshaw.com/scrapemark/) for extracting data (using regular expressions). [lxml](http://lxml.de/) and
[BeautifulSoup](http://www.crummy.com/software/BeautifulSoup/) are also used in some cases to tidy up deficient HTML in the source.

There are some sites where the [Mechanize](http://mechanize.readthedocs.io/) package does not work and in those
cases, the scrapers are based on the [requests](http://docs.python-requests.org/en/master/) package. 
There are subclasses of the above 3 types (namely DateReqScraper, PeriodReqScraper and ListReqScraper)
to implement this. Note when using these subclasses there are no form handling capabilities or built in html tidying. 

For the current list of scraper classes, their types, location, status (disabled or not) see 'list.py' which produces 
a file called 'scraper_list.csv' containing the details.

Methods
=======

Each class object offers methods to undertake discovery of applications and then retrieve the details of each one:

Discovery
---------

```
gather_ids (from, to)
```

Universal method offered by the three scraper types to return a sequence of planning application identifiers (uids and urls). 
The supplied parameters (from, to) are either date objects (DateScraper, PeriodScraper) or integers (ListScraper). 

How it works:

* If the 'to' parameter is supplied this is a request to gather **backward** before 'to' towards 'from'. The result includes the real 'from' and 'to' values for the values returned (meaning that the result 'to' can be supplied directly to the next request to continue the sequence).
* If the 'to' parameter is not supplied it's a request to gather **forwards** beyond 'from'. The result includes the real 'from' and 'to' values for the values returned (meaning that the result 'from' can be supplied directly to the next request to continue the sequence).
* If no parameters are supplied it tries to gather the most recent or highest sequence numbers known. 

There are public class variables (with default values) which determine the values actually returned as follows:

* 'data_start_target' - earliest date/sequence value - backward scraping stops once this value is reached 
* 'batch_size' - number of dates/sequences to ask for in successive requests to the web site to produce at least one planning result each time (does not apply to PeriodScrapers)
* 'min_id_goal' - threshold minimum number of planning ids in the result after which scraping will normally be stopped 
* 'current_span' - the overall number of dates/sequences requested if gathering the most recent or highest sequence numbers (whole multiple of batch_size if applicable)

Examples: 

For a DateScraper run on 05/07/2017 with data_start_target='2000-01-01', batch_size=14, min_id_goal=1, current_span=28

* `gather_ids('2007-01-31')` would produce results from '2007-02-01' to '2007-02-14'
* `gather_ids('2000-01-01', '2007-01-31')` would produce results from '2007-01-17' to '2007-01-30'
* `gather_ids()` would produce results from '2007-06-08' to '2007-07-05'

The method result is a dictionary with 'from' and 'to' atributes, indicating the real range being returned. There will also be a 'result' 
attribute which holds the array of planning application dicts (each containing minimally 'url' and 'uid' fields). If there 
is an error then a 'scrape_error' field will be included with further detail in it.

Note an empty 'result' field returned by a DateScraper should always be treated as an error (not as a valid empty result). For PeriodScrapers and ListScrapers 
an empty 'result' field can be valid if there is no 'scrape_error' field and the returned 'from' and 'to' fields are
valid sequence values. 

Detail
------

```
update_application (applic)
```

Updates the supplied application dict from source using any existing 'uid' or optional 'url' fields in 'applic'. 
If successful the supplied dict is updated in place, and the result is a dict which will also contain a non-empty 'record' 
(the updated application). If there is an error, the result is also a dict, but with a 'scrape_error' string error message. 

```
fetch_application (uid, url)
```

Gets an application record from source using 'uid' or optional 'url' identifier parameters. The result is a dict with a 
non-empty 'record' if successful, or a 'scrape_error' string error message if not.

```
show_application (uid, url, make_abs)
```

Gets the main application page HTML using 'uid' or optional 'url' identifier parameters. The result is a dict with 'html' 
and 'url' attributes if successful, or a 'scrape_error' string error message if not. You can set the 'make_abs' parameter
to True if you want to update any relative URLs in the 'html' to an absolute form for re-display purposes.


Use
===

The scraper class methods 'fetch_application', 'gather_ids' and 'show_application'
can be run directly from the run.py module. 

An example to get the current planning ids from one planning authority:

> run.py Hart gather_ids > file.json

For help on this try:

> run.py -h

An example of how classes can be retrieved, instantiated and activated programmaticaly using the run module is as follows:

```python
#!/usr/bin/env python

from ukplanning import run

scraper = 'Hart'
scraper_dict = run.all_scraper_classes()
if not scraper in scraper_dict.keys():
    print 'Scraper class not yet implemented for %s' % scraper
else:
    print 'Found scraper class for %s' % scraper
    scraper_obj = run.get_scraper(scraper, log_directory='logs')
    print 'Wait ...'
    scraped = scraper_obj.gather_ids()
    if scraped.get('result'):
        result = scraped['result']
        print "Found %d applications from %s to %s" % (len(result), scraped['from'], scraped['to'])
        app = result[0]
        updated = scraper_obj.update_application(app)
        if 'scrape_error' not in updated:
            print 'Updated first full record from %s' % scraper
            print app
            print 'OK'
        else:
            print 'Error during application update: %s' % updated['scrape_error']
    else:
        print 'Error when gathering applications: %s' % scraped['scrape_error']
```

Logging
=======

By default each scraper will write progress logging information to a log file with the same name in the
current directory, or into a 'logs' sub-directory if it exists. There are *log_level*, *log_name*, and *log_directory*
options to the scraper class to customise logging.

Testing
=======

Tests can be accessed from the test.py module which can be run from the command line. An example to run the basic working tests for one planning authority:

> test.py -s Hart -g working

For further testing options:

> test.py -h

Note the tests are not strictly unit tests as they can fail if the target website changes (not just for internal reasons) as they depend on matching to expected 
numbers of records or fields scraped.
