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
import idox

# note these should all be plain English/Welsh Idox scrapers = no variants

class AylesburyValeScraper(idox.IdoxScraper): 

    _search_url = 'http://publicaccess.aylesburyvaledc.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'AylesburyVale'
    detail_tests = [
        { 'uid': '11/01736/APP', 'len': 30 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 45 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 8 } ]

class BaberghMidSuffolkScraper(idox.IdoxScraper): # tested
    
    _search_url = 'https://planning.baberghmidsuffolk.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'BaberghMidSuffolk'
    _comment = 'Combined planning service covering Babergh and Mid Suffolk'
    detail_tests = [
        { 'uid': 'B/12/01182', 'len': 26 },
        { 'uid': '2705/11', 'len': 29 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 52 }, # 16 + 36
        { 'from': '15/08/2012', 'to': '15/08/2012', 'len': 8 } ] # 6 + 2

class BarkingScraper(idox.IdoxScraper):

    _search_url = 'http://paplan.lbbd.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Barking'
    detail_tests = [
        { 'uid': '11/00728/FUL', 'len': 26 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 16 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ]

class BasildonScraper(idox.IdoxScraper): 

    _search_url = 'http://planning.basildon.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Basildon'
    detail_tests = [
        { 'uid': '12/00914/FULL', 'len': 32 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 13 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ]
        
class BassetlawScraper(idox.IdoxScraper):

    _search_url = 'http://publicaccess.bassetlaw.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Bassetlaw'
    detail_tests = [
        { 'uid': '12/01129/FUL', 'len': 33 } ] # to do
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 17 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 } ]

class BedfordScraper(idox.IdoxScraper):

    _search_url = 'http://www.publicaccess.bedford.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Bedford'
    detail_tests = [
        { 'uid': '11/01718/FUL', 'len': 31 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 47 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 8 } ]
        
class BlabyScraper(idox.IdoxScraper):

    _search_url = 'https://w3.blaby.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Blaby'
    detail_tests = [
        { 'uid': '12/0601/1/LX', 'len': 32 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 13 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 } ]
    
class BolsoverScraper(idox.IdoxScraper): 

    _search_url = 'http://planning.bolsover.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Bolsover'
    detail_tests = [
        { 'uid': '12/00352/FUL', 'len': 29 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 11 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 2 } ]
    
class BracknellScraper(idox.IdoxScraper):

    _search_url = 'https://planapp.bracknell-forest.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Bracknell'
    detail_tests = [
        { 'uid': '12/00588/FUL', 'len': 24 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 22 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 4 } ]
    
class BradfordScraper(idox.IdoxScraper):

    _search_url = 'https://planning.bradford.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Bradford'
    detail_tests = [
        { 'uid': '12/02946/FUL', 'len': 37 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 80 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 25 } ]
    
class BraintreeScraper(idox.IdoxScraper): 

    _search_url = 'https://publicaccess.braintree.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Braintree'
    detail_tests = [
        { 'uid': '12/01287/FUL', 'len': 23 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 43 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 6 } ]
    
class BrentwoodScraper(idox.IdoxScraper): 

    _search_url = 'http://publicaccess.brentwood.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Brentwood'
    detail_tests = [
        { 'uid': '12/00934/FUL', 'len': 27 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 34 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 6 } ]

class BristolScraper(idox.IdoxScraper):

    _search_url = 'http://planningonline.bristol.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Bristol'
    detail_tests = [
        { 'uid': '12/00935/H', 'len': 21 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 105 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 20 } ]
    
class BromleyScraper(idox.IdoxScraper): 

    _search_url = 'https://searchapplications.bromley.gov.uk/onlineapplications/search.do?action=advanced'
    _authority_name = 'Bromley'
    detail_tests = [
        { 'uid': '12/02973/FULL6', 'len': 31 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 93 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 21 }  ]

class BromsgroveRedditchScraper(idox.IdoxScraper):

    _search_url = 'https://publicaccess.bromsgroveandredditch.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'BromsgroveRedditch'
    _comment = 'Combined planning service covering Bromsgrove and Redditch'
    detail_tests = [
        { 'uid': '12/0794', 'len': 32 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 25 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 9 }  ]
   
class BuckinghamshireScraper(idox.IdoxScraper):

    _search_url = 'http://publicaccess.buckscc.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Buckinghamshire' 
    detail_tests = [
        { 'uid': '12/01571/CM', 'len': 26 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 5 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 }  ]
        
class CaerphillyScraper(idox.IdoxScraper): 

    _search_url = 'http://publicaccess.caerphilly.gov.uk/PublicAccess/search.do?action=advanced'
    _authority_name = 'Caerphilly'
    detail_tests = [
        { 'uid': '12/0562/FULL', 'len': 32 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 14 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 1 } ]
    
class CalderdaleScraper(idox.IdoxScraper):

    _search_url = 'http://portal.calderdale.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Calderdale'
    detail_tests = [
        { 'uid': '12/00890/FUL', 'len': 28 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 50 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 12 } ]
    
class CambridgeScraper(idox.IdoxScraper): 

    _search_url = 'https://idox.cambridge.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Cambridge'
    detail_tests = [
        { 'uid': '11/299/TTPO', 'len': 22 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 27 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 8 } ]
        
class CherwellScraper(idox.IdoxScraper):

    _search_url = 'http://www.publicaccess.cherwell.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Cherwell'
    detail_tests = [
        { 'uid': '12/01146/F', 'len': 33 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 52 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 12 } ]
    
class ChesterfieldScraper(idox.IdoxScraper): # OK to here

    _search_url = 'https://publicaccess.chesterfield.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Chesterfield'
    _comment = 'Was custom date scraper up to May 2016'
    detail_tests = [
        { 'uid': 'CHE/12/00512/FUL', 'len': 25 }, 
        ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '03/09/2012', 'to': '29/09/2012', 'len': 47 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 1 } ]

class ChichesterScraper(idox.IdoxScraper):

    _search_url = 'https://publicaccess.chichester.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Chichester'
    detail_tests = [
        { 'uid': '12/03230/DOM', 'len': 30 }, 
        ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 41 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 6 } ]
    
class ChilternScraper(idox.IdoxScraper):

    _search_url = 'https://isa.chiltern.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Chiltern'
    detail_tests = [
        { 'uid': 'CH/2012/1198/FA', 'len': 27 }, 
        ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 27 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 6 } ]
    
class ChorleyScraper(idox.IdoxScraper):

    _search_url = 'https://planning.chorley.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Chorley'
    detail_tests = [
        { 'uid': '12/00736/FUL', 'len': 26 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 21 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 4 }  ]

class CityScraper(idox.IdoxScraper):

    _search_url = 'http://www.planning2.cityoflondon.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'City'
    detail_tests = [
        { 'uid': '11/00590/FULL', 'len': 31 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 20 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 }  ]
        
class CorbyScraper(idox.IdoxScraper):

    _search_url = 'https://publicaccess.corby.gov.uk/publicaccess/search.do?action=advanced'
    _authority_name = 'Corby'
    detail_tests = [
        { 'uid': '12/00244/COU', 'len': 30 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 8 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 2 }  ]
    
class CornwallScraper(idox.IdoxScraper): 

    _search_url = 'http://planning.cornwall.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Cornwall'
    detail_tests = [
        { 'uid': 'PA12/08844', 'len': 19 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '16/09/2012', 'len': 80 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 49 } ]
        
class CotswoldScraper(idox.IdoxScraper): 

    _search_url = 'http://publicaccess.cotswold.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Cotswold'
    detail_tests = [
        { 'uid': '12/03555/FUL', 'len': 24 },  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 68 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 12 } ]
    
class CountyDurhamScraper(idox.IdoxScraper): 

    _search_url = 'https://publicaccess.durham.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'CountyDurham'
    detail_tests = [
        { 'uid': '5/PL/2012/0318', 'len': 27 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 59 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 21 } ]
        
class CravenScraper(idox.IdoxScraper): 

    _search_url = 'https://publicaccess.cravendc.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Craven'
    _comment = 'was Fastweb'
    detail_tests = [
        { 'uid': '30/2011/11959', 'len': 20 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 21 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]
        
class CroydonScraper(idox.IdoxScraper):

    _search_url = 'http://publicaccess2.croydon.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Croydon'
    detail_tests = [
        { 'uid': '16/04940/FUL', 'len': 30 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/08/2016', 'to': '19/08/2016', 'len': 136 }, 
        { 'from': '23/09/2016', 'to': '23/09/2016', 'len': 18 }  ]
        
class DartfordScraper(idox.IdoxScraper): 

    _search_url = 'http://publicaccess.dartford.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Dartford'
    detail_tests = [
        { 'uid': '12/01148/FUL', 'len': 30 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 22 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 }  ]
    
class DerbyshireDalesScraper(idox.IdoxScraper): 

    _search_url = 'https://planning.derbyshiredales.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'DerbyshireDales'
    detail_tests = [
        { 'uid': '11/00627/FUL', 'len': 34 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 16 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 }  ]
    
class DoncasterScraper(idox.IdoxScraper): 

    _search_url = 'https://planning.doncaster.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Doncaster'
    detail_tests = [
        { 'uid': '12/01863/FUL', 'len': 32 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 50 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]

class EalingScraper(idox.IdoxScraper): 

    _search_url = 'https://pam.ealing.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Ealing'
    _comment = 'was AppSearchServ up to end Jan 2016'
    detail_tests = [
        { 'uid': 'P/2012/4146', 'len': 22 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 82 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 23 } ]

class EastCambridgeshireScraper(idox.IdoxScraper): 

    _search_url = 'http://pa.eastcambs.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'EastCambridgeshire'
    detail_tests = [
        { 'uid': '12/00813/FUL', 'len': 27 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 20 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 7 } ]

class EastDevonScraper(idox.IdoxScraper): 

    _search_url = 'https://planning.eastdevon.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'EastDevon'
    detail_tests = [
        { 'uid': '12/1784/FUL', 'len': 21 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 42 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 12 } ]
    
"""class EastDorsetScraper(idox.IdoxScraper): # now Custom scraper with Christchurch

    _search_url = 'http://planning.eastdorsetdc.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'EastDorset'"""

class EastHertfordshireScraper(idox.IdoxScraper): 

    _search_url = 'https://publicaccess.eastherts.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'EastHertfordshire'
    detail_tests = [
        { 'uid': '3/12/1373/FP', 'len': 24 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 43 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 6 } ]
    
class EastRidingScraper(idox.IdoxScraper): 

    _search_url = 'https://newplanningaccess.eastriding.gov.uk/newplanningaccess/search.do?action=advanced'
    _authority_name = 'EastRiding'
    detail_tests = [
        { 'uid': '12/03644/PLF', 'len': 27 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 77 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 12 } ]
    
class EastSuffolkScraper(idox.IdoxScraper): 

    _search_url = 'http://planningpublicaccess.waveney.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'EastSuffolk'
    _comment = 'Combined planning service covering Suffolk Coastal and Waveney'
    detail_tests = [
        { 'uid': 'DC/12/0796/FUL', 'len': 35 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 66 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 16 } ]

class EnfieldScraper(idox.IdoxScraper): 

    _search_url = 'http://planningandbuildingcontrol.enfield.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Enfield'
    detail_tests = [
        { 'uid': 'P12-01776PLA', 'len': 27 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 33 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 7 } ]
        
class FenlandScraper(idox.IdoxScraper): 

    _search_url = 'http://www.fenland.gov.uk/publicaccess/search.do?action=advanced'
    _authority_name = 'Fenland'
    detail_tests = [
        { 'uid': 'F/YR12/0618/F', 'len': 32 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 20 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 7 } ]

class ForestOfDeanScraper(idox.IdoxScraper): 

    _search_url = 'https://publicaccess.fdean.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'ForestOfDean' 
    detail_tests = [
        { 'uid': 'P1056/12/FUL', 'len': 30 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 23 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 7 } ]

class GedlingScraper(idox.IdoxScraper): 

    _search_url = 'https://pawam.gedling.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Gedling'
    detail_tests = [
        { 'uid': '2012/0913', 'len': 30 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 13 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 }  ]

class GloucesterScraper(idox.IdoxScraper):

    _search_url = 'http://glcstrplnng12.co.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Gloucester'
    detail_tests = [
        { 'uid': '11/00922/FUL', 'len': 32 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 15 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 11 }  ]

class GloucestershireScraper(idox.IdoxScraper): # low numbers

    _search_url = 'http://planning.gloucestershire.gov.uk/publicaccess/search.do?action=advanced'
    _authority_name = 'Gloucestershire' 
    detail_tests = [
        { 'uid': '12/0037/CWMAJM', 'len': 30 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '13/10/2012', 'len': 4 }, 
        { 'from': '20/08/2012', 'to': '20/08/2012', 'len': 1 }  ]

class GosportScraper(idox.IdoxScraper): 

    _search_url = 'https://publicaccess.gosport.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Gosport'
    detail_tests = [
        { 'uid': '12/00299/FULL', 'len': 24 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 16 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 }  ]
    
class GraveshamScraper(idox.IdoxScraper): 

    _search_url = 'https://plan.gravesham.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Gravesham'
    detail_tests = [
        { 'uid': '20120642', 'len': 30 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 22 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 }  ]

class HambletonScraper(idox.IdoxScraper): 

    _search_url = 'https://planning.hambleton.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Hambleton'  
    detail_tests = [
        { 'uid': '13/01529/FUL', 'len': 29 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 37 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 4 } ]

class HarlowScraper(idox.IdoxScraper): 

    _search_url = 'https://planningonline.harlow.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Harlow'
    _comment = 'was Fastweb'
    detail_tests = [
        { 'uid': 'HW/PL/13/00028', 'len': 26 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 13 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]
    
class HarboroughScraper(idox.IdoxScraper): 

    _search_url = 'https://pa2.harborough.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Harborough'
    detail_tests = [
        { 'uid': '12/01090/FUL', 'len': 29 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 24 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 9 } ]
    
class HarrogateScraper(idox.IdoxScraper): # very slow

    _search_url = 'https://uniformonline.harrogate.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Harrogate'
    detail_tests = [
        { 'uid': '12/02805/FUL', 'len': 24 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 74 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 12 }  ]
    
class HartScraper(idox.IdoxScraper): 

    _search_url = 'http://publicaccess.hart.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Hart'
    detail_tests = [
        { 'uid': '12/01944/FUL', 'len': 24 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 46 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 9 }  ]

class HertsmereScraper(idox.IdoxScraper): 

    _search_url = 'http://www6.hertsmere.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Hertsmere' 
    detail_tests = [
        { 'uid': 'TP/12/1520', 'len': 29 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 27 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 }  ]

class HorshamScraper(idox.IdoxScraper):

    _search_url = 'https://public-access.horsham.gov.uk/public-access/search.do?action=advanced'
    _authority_name = 'Horsham'
    detail_tests = [
        { 'uid': 'DC/11/1597', 'len': 23 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 40 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 15 } ]
        
class HullScraper(idox.IdoxScraper): 

    _search_url = 'https://www.hullcc.gov.uk/padcbc/publicaccess-live/search.do?action=advanced'
    _authority_name = 'Hull' 
    detail_tests = [
        { 'uid': '12/00701/FULL', 'len': 21 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 22 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 7 }  ]
    
class HuntingdonshireScraper(idox.IdoxScraper): 

    _search_url = 'http://publicaccess.huntsdc.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Huntingdonshire'
    _cookies = [ { 'name': 'PublicAccess', 
        'value': 'AcceptDisclaimer', 
        'domain': '.huntingdonshire.gov.uk', 'path': '/' } ]
    detail_tests = [
        { 'uid': '1201445FUL', 'len': 30 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 43 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 6 } ]
        
class KingsLynnScraper(idox.IdoxScraper): # tested

    _search_url = 'http://online.west-norfolk.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'KingsLynn'
    detail_tests = [
        { 'uid': '12/01532/F', 'len': 30 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 35 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ]
        
class LambethScraper(idox.IdoxScraper):

    _search_url = 'https://planning.lambeth.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Lambeth'
    detail_tests = [
        { 'uid': '11/02704/FUL', 'len': 24 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 68 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 13 } ]

class LancasterScraper(idox.IdoxScraper):

    _search_url = 'https://planning.lancaster.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Lancaster'
    detail_tests = [
        { 'uid': '11/00748/FUL', 'len': 28 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 18 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 7 } ]
    
class LeedsScraper(idox.IdoxScraper):

    _search_url = 'https://publicaccess.leeds.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Leeds'
    detail_tests = [
        { 'uid': '12/03050/FU', 'len': 18 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 85 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 14 } ]

class LewesScraper(idox.IdoxScraper): 

    _search_url = 'http://planningpa.lewes.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Lewes'
    detail_tests = [
        { 'uid': 'LW/11/0982', 'len': 34 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 13 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]

class LincolnScraper(idox.IdoxScraper):

    _search_url = 'https://development.lincoln.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Lincoln'
    _comment = 'was Planning Explorer'
    detail_tests = [
        { 'uid': '2011/1030/F', 'len': 30 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 25 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ]
    
class MaldonScraper(idox.IdoxScraper): 

    _search_url = 'https://publicaccess.maldon.gov.uk//online-applications/search.do?action=advanced'
    _authority_name = 'Maldon'
    _comment = 'was Civica - note from 2004 onwards'
    detail_tests = [
        { 'uid': '12/00616/FUL', 'len': 28 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 28 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 8 } ]

class ManchesterScraper(idox.IdoxScraper):

    _search_url = 'http://pa.manchester.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Manchester'
    detail_tests = [
        { 'uid': '097035/AO/2011/N1', 'len': 20 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 54 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 16 } ]
        
class MansfieldScraper(idox.IdoxScraper): 

    _search_url = 'https://planning.mansfield.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Mansfield'
    _comment = 'was Fastweb'
    detail_tests = [
        { 'uid': '2011/0474/ST', 'len': 24 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 10 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 4 } ]

class MeltonScraper(idox.IdoxScraper): 

    _search_url = 'http://publicaccess.melton.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Melton'
    detail_tests = [
        { 'uid': '12/00505/FUL', 'len': 34 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 18 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 7 } ]
        
class MendipScraper(idox.IdoxScraper): # tested

    _search_url = 'http://publicaccess.mendip.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Mendip'
    _comment = 'was PlanningExplorer'
    detail_tests = [
        { 'uid': '2012/2265', 'len': 28 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 38 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ]
        
class MiddlesbroughScraper(idox.IdoxScraper): 

    _search_url = 'https://publicaccess.middlesbrough.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Middlesbrough'
    _comment = 'was Ocella'
    detail_tests = [
        { 'uid': 'M/FP/0865/11/P', 'len': 26 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 24 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]

class MidSussexScraper(idox.IdoxScraper):

    _search_url = 'https://pa.midsussex.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'MidSussex'
    detail_tests = [
        { 'uid': '11/02484/FUL', 'len': 26 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 40 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 8 } ]
    
class MiltonKeynesScraper(idox.IdoxScraper):
    
    _search_url = 'https://publicaccess2.milton-keynes.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'MiltonKeynes'
    detail_tests = [
        { 'uid': '12/01684/FUL', 'len': 27 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 42 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 10 } ]
    
class NewcastleUponTyneScraper(idox.IdoxScraper):
    
    _search_url = 'https://publicaccessapplications.newcastle.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'NewcastleUponTyne'
    detail_tests = [
        { 'uid': '2012/1199/01/DET', 'len': 30 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 33 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 11 } ]
    
class NewcastleUnderLymeScraper(idox.IdoxScraper):
    
    _search_url = 'https://publicaccess.newcastle-staffs.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'NewcastleUnderLyme'
    detail_tests = [
        { 'uid': '12/00439/FUL', 'len': 18 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 18 }, 
        { 'from': '15/08/2012', 'to': '15/08/2012', 'len': 3 }  ]
        
class NewhamScraper(idox.IdoxScraper):

    _search_url = 'https://pa.newham.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Newham'
    detail_tests = [
        { 'uid': '11/01361/FUL', 'len': 18 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 31 }, 
        { 'from': '15/08/2012', 'to': '15/08/2012', 'len': 8 }  ]
        
class NorthDorsetScraper(idox.IdoxScraper):

    _search_url = 'http://planning.north-dorset.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'NorthDorset'
    detail_tests = [
        { 'uid': '2/2012/0926/PLNG', 'len': 27 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 24 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 6 }  ]
    
class NorthEastDerbyshireScraper(idox.IdoxScraper):

    _search_url = 'http://planapps-online.ne-derbyshire.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'NorthEastDerbyshire'
    detail_tests = [
        { 'uid': '12/00845/FL', 'len': 31 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 26 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 }  ]
    
class NorthEastLincsScraper(idox.IdoxScraper):

    _search_url = 'http://planninganddevelopment.nelincs.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'NorthEastLincs'
    detail_tests = [
        { 'uid': 'DC/692/12/HUM', 'len': 24 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 33 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 7 }  ]

class NorthTynesideScraper(idox.IdoxScraper):

    _search_url = 'http://idoxpublicaccess.northtyneside.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'NorthTyneside'
    detail_tests = [
        { 'uid': '12/01308/FULH', 'len': 30 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 24 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 4 }  ]
    
class NorthumberlandScraper(idox.IdoxScraper):

    _search_url = 'https://publicaccess.northumberland.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Northumberland'
    detail_tests = [
        { 'uid': '12/02866/FUL', 'len': 29 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 66 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 10 }  ]
        
class NorthWestLeicestershireScraper(idox.IdoxScraper):

    _search_url = 'https://plans.nwleics.gov.uk/public-access/search.do?action=advanced'
    _authority_name = 'NorthWestLeicestershire'
    detail_tests = [
        { 'uid': '12/00801/FUL', 'len': 32 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 17 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 1 }  ]
    
class NottinghamScraper(idox.IdoxScraper):

    _search_url = 'http://publicaccess.nottinghamcity.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Nottingham'
    _comment = 'was WeeklyWAM'
    detail_tests = [
        { 'uid': '12/02133/PFUL3', 'len': 32 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 46 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 8 }  ]

class OxfordScraper(idox.IdoxScraper):

    _search_url = 'http://public.oxford.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Oxford'
    detail_tests = [
        { 'uid': '12/01893/FUL', 'len': 24 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 51 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 10 }  ]
    
class Pendle(idox.IdoxScraper):

    _search_url = 'https://publicaccess.pendle.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Pendle'
    _comment = 'was Civica'
    detail_tests = [
        { 'uid': '13/12/0352P', 'len': 23 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 15 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 } ]
    
class PeterboroughScraper(idox.IdoxScraper):

    _search_url = 'http://planpa.peterborough.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Peterborough'
    detail_tests = [
        { 'uid': '11/01273/FUL', 'len': 19 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 31 }, 
        { 'from': '28/08/2012', 'to': '28/08/2012', 'len': 6 }  ]

class PlymouthScraper(idox.IdoxScraper):

    _search_url = 'https://planning.plymouth.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Plymouth'
    _comment = 'was Fastweb'
    detail_tests = [
        { 'uid': '11/01380/FUL', 'len': 23 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 21 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 8 } ]
        
class PortsmouthScraper(idox.IdoxScraper):

    _search_url = 'http://publicaccess.portsmouth.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Portsmouth'
    detail_tests = [
        { 'uid': '12/00809/HOU', 'len': 30 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 19 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ]
    
class ReigateScraper(idox.IdoxScraper):

    _search_url = 'http://planning.reigate-banstead.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Reigate'
    detail_tests = [
        { 'uid': '12/01299/HHOLD', 'len': 28 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 42 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 15 } ]
    
class RichmondshireScraper(idox.IdoxScraper):

    _search_url = 'https://planning.richmondshire.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Richmondshire'
    detail_tests = [
        { 'uid': '12/00555/FULL', 'len': 22 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 28 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 5 } ]
        
class RossendaleScraper(idox.IdoxScraper):

    _search_url = 'https://publicaccess.rossendale.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Rossendale'
    _comment = 'Was ListScraper'
    detail_tests = [
        { 'uid': '2011/0416', 'len': 24 } ] 
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 14 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]
    
class RushcliffeScraper(idox.IdoxScraper):

    _search_url = 'https://planningon-line.rushcliffe.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Rushcliffe'
    detail_tests = [
        { 'uid': '12/01405/FUL', 'len': 30 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 29 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ]
    
class RushmoorScraper(idox.IdoxScraper): 

    _search_url = 'http://publicaccess.rushmoor.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Rushmoor'
    detail_tests = [
        { 'uid': '12/00581/FUL', 'len': 33 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 14 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 4 } ]
        
class RyedaleScraper(idox.IdoxScraper):

    _search_url = 'https://planningregister.ryedale.gov.uk/caonline-applications/search.do?action=advanced'
    _authority_name = 'Ryedale'
    detail_tests = [
        { 'uid': '12/00797/HOUSE', 'len': 34 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 18 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 2 } ]

class SalfordScraper(idox.IdoxScraper):

    _search_url = 'http://publicaccess.salford.gov.uk/publicaccess/search.do?action=advanced'
    _authority_name = 'Salford'
    detail_tests = [
        { 'uid': '12/62079/FUL', 'len': 32 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 23 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]
    
class SandwellScraper(idox.IdoxScraper):

    _search_url = 'http://webcaps.sandwell.gov.uk/publicaccess/search.do?action=advanced'
    _authority_name = 'Sandwell'
    detail_tests = [
        { 'uid': 'DC/12/55150', 'len': 27 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 21 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 1 } ]
    
class ScarboroughScraper(idox.IdoxScraper):

    _search_url = 'http://planning.scarborough.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Scarborough'
    detail_tests = [
        { 'uid': '12/01945/FL', 'len': 26 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 19 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]
    
class SeftonScraper(idox.IdoxScraper): 

    _search_url = 'http://pa.sefton.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Sefton'
    detail_tests = [
        { 'uid': 'S/2012/0989', 'len': 21 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 31 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 12 } ]
    
class SelbyScraper(idox.IdoxScraper):

    _search_url = 'http://public.selby.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Selby'
    detail_tests = [
        { 'uid': '2012/0778/FUL', 'len': 33 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 11 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 4 } ]
    
class SevenoaksScraper(idox.IdoxScraper):

    _search_url = 'https://pa.sevenoaks.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Sevenoaks'
    detail_tests = [
        { 'uid': '12/02085/HOUSE', 'len': 36 } ]
    batch_tests = [ # note date ranges shod not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 41 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 14 } ]
    
class SheffieldScraper(idox.IdoxScraper):

    _search_url = 'https://planningapps.sheffield.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Sheffield'
    detail_tests = [
        { 'uid': '12/02279/FUL', 'len': 26 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 57 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 19 } ]
    
class ShepwayScraper(idox.IdoxScraper):

    _search_url = 'https://searchplanapps.shepway.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Shepway'
    detail_tests = [
        { 'uid': 'Y12/0855/SH', 'len': 28 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 15 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 } ]
    
class ShropshireScraper(idox.IdoxScraper):

    _search_url = 'https://pa.shropshire.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Shropshire'
    detail_tests = [
        { 'uid': '12/03418/FUL', 'len': 29 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 76 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 25 } ]
    
class SolihullScraper(idox.IdoxScraper): 

    _search_url = 'https://publicaccess.solihull.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Solihull'
    _comment = 'was Custom PeriodScraper'
    detail_tests = [
        { 'uid': 'PL/2012/00382/FULL', 'len': 27 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 48 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 7 } ]

class SouthamptonScraper(idox.IdoxScraper):

    _search_url = 'https://planningpublicaccess.southampton.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Southampton'
    detail_tests = [
        { 'uid': '12/01319/FUL', 'len': 21 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 39 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ]

class SouthBucksScraper(idox.IdoxScraper): 

    _search_url = 'https://publicaccess.southbucks.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'SouthBucks'
    detail_tests = [
        { 'uid': '12/01307/FUL', 'len': 28 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 37 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 }  ]
        
class SouthDownsScraper(idox.IdoxScraper):

    data_start_target = '2012-02-09'
    _search_url = 'http://planningpublicaccess.southdowns.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'SouthDowns'
    detail_tests = [
        { 'uid': 'SDNP/12/01871/FUL', 'len': 25 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 80 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 19 }  ]

class SouthGloucestershireScraper(idox.IdoxScraper): 

    _search_url = 'http://developments.southglos.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'SouthGloucestershire'
    detail_tests = [
        { 'uid': 'PT12/3155/F', 'len': 26 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 38 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 14 }  ]
    
class SouthRibbleScraper(idox.IdoxScraper): 

    _search_url = 'http://publicaccess.southribble.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'SouthRibble'
    detail_tests = [
        { 'uid': '07/2012/0491/FUL', 'len': 30 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 33 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 }  ]
    
class SouthStaffordshireScraper(idox.IdoxScraper): 

    _search_url = 'http://www2.sstaffs.gov.uk:81/online-applications/search.do?action=advanced'
    _authority_name = 'SouthStaffordshire'
    detail_tests = [
        { 'uid': '12/00678/FUL', 'len': 32 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 12 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 4 } ]
    
class StaffordScraper(idox.IdoxScraper): 

    _search_url = 'https://www12.staffordbc.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Stafford'
    detail_tests = [
        { 'uid': '12/17464/HOU', 'len': 23 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 18 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 7 } ]
    
class StevenageScraper(idox.IdoxScraper): 

    _search_url = 'https://publicaccess.stevenage.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Stevenage'
    _comment = 'Was custom weekly period scraper'
    detail_tests = [
        { 'uid': '11/00694/FP', 'len': 29 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 25 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 2 } ]
        
class StHelensScraper(idox.IdoxScraper): 

    _search_url = 'http://publicaccess.sthelens.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'StHelens'
    detail_tests = [
        { 'uid': 'P/2011/0664', 'len': 27 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 22 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ]

class StockportScraper(idox.IdoxScraper): 

    _search_url = 'http://planning.stockport.gov.uk/PlanningData-live/search.do?action=advanced'
    _authority_name = 'Stockport'
    detail_tests = [
        { 'uid': 'DC/050546', 'len': 23 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 43 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 17 } ]
        
class StocktonScraper(idox.IdoxScraper): 

    _search_url = 'http://www.developmentmanagement.stockton.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Stockton'
    detail_tests = [
        { 'uid': '12/1753/FUL', 'len': 29 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 21 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 5 } ]
    
class SunderlandScraper(idox.IdoxScraper):

    _search_url = 'http://www.sunderland.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Sunderland'
    detail_tests = [
        { 'uid': '11/02541/FUL', 'len': 30 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 31 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 }  ]
    
class SwanseaScraper(idox.IdoxScraper): 

    _search_url = 'http://property.swansea.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Swansea'
    _comment = 'was WeeklyWAM'
    detail_tests = [
        { 'uid': '2012/1066', 'len': 31 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 34 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 } ]
    
class SwindonScraper(idox.IdoxScraper): 

    _search_url = 'http://pa1.swindon.gov.uk/publicaccess/search.do?action=advanced'
    _authority_name = 'Swindon'
    detail_tests = [
        { 'uid': 'S/12/0994', 'len': 29 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 35 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 } ]

class TendringScraper(idox.IdoxScraper): 

    _search_url = 'https://idox.tendringdc.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Tendring'
    detail_tests = [
        { 'uid': '12/00822/FUL', 'len': 31 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 25 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 7 } ]

class TewkesburyScraper(idox.IdoxScraper): 

    _search_url = 'http://publicaccess.tewkesbury.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Tewkesbury'
    detail_tests = [
        { 'uid': '12/00745/FUL', 'len': 30 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 29 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ]

class ThanetScraper(idox.IdoxScraper): 

    _search_url = 'https://planning.thanet.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Thanet'
    detail_tests = [
        { 'uid': 'F/TH/12/0600', 'len': 26 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 19 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 } ]
     
class ThreeRiversScraper(idox.IdoxScraper): 

    _search_url = 'http://www3.threerivers.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'ThreeRivers'
    detail_tests = [
        { 'uid': '12/1543/FUL', 'len': 28 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 38 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 9 } ]
    
class ThurrockScraper(idox.IdoxScraper): 

    _search_url = 'http://regs.thurrock.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Thurrock'
    detail_tests = [
        { 'uid': '12/00872/FUL', 'len': 28 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 13 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 1 } ]
    
class TonbridgeScraper(idox.IdoxScraper): 

    _search_url = 'https://publicaccess2.tmbc.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Tonbridge'
    detail_tests = [
        { 'uid': '12/02492/FL', 'len': 29 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 33 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 7 } ]

class TorfaenScraper(idox.IdoxScraper): 

    _search_url = 'https://planningonline.torfaen.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Torfaen'
    detail_tests = [
        { 'uid': '12/P/00281', 'len': 25 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '29/09/2012', 'len': 43 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 } ]
        
class TorridgeScraper(idox.IdoxScraper): 

    _search_url = 'http://publicaccess.torridge.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Torridge'
    detail_tests = [
        { 'uid': '1/0654/2012/FUL', 'len': 35 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 12 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]
        
class TraffordScraper(idox.IdoxScraper): 

    _search_url = 'http://publicaccess.trafford.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Trafford'
    _comment = 'was PlanningExplorer'
    detail_tests = [
        { 'uid': '77342/HHA/2011', 'len': 28 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 26 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 } ]
        
class TunbridgeWellsScraper(idox.IdoxScraper): 

    _search_url = 'http://twbcpa.midkent.gov.uk/online-applications//search.do?action=advanced'
    _authority_name = 'TunbridgeWells'
    _comment = 'was part of Mid Kent Planning Support Service (with Maidstone and Swale) but separated out in July 2016'
    detail_tests = [
        { 'uid': '12/02070/HOUSE', 'len': 24 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 40 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 14 } ]
        
class UttlesfordScraper(idox.IdoxScraper): 

    _search_url = 'http://publicaccess.uttlesford.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Uttlesford'
    detail_tests = [
        { 'uid': 'UTT/1467/12/FUL', 'len': 33 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 50 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 8 } ]
    
class WakefieldScraper(idox.IdoxScraper): 

    _search_url = 'https://planning.wakefield.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Wakefield'
    detail_tests = [
        { 'uid': '11/01618/ADV', 'len': 32 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 49 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 12 } ]
    
class WatfordScraper(idox.IdoxScraper): 

    _search_url = 'http://pa.watford.gov.uk/publicaccess/search.do?action=advanced'
    _authority_name = 'Watford'
    detail_tests = [
        { 'uid': '12/00715/FUL', 'len': 29 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 30 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 } ]
    
class WellingboroughScraper(idox.IdoxScraper): 

    _search_url = 'http://pawebsrv.wellingborough.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Wellingborough'
    _comment = 'Was AppSearchServ up to Mar 2014'
    detail_tests = [
        { 'uid': 'WP/2011/0373', 'len': 26 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 17 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 } ]
        
class WestBerkshireScraper(idox.IdoxScraper): 

    _search_url = 'https://publicaccess.westberks.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'WestBerkshire'
    detail_tests = [
        { 'uid': '12/01798/HOUSE', 'len': 18 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 49 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 19 } ]
    
class WestLancashireScraper(idox.IdoxScraper): 

    _search_url = 'https://pa.westlancs.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'WestLancashire'
    detail_tests = [
        { 'uid': '2012/0794/FUL', 'len': 27 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 26 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ]
    
class WestminsterScraper(idox.IdoxScraper):

    _search_url = 'http://idoxpa.westminster.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Westminster'
    detail_tests = [
        { 'uid': '11/07236/FULL', 'len': 27 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 219 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 44 } ]
        
class WestOxfordshireScraper(idox.IdoxScraper): 

    _search_url = 'http://publicaccess.westoxon.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'WestOxfordshire'
    detail_tests = [
        { 'uid': '12/1333/P/FP', 'len': 20 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 28 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 7 } ]
        
class WestSuffolkScraper(idox.IdoxScraper): 

    _search_url = 'https://planning.westsuffolk.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'WestSuffolk'
    _comment = 'Combined planning service covering Forest Heath and St Edmundsbury'
    detail_tests = [
        { 'uid': 'F/2012/0600/HOU', 'len': 27 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 30 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 10 } ]

class WinchesterScraper(idox.IdoxScraper): 

    _search_url = 'http://planningapps.winchester.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Winchester'
    detail_tests = [
        { 'uid': '12/01580/FUL', 'len': 23 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 38 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 10 } ]
        
class WindsorScraper(idox.IdoxScraper): 

    _search_url = 'http://publicaccess.rbwm.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Windsor'
    _comment = 'Was Custom Date scraper'
    detail_tests = [
        { 'uid': '12/02545/FULL', 'len': 25 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 64 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 10 } ]
    
class WolverhamptonScraper(idox.IdoxScraper): 

    _search_url = 'http://planningonline.wolverhampton.gov.uk:2707/online-applications/search.do?action=advanced'
    _authority_name = 'Wolverhampton'
    detail_tests = [
        { 'uid': '12/00830/FUL', 'len': 35 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 23 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ]
    
class WycombeScraper(idox.IdoxScraper): 

    _search_url = 'http://publicaccess.wycombe.gov.uk/idoxpa-web/search.do?action=advanced'
    _authority_name = 'Wycombe'
    detail_tests = [
        { 'uid': '12/06622/FUL', 'len': 25 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 56 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 8 } ]
    
class YorkScraper(idox.IdoxScraper): 

    _search_url = 'https://planningaccess.york.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'York'
    detail_tests = [
        { 'uid': '12/02508/FUL', 'len': 37 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 51 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 16 } ]
    


