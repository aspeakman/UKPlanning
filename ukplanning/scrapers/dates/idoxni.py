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
try:
    from ukplanning import scrapemark
except ImportError:
    import scrapemark
try:
    from ukplanning import scrapeutils
except ImportError:
    import scrapeutils
import idox

# note uses the new Idox Northern Ireland system active from September 2015

class IdoxNIScraper(idox.IdoxScraper):

    _search_url = 'http://epicpublic.planningni.gov.uk/publicaccess/search.do?action=advanced'
    _scraper_type = 'IdoxNI'
    _disabled = False
    
    def get_id_batch (self, date_from, date_to): 

        final_result = []
        
        for case in self._case_prefixes:
            
            interim_result = []
            response = self.br.open(self._search_url)
            #self.logger.debug("Start html: %s", response.read())
    
            fields = { self._ref_field: case }
            fields[self._date_from_field] = date_from.strftime(self._request_date_format)
            fields[self._date_to_field] = date_to.strftime(self._request_date_format)
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
                    interim_result.extend(result['records'])
                elif not interim_result: # is it a single record?
                    single_result = scrapemark.scrape(self._scrape_one_id, html, url)
                    if single_result:
                        self._clean_record(single_result)
                        interim_result = [ single_result ]
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
                
            final_result.extend(interim_result)
            
        return final_result
        
class AntrimNewtownabbeyScraper(IdoxNIScraper):

    _authority_name = 'AntrimNewtownabbey'
    #_search_fields =  { 'srchlgdcode': 'AN|Antrim and Newtownabbey' }
    #_search_fields =  { 'srchlgdcode': 'LGDANT|Antrim' }
    #_search_fields =  { 'srchlgdcode': 'LGDNEW|Newtownabbey' }
    _case_prefixes =  [ 'LA03', 'T/20', 'U/20' ]
    detail_tests = [
        { 'uid': 'LA03/2015/0009/F', 'len': 20 },
        { 'uid': 'T/2012/0278/F', 'len': 16 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/04/2015', 'to': '29/04/2015', 'len': 26 }, 
        { 'from': '08/04/2015', 'to': '08/04/2015', 'len': 2 },
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 18 }, # 7 + 11 
        { 'from': '16/08/2012', 'to': '16/08/2012', 'len': 5 } ] # 3 + 2

class ArdsNorthDownScraper(IdoxNIScraper):

    _authority_name = 'ArdsNorthDown'
    #_search_fields =  { 'srchlgdcode': 'NDA|Ards and North Down' }
    #_search_fields =  { 'srchlgdcode': 'LGDARD|Ards' }
    #_search_fields =  { 'srchlgdcode': 'LGDND|North Down' }
    _case_prefixes =  [ 'LA06', 'X/20', 'W/20' ]
    detail_tests = [
        { 'uid': 'LA06/2015/0113/F', 'len': 18 },
        { 'uid': 'X/2011/0544/F', 'len': 18 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/04/2015', 'to': '19/04/2015', 'len': 18 }, 
        { 'from': '08/04/2015', 'to': '08/04/2015', 'len': 10 },
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 24 }, # 16 + 8
        { 'from': '16/08/2012', 'to': '16/08/2012', 'len': 2 } ] # 2 + 0

class ArmaghBanbridgeCraigavonScraper(IdoxNIScraper):

    _authority_name = 'ArmaghBanbridgeCraigavon'
    #_search_fields =  { 'srchlgdcode': 'ABC|Armagh, Banbridge and Craigavon' }
    #_search_fields =  { 'srchlgdcode': 'LGDARM|Armagh' }
    #_search_fields =  { 'srchlgdcode': 'LGDBAN|Banbridge' }
    #_search_fields =  { 'srchlgdcode': 'LGDCRA|Craigavon' }
    _case_prefixes =  [ 'LA08', 'O/20', 'Q/20', 'N/20' ]
    detail_tests = [
        { 'uid': 'LA08/2015/0169/F', 'len': 18 }, 
        { 'uid': 'O/2011/0387/F', 'len': 20 },
        { 'uid': 'Q/2011/0387/F', 'len': 20 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/04/2015', 'to': '19/04/2015', 'len': 22 }, 
        { 'from': '09/04/2015', 'to': '09/04/2015', 'len': 6 },
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 27 }, # 16 + 3 + 8
        { 'from': '16/08/2012', 'to': '16/08/2012', 'len': 7 } ] # 2 + 1 + 4
        
class BelfastScraper(IdoxNIScraper):

    _authority_name = 'Belfast'
    #_search_fields =  { 'srchlgdcode': 'BEL|Belfast' }
    #_search_fields =  { 'caseNo': 'LA04' }
    #_search_fields =  { 'caseNo': 'Z/20' }
    _case_prefixes =  [ 'LA04', 'Z/20' ]
    detail_tests = [
        { 'uid': 'LA04/2015/0169/F', 'len': 17 }, 
        { 'uid': 'Z/2012/0861/F', 'len': 20 }, ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/04/2015', 'to': '19/04/2015', 'len': 26 }, 
        { 'from': '09/04/2015', 'to': '09/04/2015', 'len': 10 },
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 17 }, 
        { 'from': '16/08/2012', 'to': '16/08/2012', 'len': 2 } ] 

class CausewayGlensScraper(IdoxNIScraper):

    _authority_name = 'CausewayGlens'
    #_search_fields =  { 'srchlgdcode': 'CCG|Causeway Coast and Glens' }
    #_search_fields =  { 'srchlgdcode': 'LGDBMY|Ballymoney' }
    #_search_fields =  { 'srchlgdcode': 'LGDCOL|Coleraine' }
    #_search_fields =  { 'srchlgdcode': 'LGDLIM|Limavady' }
    #_search_fields =  { 'srchlgdcode': 'LGDMOY|Moyle' }
    _case_prefixes =  [ 'LA01', 'B/20', 'C/20', 'D/20', 'E/20' ]
    detail_tests = [
        { 'uid': 'LA01/2015/0169/F', 'len': 20 }, 
        { 'uid': 'C/2011/0387/F', 'len': 17 },
        { 'uid': 'D/2011/0287/F', 'len': 20 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/04/2015', 'to': '19/04/2015', 'len': 16 }, 
        { 'from': '09/04/2015', 'to': '09/04/2015', 'len': 2 },
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 30 }, # 2 + 12 + 10 + 6
        { 'from': '16/08/2012', 'to': '16/08/2012', 'len': 2 } ] # 0 + 1 + 0 + 1

class DerryStrabaneScraper(IdoxNIScraper): 

    _authority_name = 'DerryStrabane'
    #_search_fields =  { 'srchlgdcode': 'DS|Derry and Strabane' }
    #_search_fields =  { 'srchlgdcode': 'LGDDER|Derry' }
    #_search_fields =  { 'srchlgdcode': 'LGDSTR|Strabane' }
    _case_prefixes =  [ 'LA11', 'A/20', 'J/20' ]
    detail_tests = [
        { 'uid': 'LA11/2015/0169/F', 'len': 18 }, 
        { 'uid': 'A/2011/0285/F', 'len': 19 },
        { 'uid': 'J/2011/0135/F', 'len': 20 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/04/2015', 'to': '19/04/2015', 'len': 22 }, 
        { 'from': '08/04/2015', 'to': '08/04/2015', 'len': 6 },
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 18 }, # 12 + 6
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ] # 2 + 0

class FermanaghOmaghScraper(IdoxNIScraper): 

    _authority_name = 'FermanaghOmagh'
    #_search_fields =  { 'srchlgdcode': 'FOEN|Fermanagh and Omagh - Fermanagh' }
    #_search_fields =  { 'srchlgdcode': 'FOOMA|Fermanagh and Omagh - Omagh' }
    #_search_fields =  { 'srchlgdcode': 'LGDFER|Fermanagh' }
    #_search_fields =  { 'srchlgdcode': 'LGDOMA|Omagh' }
    _case_prefixes =  [ 'LA10', 'L/20', 'K/20' ]
    detail_tests = [
        { 'uid': 'LA10/2015/0169/F', 'len': 16 }, 
        { 'uid': 'L/2011/0185/F', 'len': 18 },
        { 'uid': 'K/2011/0185/F', 'len': 20 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/04/2015', 'to': '19/04/2015', 'len': 14 }, 
        { 'from': '08/04/2015', 'to': '08/04/2015', 'len': 6 },
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 20 }, # 12 + 8
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ] # 4 + 1

class LisburnCastlereaghScraper(IdoxNIScraper): 

    _authority_name = 'LisburnCastlereagh'
    #_search_fields =  { 'srchlgdcode': 'LC|Lisburn and Castlereagh' }
    #_search_fields =  { 'srchlgdcode': 'LGDCAS|Castlereagh' }
    #_search_fields =  { 'srchlgdcode': 'LGDLIS|Lisburn' }
    _case_prefixes =  [ 'LA05', 'S/20', 'Y/20' ]
    detail_tests = [
        { 'uid': 'LA05/2015/0169/F', 'len': 20 }, 
        { 'uid': 'S/2011/0285/F', 'len': 16 },
        { 'uid': 'Y/2011/0285/F', 'len': 18 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/04/2015', 'to': '19/04/2015', 'len': 25 }, 
        { 'from': '08/04/2015', 'to': '08/04/2015', 'len': 5 },
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 20 }, # 14 + 6
        { 'from': '16/08/2012', 'to': '16/08/2012', 'len': 2 } ] # 2 + 0

class MidEastAntrimScraper(IdoxNIScraper):

    _authority_name = 'MidEastAntrim'
    #_search_fields =  { 'srchlgdcode': 'MEA|Mid and East Antrim' }
    #_search_fields =  { 'srchlgdcode': 'LGDBMA|Ballymena' }
    #_search_fields =  { 'srchlgdcode': 'LGDCAR|Carrickfergus' }
    #_search_fields =  { 'srchlgdcode': 'LGDLAR|Larne' }
    _case_prefixes =  [ 'LA02', 'F/20', 'G/20', 'V/20' ]
    detail_tests = [
        { 'uid': 'LA02/2015/0414/F', 'len': 16 }, 
        { 'uid': 'G/2012/0178/F', 'len': 18 },
        { 'uid': 'V/2012/0178/F', 'len': 20 }, ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/04/2015', 'to': '19/04/2015', 'len': 18 }, 
        { 'from': '09/04/2015', 'to': '09/04/2015', 'len': 1 }, 
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 23 }, # 8 + 8 + 7
        { 'from': '16/08/2012', 'to': '16/08/2012', 'len': 4 } ] # 2 + 1 + 1

class MidUlsterScraper(IdoxNIScraper): 

    _authority_name = 'MidUlster'
    #_search_fields =  { 'srchlgdcode': 'MU|Mid Ulster' }
    #_search_fields =  { 'srchlgdcode': 'LGDCOO|Cookstown' }
    #_search_fields =  { 'srchlgdcode': 'LGDDUN|Dungannon' }
    #_search_fields =  { 'srchlgdcode': 'LGDMAG|Magherafelt' }
    _case_prefixes =  [ 'LA09', 'I/20', 'M/20', 'H/20' ]
    detail_tests = [
        { 'uid': 'LA09/2015/0414/F', 'len': 16 }, 
        { 'uid': 'I/2012/0278/F', 'len': 16 },
        { 'uid': 'M/2012/0397/F', 'len': 18 }, ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/04/2015', 'to': '19/04/2015', 'len': 15 }, 
        { 'from': '09/04/2015', 'to': '09/04/2015', 'len': 16 }, 
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 22 }, # 5 + 11 + 6
        { 'from': '16/08/2012', 'to': '16/08/2012', 'len': 3 } ] # 2 + 0 + 1

class NewryMourneDownScraper(IdoxNIScraper): 

    _authority_name = 'NewryMourneDown'
    #_search_fields =  { 'srchlgdcode': 'NMDDPT|Newry, Mourne and Down - Downpatrick' }
    #_search_fields =  { 'srchlgdcode': 'NMDNRY|Newry, Mourne and Down - Newry' }
    #_search_fields =  { 'srchlgdcode': 'LGDNM|Newry and Mourne' }
    #_search_fields =  { 'srchlgdcode': 'LGDDOW|Down' }
    _case_prefixes =  [ 'LA07', 'P/20', 'R/20' ]
    detail_tests = [
        { 'uid': 'LA07/2015/0414/F', 'len': 20 }, 
        { 'uid': 'P/2012/0582/F', 'len': 20 },
        { 'uid': 'R/2012/0363/F', 'len': 20 }, ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/04/2015', 'to': '19/04/2015', 'len': 27 }, # 10 + 17 
        { 'from': '09/04/2015', 'to': '09/04/2015', 'len': 8 }, # 2 + 6
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 30 }, # 17 + 13
        { 'from': '16/08/2012', 'to': '16/08/2012', 'len': 5 } ] # 3 + 2

"""class AntrimScraper(IdoxNIScraper): #T

    _authority_name = 'Antrim'
    _search_fields =  { 'srchlgdcode': 'LGDANT|Antrim' }
    detail_tests = [
        { 'uid': 'T/2012/0278/F', 'len': 24 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 7 }, 
        { 'from': '16/08/2012', 'to': '16/08/2012', 'len': 3 } ]
        
class ArdsScraper(IdoxNIScraper): # X

    _authority_name = 'Ards'
    _search_fields =  { 'srchlgdcode': 'LGDARD|Ards' }
    detail_tests = [
        { 'uid': 'X/2011/0544/F', 'len': 26 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 16 }, 
        { 'from': '16/08/2012', 'to': '16/08/2012', 'len': 2 } ]

class ArmaghScraper(IdoxNIScraper): # O

    _authority_name = 'Armagh'
    _search_fields =  { 'srchlgdcode': 'LGDARM|Armagh' }
    detail_tests = [
        { 'uid': 'O/2011/0387/F', 'len': 26 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 16 }, 
        { 'from': '16/08/2012', 'to': '16/08/2012', 'len': 2 } ]
        
class BallymenaScraper(IdoxNIScraper): # G

    _authority_name = 'Ballymena'
    #_search_fields =  { 'srchlgdcode': 'LGDBMA|Ballymena' }
    _search_fields =  { 'caseNo': 'G/20' }
    detail_tests = [
        { 'uid': 'G/2012/0375/F', 'len': 25 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 16 }, 
        { 'from': '16/08/2012', 'to': '16/08/2012', 'len': 2 } ]
        
class BallymoneyScraper(IdoxNIScraper): # D

    _authority_name = 'Ballymoney'
    _search_fields =  { 'srchlgdcode': 'LGDBMY|Ballymoney' }
    _search_fields =  { 'caseNo': 'D/20' }
    detail_tests = [
        { 'uid': 'D/2011/0387/F', 'len': 25 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 16 }, 
        { 'from': '16/08/2012', 'to': '16/08/2012', 'len': 2 } ]
        
# Banbridge = Q

class CarrickfergusScraper(IdoxNIScraper): # V

    _search_fields =  { 'srchlgdcode': 'LGDCAR|Carrickfergus' }

class CastlereaghScraper(IdoxNIScraper): # Y

    _search_fields =  { 'srchlgdcode': 'LGDCAS|Castlereagh' }

class ColeraineScraper(IdoxNIScraper): # C

    _search_fields =  { 'srchlgdcode': 'LGDCOL|Coleraine' }

class CookstownScraper(IdoxNIScraper): # I

    _search_fields =  { 'srchlgdcode': 'LGDCOO|Cookstown' }
    
# Craigavon = N

class DerryScraper(IdoxNIScraper): # A

    _search_fields =  { 'srchlgdcode': 'LGDDER|Derry' }

class DownScraper(IdoxNIScraper): # R = Downpatrick

    _search_fields =  { 'srchlgdcode': 'LGDDOW|Down' }

class DungannonScraper(IdoxNIScraper): # M

    _search_fields =  { 'srchlgdcode': 'LGDDUN|Dungannon' }

class FermanaghScraper(IdoxNIScraper): #L = Enniskillen

    _search_fields =  { 'srchlgdcode': 'LGDFER|Fermanagh' }

class LarneScraper(IdoxNIScraper): # F

    _search_fields =  { 'srchlgdcode': 'LGDLAR|Larne' }

class LimavadyScraper(IdoxNIScraper): # B

    _search_fields =  { 'srchlgdcode': 'LGDLIM|Limavady' }

class LisburnScraper(IdoxNIScraper): # S

    _search_fields =  { 'srchlgdcode': 'LGDLIS|Lisburn' }

class MagherafeltScraper(IdoxNIScraper): # H

    _search_fields =  { 'srchlgdcode': 'LGDMAG|Magherafelt' }

class MoyleScraper(IdoxNIScraper): # E

    _search_fields =  { 'srchlgdcode': 'LGDMOY|Moyle' }

class NewryAndMourneScraper(IdoxNIScraper): # P

    _search_fields =  { 'srchlgdcode': 'LGDNM|Newry and Mourne' }
    
# Newtownabbey = U
# North Down = W

class OmaghScraper(IdoxNIScraper): # K

    _search_fields =  { 'srchlgdcode': 'LGDOMA|Omagh' }

class StrabaneScraper(IdoxNIScraper): # J

    _search_fields =  { 'srchlgdcode': 'LGDSTR|Strabane' }"""


  


