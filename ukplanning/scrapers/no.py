import base

# a list all the scrapers that cannot be implemented and reasons

class NoScraper(base.BaseScraper):
    
    _base_type = 'NoScraper'
    _scraper_type = 'None'
    _disabled = True
    _comment = 'No scraper - site has PDFs only'

class AlderneyScraper(NoScraper):

    _authority_name = 'Alderney'
    _search_url = 'http://www.alderney.gov.gg/article/103482/Planning-Applications'
    
class AngleseyScraper(NoScraper):

    _authority_name = 'Anglesey'
    _search_url = 'http://www.anglesey.gov.uk/planning-and-waste/planning-control/view-list-of-current-and-previous-planning-applications/'
    
class BlaenauGwentScraper(NoScraper):

    _authority_name = 'BlaenauGwent'
    _search_url = 'http://www.blaenau-gwent.gov.uk/resident/planning/recent-applications/'
    
class CopelandScraper(NoScraper):

    _authority_name = 'Copeland'
    _search_url = 'http://www.copeland.gov.uk/content/search-and-comment-planning-application'

class EastleighScraper(NoScraper):

    _authority_name = 'Eastleigh'
    _search_url = 'https://planning.eastleigh.gov.uk/s/public-register'
    _comment = 'Was Fastweb - no scraper now - new site has complicated hidden JSON/Javascript implementation'

class SarkScraper(NoScraper):

    _authority_name = 'Sark'
    _search_url = 'http://www.gov.sark.gg/public_notices.html'

        

