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
from datetime import datetime, timedelta
try:
    from ukplanning import scrapeutils
except ImportError:
    import scrapeutils
try:
    from ukplanning import scrapemark
except ImportError:
    import scrapemark

class IdoxEndExcScraper(idox.IdoxScraper):

    def get_id_batch (self, date_from, date_to): # end date is exclusive, not inclusive
        new_date_to = date_to + timedelta(days=1) # increment end date by one day
        return super(IdoxEndExcScraper, self).get_id_batch(date_from, new_date_to)
        
"""class BaberghOldScraper(IdoxEndExcScraper): # now new combined service Babergh Mid Suffolk
    
    batch_size = 21 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 21 # start this number of days ago when gathering current ids

    _search_url = 'https://planning.babergh.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'BaberghOld'
    _comment = 'Was AcolNet up to Sep 2014'
    detail_tests = [
        { 'uid': 'B/12/01182', 'len': 31 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 16 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ]
        
    # note Babergh scraper fails silently (no return, no timeout) if run between 6pm and 6 30 am
    @classmethod
    def can_run(cls):
        now = datetime.now()
        if now.hour >= 17 or now.hour <= 6:
            return False
        else:
            return True"""
            
class BlackpoolScraper(IdoxEndExcScraper):

    _search_url = 'http://idoxpa.blackpool.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Blackpool'
    detail_tests = [
        { 'uid': '11/0773', 'len': 26 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 17 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 } ]
    
class BuryScraper(IdoxEndExcScraper):

    _search_url = 'https://planning.bury.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Bury'
    _comment = 'was AcolNet'
    detail_tests = [
        { 'uid': '55622', 'len': 31 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 21 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 } ]

class CanterburyScraper(IdoxEndExcScraper): 

    _search_url = 'https://publicaccess.canterbury.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Canterbury'
    _comment = 'was AcolNet'
    detail_tests = [
        { 'uid': 'CA//12/01582 ', 'len': 26 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 51 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 13 } ]

class CarlisleScraper(IdoxEndExcScraper): 

    _search_url = 'http://publicaccess.carlisle.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Carlisle'
    _comment = 'was AcolNet'
    detail_tests = [
        { 'uid': '13/0893', 'len': 21 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '01/12/2015', 'to': '14/12/2015', 'len': 41 }, 
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 12 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 7 } ]
        
    def get_id_batch (self, date_from, date_to):

        new_date_to = date_to + timedelta(days=1) # increment end date by one day
        final_result = []
        response = self.br.open(self._search_url)
        #self.logger.debug("ID batch start html: %s", response.read())
            
        fields = {}
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = new_date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        
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
                for res in result['records']:
                    if res.get('uid'): # one uid on 1 dec 2015 is empty
                        final_result.append(res)
            elif not final_result: # is it a single record?
                single_result = scrapemark.scrape(self._scrape_one_id, html, url)
                if single_result:
                    self._clean_record(single_result)
                    final_result = [ single_result ]
                    break
            else:
                self.logger.debug("Empty result after %d pages", page_count)
                break
            try:
                result = scrapemark.scrape(self._scrape_next_link, html, url)
                response = self.br.open(result['next_link'])
            except:
                self.logger.debug("No next link after %d pages", page_count)
                break
                
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
       
        return final_result
        
class CardiffScraper(IdoxEndExcScraper):

    _search_url = 'http://planning.cardiff.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Cardiff'
    detail_tests = [
        { 'uid': '11/01366/DCH', 'len': 25 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 49 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 7 }  ]

"""class CroydonOldScraper(IdoxEndExcScraper):

    _search_url = 'http://publicaccess.croydon.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'CroydonOld'
    _comment = 'was AcolNet, also public access 2 parallel site until 8 Nov 2016'
    detail_tests = [
        { 'uid': '11/01559/LE', 'len': 24 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 52 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 13 }  ]"""
        
class DacorumScraper(IdoxEndExcScraper): 

    _search_url = 'https://site.dacorum.gov.uk/publicaccess/search.do?action=advanced'
    _authority_name = 'Dacorum'
    detail_tests = [
        { 'uid': '4/01130/11/FUL', 'len': 31 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 43 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 14 } ]

class DerbyScraper(IdoxEndExcScraper): 

    _search_url = 'http://eplanning.derby.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Derby'
    _scrape_min_data = """
    <th> Reference </th> <td> {{ reference }} </td>
    <th> Location </th> <td> {{ address }} </td>
    <th> Proposal </th> <td> {{ description }} </td>
    """
    detail_tests = [
        { 'uid': '08/12/00973', 'len': 23 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 31 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 7 }  ]
    
class DoverScraper(IdoxEndExcScraper): 

    _search_url = 'https://planning.dover.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Dover'
    detail_tests = [
        { 'uid': '11/00702', 'len': 25 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 33 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 6 }  ]
    
class EastHampshireScraper(IdoxEndExcScraper):

    _search_url = 'http://planningpublicaccess.easthants.gov.uk/online-applications/search.do?action=advanced'
    _scrape_min_dates = "<th> Valid Date </th> <td> {{ date_validated }} </td>"
    _authority_name = 'EastHampshire'
    detail_tests = [
        { 'uid': '23971/016', 'len': 21 }    ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 14 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 9 }  ]

class EastLindseyScraper(IdoxEndExcScraper): 

    _search_url = 'http://publicaccess.e-lindsey.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'EastLindsey'
    detail_tests = [
        { 'uid': 'N/173/01470/11', 'len': 27 }    ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 16 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 4 }  ]
    
class FyldeScraper(IdoxEndExcScraper):

    _search_url = 'http://www3.fylde.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Fylde'
    detail_tests = [
        { 'uid': '11/0560', 'len': 32 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 18 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 4 }  ]

class GreenwichScraper(IdoxEndExcScraper):

    _search_url = 'https://planning.royalgreenwich.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Greenwich'
    _scrape_min_dates = """
    <th> Received </th> <td> {{ date_received }} </td>
    """
    _min_fields = [ 'reference', 'address', 'description', 'date_received', 'application_type' ]
    detail_tests = [
        { 'uid': '11/1768/F', 'len': 28 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 64 }, 
        { 'from': '15/08/2012', 'to': '15/08/2012', 'len': 14 }  ]
        
class GuildfordScraper(IdoxEndExcScraper): 

    _search_url = 'http://www2.guildford.gov.uk/publicaccess/search.do?action=advanced'
    _authority_name = 'Guildford'
    detail_tests = [
        { 'uid': '12/P/01264', 'len': 29 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 47 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 19 }  ]
    
class HastingsScraper(IdoxEndExcScraper): 

    _search_url = 'http://publicaccess.hastings.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Hastings'
    detail_tests = [
        { 'uid': 'HS/FA/11/00628', 'len': 26 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 12 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 }  ]
    
class HavantScraper(IdoxEndExcScraper): 

    _search_url = 'https://planningpublicaccess.havant.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Havant' 
    detail_tests = [
        { 'uid': 'APP/12/00747', 'len': 35 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 16 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 4 }  ]
    
class LewishamScraper(IdoxEndExcScraper):

    _search_url = 'http://planning.lewisham.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Lewisham'
    detail_tests = [
        { 'uid': 'DC/12/080873/FT', 'len': 25 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 60 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 18 } ]
        
class MedwayScraper(IdoxEndExcScraper): 

    _search_url = 'https://publicaccess.medway.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Medway'
    detail_tests = [
        { 'uid': 'MC/12/1745', 'len': 28 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 27 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 14 } ]
    
"""class MidSuffolkOldScraper(IdoxEndExcScraper):

    _search_url = 'http://planningpages.midsuffolk.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'MidSuffolkOld' 
    detail_tests = [
        { 'uid': '2705/11', 'len': 32 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 36 }, 
        { 'from': '15/08/2012', 'to': '15/08/2012', 'len': 2 }  ]"""
            
class NewForestScraper(IdoxEndExcScraper):

    _search_url = 'http://planning.newforest.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'NewForest'
    detail_tests = [
        { 'uid': '11/97541', 'len': 21 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 20 }, 
        { 'from': '15/08/2012', 'to': '15/08/2012', 'len': 3 }  ]
        
class NewForestParkScraper(IdoxEndExcScraper):

    _search_url = 'http://publicaccess.newforestnpa.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'NewForestPark'
    detail_tests = [
        { 'uid': '11/96734', 'len': 17 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 18 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 3 }  ]

class NorthHertfordshireScraper(IdoxEndExcScraper):

    _search_url = 'http://pa.north-herts.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'NorthHertfordshire'
    detail_tests = [
        { 'uid': '12/01827/1HH', 'len': 30 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 43 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 12 }  ]
    
class NorthNorfolkScraper(IdoxEndExcScraper):

    _search_url = 'https://idoxpa.north-norfolk.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'NorthNorfolk'
    detail_tests = [
        { 'uid': 'PF/12/0916', 'len': 25 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 31 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 }  ]
        
class OldhamScraper(IdoxEndExcScraper):

    _search_url = 'http://planningpa.oldham.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Oldham'
    detail_tests = [
        { 'uid': 'PA/331003/11', 'len': 29 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 25 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 }  ]
           
class PooleScraper(IdoxEndExcScraper):

    _search_url = 'https://boppa.poole.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Poole'
    detail_tests = [
        { 'uid': 'APP/11/01050/F', 'len': 25 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 40 }, 
        { 'from': '28/08/2012', 'to': '28/08/2012', 'len': 8 }  ]

class RenfrewshireScraper(IdoxEndExcScraper):

    _search_url = 'http://pl.renfrewshire.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Renfrewshire'
    detail_tests = [
        { 'uid': '12/0523/PP', 'len': 26 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 25 }, 
        { 'from': '15/08/2012', 'to': '15/08/2012', 'len': 3 }  ]

class RhonddaScraper(IdoxEndExcScraper):

    _search_url = 'http://planning.rctcbc.gov.uk/online-applications/search.do?action=advanced'
    _scrape_min_dates = "<th> Received </th> <td> {{ date_received }} </td>"
    _min_fields = [ 'reference', 'address', 'description', 'date_received', 'application_type' ]
    _authority_name = 'Rhondda'
    detail_tests = [
        { 'uid': '11/0969/10', 'len': 22 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 20 }, 
        { 'from': '28/08/2012', 'to': '28/08/2012', 'len': 6 }  ]

class SouthwarkScraper(IdoxEndExcScraper): 

    _search_url = 'http://planbuild.southwark.gov.uk:8190/online-applications/search.do?action=advanced'
    _authority_name = 'Southwark'
    detail_tests = [
        { 'uid': '12/AP/2125', 'len': 22 },
        ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 70 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 11 } ]

class StokeScraper(IdoxEndExcScraper): 

    _search_url = 'https://planning.stoke.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Stoke'
    detail_tests = [
        { 'uid': '53922/FUL', 'len': 30 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 32 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 4 } ]
           
class TowerHamletsScraper(IdoxEndExcScraper): 

    _search_url = 'https://development.towerhamlets.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'TowerHamlets'
    _comment = 'was WeeklyWAM up to end Sep 2015'
    detail_tests = [
        { 'uid': 'PA/11/02670', 'len': 20 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 43 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 7 } ]

class WarwickScraper(IdoxEndExcScraper):

    _search_url = 'http://planningdocuments.warwickdc.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Warwick' 
    detail_tests = [
        { 'uid': 'W/11/1024', 'len': 31 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 32 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 7 } ]
        
class WestLothianScraper(IdoxEndExcScraper):

    _search_url = 'https://planning.westlothian.gov.uk/publicaccess/search.do?action=advanced'
    _authority_name = 'WestLothian'
    _comment = 'was WeeklyWAM'
    detail_tests = [
        { 'uid': 'LIVE/0563/FUL/12', 'len': 21 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 6 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 }  ]
        


