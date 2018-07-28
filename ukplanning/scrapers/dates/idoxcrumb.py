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
        
class IdoxCrumbScraper(idox.IdoxScraper):
        
    _scrape_min_data = """
    <div class="addressCrumb">
    <span class="caseNumber"> {{ reference }} </span>
    <span class="description"> {{ description }} </span>
    <span class="address"> {{ address }} </span>
    </div>
    """
    _scrape_min_dates = """
    <th> Agreed Expiry Date </th> <td> {{ application_expires_date }} </td>
    """
    _scrape_one_id = """
    <div class="addressCrumb">
        <span class="caseNumber"> {{ uid }} </span>
    </div>
    <a id="subtab_summary" href="{{ url|abs }}" />
    """
    _min_fields = [ 'reference', 'address', 'description', 'application_expires_date', 'application_type' ]
    
class BreconBeaconsScraper(IdoxCrumbScraper):

    data_start_target = '2005-12-01'
    batch_size = 28 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 28 # start this number of days ago when gathering current ids
    
    _search_url = 'http://planningbreconnpa.org/online-applications/search.do?action=advanced'
    _authority_name = 'BreconBeacons'
    _scrape_min_dates = """
    <th> Validated </th> <td> {{ date_validated }} </td>
    """
    _min_fields = [ 'reference', 'address', 'description', 'date_validated', 'application_type' ]
    detail_tests = [
        { 'uid': '12/08363/FUL', 'len': 20 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 14 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]
        
class BroadsScraper(IdoxCrumbScraper):

    _search_url = 'http://planning.broads-authority.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Broads'
    _scrape_min_dates = """
    <th> Validated </th> <td> {{ date_validated }} </td>
    """
    _min_fields = [ 'reference', 'address', 'description', 'date_validated', 'application_type' ]
    detail_tests = [
        { 'uid': 'BA/2012/0262/FUL', 'len': 26 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 3 }, 
        { 'from': '14/08/2012', 'to': '14/08/2012', 'len': 2 } ]
    
class CheltenhamScraper(IdoxCrumbScraper):

    _search_url = 'http://publicaccess.cheltenham.gov.uk/idoxpa17/search.do?action=advanced'
    _authority_name = 'Cheltenham'
    detail_tests = [
        { 'uid': '12/01305/FUL', 'len': 30 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 35 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 }  ]

class EastLothianScraper(IdoxCrumbScraper): 

    _search_url = 'http://pa.eastlothian.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'EastLothian'
    _scrape_min_dates = """
    <th> Validated </th> <td> {{ date_validated }} </td>
    """
    _min_fields = [ 'reference', 'address', 'description', 'date_validated', 'application_type' ]
    
    detail_tests = [
        { 'uid': '12/00575/P', 'len': 27 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 25 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 }  ]

class EastNorthamptonshireScraper(IdoxCrumbScraper): 

    _search_url = 'http://pawebsrv.east-northamptonshire.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'EastNorthamptonshire'
    _min_fields = [ 'reference', 'address', 'description', 'application_type' ] # for testing only
    detail_tests = [
        { 'uid': '12/01327/FUL', 'len': 15 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 21 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 } ]
    
class EpsomScraper(IdoxCrumbScraper): 

    _search_url = 'http://eplanning.epsom-ewell.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Epsom'
    _min_fields = [ 'reference', 'address', 'description', 'application_type' ] # for testing only
    detail_tests = [
        { 'uid': '12/00547/FLH', 'len': 15 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 29 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ]
    
class GatesheadScraper(IdoxCrumbScraper): 

    _search_url = 'http://public.gateshead.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Gateshead'
    _scrape_min_dates = """
    <th> Validated </th> <td> {{ date_validated }} </td>
    """
    _min_fields = [ 'reference', 'address', 'description', 'date_validated', 'application_type' ]
    detail_tests = [
        { 'uid': 'DC/12/00827/HHA', 'len': 22 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 17 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 3 }  ]
       
class KnowsleyScraper(IdoxCrumbScraper): 

    _search_url = 'https://planapp.knowsley.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Knowsley'
    _min_fields = [ 'reference', 'address', 'description', 'application_type' ] # for testing only
    detail_tests = [
        { 'uid': '12/00442/FUL', 'len': 21 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 15 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 1 } ]
           
class LutonScraper(IdoxCrumbScraper):

    _search_url = 'https://planning.luton.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Luton'
    _comment = 'Was Public Access'
    detail_tests = [
        { 'uid': '12/00934/FUL', 'len': 28 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 27 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 7 } ]
   
class MerthyrTydfilScraper(IdoxCrumbScraper):

    batch_size = 14 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 20 # start this number of days ago when gathering current ids
    
    _search_url = 'http://publicaccess.merthyr.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'MerthyrTydfil'
    _min_fields = [ 'reference', 'address', 'description', 'application_type' ] # for testing only
    detail_tests = [
        { 'uid': 'P/12/0223', 'len': 15 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 7 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]

class MidDevonScraper(IdoxCrumbScraper): 

    _search_url = 'https://planning.middevon.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'MidDevon' 
    _scrape_min_dates = """
    <th> Determination Deadline </th> <td> {{ target_decision_date }} </td>
    """
    _min_fields = [ 'reference', 'address', 'description', 'target_decision_date', 'application_type' ] # for testing only
    detail_tests = [
        { 'uid': '12/01164/FULL', 'len': 25 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 33 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ]
        
class NorwichScraper(IdoxCrumbScraper):

    _search_url = 'https://planning.norwich.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Norwich'
    detail_tests = [
        { 'uid': '12/01487/F', 'len': 28 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 29 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 11 }  ]

class RochdaleScraper(IdoxCrumbScraper):

    _search_url = 'http://publicaccess.rochdale.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Rochdale'
    detail_tests = [
        { 'uid': '12/55788/FUL', 'len': 35 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 21 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 5 } ]
    
class SouthendScraper(IdoxCrumbScraper): 

    _search_url = 'https://publicaccess.southend.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Southend'
    detail_tests = [
        { 'uid': '12/00960/FULH', 'len': 21 }  ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 32 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 4 }  ]
         
class WokingScraper(IdoxCrumbScraper): 

    _search_url = 'http://caps.woking.gov.uk/online-applications/search.do?action=advanced'
    _authority_name = 'Woking'
    _scrape_min_dates = """
    <th> Validated </th> <td> {{ date_validated }} </td>
    """
    _min_fields = [ 'reference', 'address', 'description', 'date_validated', 'application_type' ]
    detail_tests = [
        { 'uid': 'PLAN/2012/0681', 'len': 25 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 28 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 2 } ]




