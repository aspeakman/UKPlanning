#!/usr/bin/env python
"""Copyright (C) 2013-2017  Andrew Speakman

This file is part of UKPlanning, a library of scrapers for UK planning applications

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>."""
import idox
from datetime import datetime

# note these are all Scottish Idox scrapers, but none now use the defunct IdoxScotsScraper class

"""class IdoxScotsScraper(idox.IdoxScraper):

    _date_from_field = 'dates(applicationReceivedStart)'
    _date_to_field = 'dates(applicationReceivedEnd)'
    _scrape_ids = ""
    <div id="searchresults">
    {* <div>
    <a href="{{ [records].url|abs }}" />
    <p> No: {{ [records].uid }} <span />
    </div> *}
    </div>
    ""
    _scrape_dates_link = '<a id="dates" href="{{ dates_link|abs }}" />'
    _scrape_info_link = '<a id="details" href="{{ info_link|abs }}" />'
    _detail_page = None"""
    
class AberdeenScraper(idox.IdoxScraper): 

    _search_url = 'https://publicaccess.aberdeencity.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Aberdeen'
    _comment = 'was Custom Scraper'
    detail_tests = [
        { 'uid': '121385', 'len': 20 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 42 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 4 } ]

class AberdeenshireScraper(idox.IdoxScraper): 

    data_start_target = '2001-11-03'
    min_id_goal = 150 # min target for application ids to fetch in one go
    batch_size = 21 # batch size for each scrape - number of days to gather to produce at least one result each time
    
    _search_url = 'https://upa.aberdeenshire.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Aberdeenshire'
    detail_tests = [
        { 'uid': 'APP/2012/3106', 'len': 25 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 84 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 19 } ]
        
class AngusScraper(idox.IdoxScraper): 

    _search_url = 'https://planning.angus.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Angus'
    detail_tests = [
        { 'uid': '12/00865/FULL', 'len': 30 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 24 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 4 } ]
        
class ArgyllScraper(idox.IdoxScraper):
    
    _search_url = 'http://publicaccess.argyll-bute.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Argyll'
    detail_tests = [
        { 'uid': '12/01733/PP', 'len': 31 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 51 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 6 } ]
        
class CairngormsScraper(idox.IdoxScraper):

    data_start_target = '2003-09-01'
    batch_size = 28 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 28 # start this number of days ago when gathering current ids
    
    _search_url = 'http://www.eplanningcnpa.co.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Cairngorms'
    detail_tests = [
        { 'uid': '2012/0297/DET', 'len': 27 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 7 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ]
        
# Clackmannan - see idoxreq
        
class DumfriesScraper(idox.IdoxScraper):

    _search_url = 'https://eaccess.dumgal.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Dumfries'
    detail_tests = [
        { 'uid': '11/P/3/0348', 'len': 24 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 40 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 }  ]

class DundeeScraper(idox.IdoxScraper): 

    _search_url = 'http://idoxwam.dundeecity.gov.uk/idoxpa-web/search.do?action=advanced'
    _authority_name = 'Dundee'
    detail_tests = [
        { 'uid': '12/00455/FULL', 'len': 29 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 14 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 }  ]
    
class EastAyrshireScraper(idox.IdoxScraper):

    _search_url = 'http://eplanning.east-ayrshire.gov.uk/online/search.do?action=advanced'
    _authority_name = 'EastAyrshire'
    detail_tests = [
        { 'uid': '11/0689/AD', 'len': 27 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 17 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 7 }   ]
    
class EastDunbartonshireScraper(idox.IdoxScraper):

    _search_url = 'http://planning.eastdunbarton.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'EastDunbartonshire'
    detail_tests = [
        { 'uid': 'TP/ED/11/0754', 'len': 29 }    ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 17 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 }  ]

# EastLothian - see idoxcrumb

class EastRenfrewshireScraper(idox.IdoxScraper):

    _search_url = 'https://ercbuildingstandards.eastrenfrewshire.gov.uk/buildingstandards/search.do?action=advanced'
    _authority_name = 'EastRenfrewshire'
    detail_tests = [
        { 'uid': '2011/0523/TP', 'len': 26 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 16 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 4 }  ]
    
class EdinburghScraper(idox.IdoxScraper):

    _search_url = 'https://citydev-portal.edinburgh.gov.uk/idoxpa-web/search.do?action=advanced'
    _authority_name = 'Edinburgh'
    detail_tests = [
        { 'uid': '11/02705/FUL', 'len': 27 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 57 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 23 }  ]
        
class FalkirkScraper(idox.IdoxScraper):

    _search_url = 'http://edevelopment.falkirk.gov.uk/online/search.do?action=advanced'
    _authority_name = 'Falkirk'
    detail_tests = [
        { 'uid': 'P/12/0430/FUL', 'len': 29 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 19 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 }  ]
    
class FifeScraper(idox.IdoxScraper):

    _search_url = 'http://planning.fife.gov.uk/online/search.do?action=advanced'
    _authority_name = 'Fife'
    detail_tests = [
        { 'uid': '12/02934/FULL', 'len': 20 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 73 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 10 }  ]
        
class GlasgowScraper(idox.IdoxScraper):

    _search_url = 'https://publicaccess.glasgow.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Glasgow'
    detail_tests = [
        { 'uid': '12/01874/DC', 'len': 20 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 52 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 9 }  ]
        
class HighlandScraper(idox.IdoxScraper):

    _search_url = 'http://wam.highland.gov.uk/wam/search.do?action=advanced'
    _authority_name = 'Highland'
    detail_tests = [
        { 'uid': '12/03092/FUL', 'len': 27 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 62 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 12 } ]
        
class InverclydeScraper(idox.IdoxScraper): # low numbers

    batch_size = 28 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 28 # start this number of days ago when gathering current ids
    _search_url = 'https://planning.inverclyde.gov.uk/Online/search.do?action=advanced'
    _authority_name = 'Inverclyde'
    detail_tests = [
        { 'uid': '11/0214/IC', 'len': 21 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 6 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]
        
class LochLomondScraper(idox.IdoxScraper):

    _search_url = 'http://eplanning.lochlomond-trossachs.org/OnlinePlanning/search.do?action=advanced'
    _authority_name = 'LochLomond'
    detail_tests = [
        { 'uid': '2012/0284/DET', 'len': 27 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 4 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]

class MidlothianScraper(idox.IdoxScraper):

    _search_url = 'https://planning-applications.midlothian.gov.uk/OnlinePlanning/search.do?action=advanced'
    _authority_name = 'Midlothian'
    detail_tests = [
        { 'uid': '11/00590/PNSP', 'len': 21 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 14 }, 
        { 'from': '15/08/2012', 'to': '15/08/2012', 'len': 5 }  ]
        
class MorayScraper(idox.IdoxScraper):

    _search_url = 'http://public.moray.gov.uk/eplanning/search.do?action=advanced'
    _authority_name = 'Moray'
    detail_tests = [
        { 'uid': '12/01240/APP', 'len': 25 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 9 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 1 }  ]

class NorthAyrshireScraper(idox.IdoxScraper):

    _search_url = 'http://www.eplanning.north-ayrshire.gov.uk/OnlinePlanning/search.do?action=advanced'
    _authority_name = 'NorthAyrshire'
    detail_tests = [
        { 'uid': '11/00581/PP', 'len': 26 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 12 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]
        
class NorthLanarkshireScraper(idox.IdoxScraper):

    _search_url = 'https://eplanning.northlanarkshire.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'NorthLanarkshire'
    detail_tests = [
        { 'uid': '11/00971/FUL', 'len': 23 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 13 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 }  ]
    
class OrkneyScraper(idox.IdoxScraper):

    data_start_target = '2005-01-05'
    batch_size = 28 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 28 # start this number of days ago when gathering current ids
    _search_url = 'http://planningandwarrant.orkney.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Orkney'
    detail_tests = [
        { 'uid': '11/439/PP', 'len': 21 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 9 }, 
        { 'from': '28/08/2012', 'to': '28/08/2012', 'len': 2 }  ]
        
class PerthScraper(idox.IdoxScraper):

    _search_url = 'http://planningapps.pkc.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Perth'
    detail_tests = [
        { 'uid': '12/01332/FLL', 'len': 24 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 40 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 13 }  ]

# Renfrewshire - see idoxendexc

class ScottishBordersScraper(idox.IdoxScraper):

    _search_url = 'https://eplanning.scotborders.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'ScottishBorders'
    detail_tests = [
        { 'uid': '12/00923/FUL', 'len': 25 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 33 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 6 }  ]

class ShetlandScraper(idox.IdoxScraper):

    batch_size = 21 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 21 # start this number of days ago when gathering current ids
    _search_url = 'http://pa.shetland.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Shetland'
    detail_tests = [
        { 'uid': '2012/309/PPF', 'len': 28 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 5 }, 
        { 'from': '28/08/2012', 'to': '28/08/2012', 'len': 2 }  ]

class SouthAyrshireScraper(idox.IdoxScraper): 

    _search_url = 'http://publicaccess.south-ayrshire.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'SouthAyrshire'
    detail_tests = [
        { 'uid': '11/01054/APP', 'len': 19 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 28 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 }  ]
        
class StirlingScraper(idox.IdoxScraper): 

    _search_url = 'http://pabs.stirling.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Stirling'
    detail_tests = [
        { 'uid': '12/00498/FUL', 'len': 29 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 15 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 }  ]
        
class WesternIslesScraper(idox.IdoxScraper): 

    _search_url = 'http://planning.cne-siar.gov.uk/PublicAccess/search.do?action=advanced'
    _authority_name = 'WesternIsles'
    detail_tests = [
        { 'uid': '12/00432/PPD', 'len': 33 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 11 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 }  ]

# WestLothian - see idoxendexc



