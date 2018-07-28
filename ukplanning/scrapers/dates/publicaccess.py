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
from .. import base
try:
    from ukplanning import scrapeutils
except ImportError:
    import scrapeutils
from datetime import timedelta

class PublicAccessScraper(base.DateScraper):

    min_id_goal = 300 # min target for application ids to fetch in one go
    
    _disabled = True # default, selectively enabled below
    _scraper_type = 'PublicAccess'
    _date_from_field = 'srchDateReceivedStart'
    _date_to_field = 'srchDateReceivedEnd'
    _detail_page = 'application_detailview.aspx'
    _search_fields = { }
    _search_form = 'searchform'
    _scrape_ids = """
     <table class="cResultsForm"> <tr />
    {* <tr>
    <td> {{ [records].uid }} </td> <td> <a href="{{ [records].url|abs }}"> </a> </td>
    </tr> *}
    </table>
    """
    _next_page = 'Next Page'
    _ref_field = 'caseNo'
    _scrape_max_recs = '<td class="cFormContent"> {{ max_recs }} matching </td>'
   
    # captures HTML block encompassing all fields to be gathered
    _scrape_data_block = "<body> {{ block|html }} </body>"
    # the minimum acceptable valid dataset on the details page
    _scrape_min_data = """
    <input id="applicationno" value="{{ reference }}">
    <textarea id="address"> {{ address }} </textarea>
    <textarea id="desc"> {{ description }} </textarea>
    """
    # other optional parameters that can appear on the details page
    _scrape_optional_data = [
    '<input id="PPReference" value="{{ planning_portal_id }}">',
    '<input id="type" value="{{ application_type }}">',
    '<input id="applicationstatus" value="{{ status }}">',
    '<input id="decision" value="{{ decision }}">',
    '<input id="decisiontype" value="{{ decided_by }}">',
    '<input id="officer" value="{{ case_officer }}">',
    '<input id="parish" value="{{ parish }}">',
    '<input id="wardname" value="{{ ward_name }}">',
    '<input id="wardnamesubmit" value="{{ ward_name }}">',
    '<input id="daterecv" value="{{ date_received }}">',
    '<input id="datevalid" value="{{ date_validated }}">',
    '<input id="targetdate" value="{{ target_decision_date }}">',
    '<input id="dateactualcommittee" value="{{ meeting_date }}">',
    '<input id="firstdcdate" value="{{ meeting_date }}">',
    '<input id="lgd" value="{{ district }}">',
    '<input id="dateneighbourconsult" value="{{ neighbour_consultation_start_date }}">',
    '<input id="dateneighbourexpiry" value="{{ neighbour_consultation_end_date }}">',
    '<input id="stconsultation" value="{{ consultation_start_date }}">',
    '<input id="consultationex" value="{{ consultation_end_date }}">',
    '<input id="dateadvert" value="{{ last_advertised_date }}">',
    '<input id="dateadvertexpiry" value="{{ latest_advertisement_expiry_date }}">',
    '<input id="datedecisionmade" value="{{ decision_date }}">',
    '<input id="datedecisionissued" value="{{ decision_issued_date }}">',
    '<input id="datepermissionexpiry" value="{{ permission_expires_date }}">',
    '<input id="datedecisionprinted" value="{{ decision_published_date }}">',
    '<input id="applicantname" value="{{ applicant_name }}">',
    '<textarea id="applicantaddress"> {{ applicant_address }} </textarea>',
    '<input id="agentname" value="{{ agent_name }}">',
    '<textarea id="agentaddress"> {{ agent_address }} </textarea>',
    '<input id="agentcondetail" value="{{ agent_tel }}">',
    '<input id="agentphonenumber" value="{{ agent_tel }}">',
    '<input id="dateexpiry" value="{{ application_expires_date }}">',
    '<input id="datesitenotice" value="{{ site_notice_start_date }}">',
    '<input id="datesitenoticeexpiry" value="{{ site_notice_end_date }}">',
    ]

    def get_id_batch (self, date_from, date_to):

        final_result = []
        response = self.br.open(self._search_url)
        #self.logger.debug("Start html: %s", response.read())

        fields = {}
        fields.update(self._search_fields)
        fields[self._date_from_field] = date_from.strftime(self._request_date_format)
        fields[self._date_to_field] = date_to.strftime(self._request_date_format)
        scrapeutils.setup_form(self.br, self._search_form, fields)
        self.logger.debug("ID batch form: %s", str(self.br.form))
        response = scrapeutils.submit_form(self.br)
        
        html = response.read()
        try:
            result = scrapemark.scrape(self._scrape_max_recs, html)
            if result['max_recs'] == 'One':
                max_recs = 1
            else:
                max_recs = int(result['max_recs'])
        except:
            max_recs = 0
        self.logger.debug("max_recs: %d", max_recs)
        
        page_count = 0
        max_pages = (2 * self.min_id_goal / 10) + 20 # guard against infinite loop
        while response and len(final_result) < max_recs and page_count < max_pages:
            url = response.geturl()
            #self.logger.debug("ID batch page html: %s", html)
            result = scrapemark.scrape(self._scrape_ids, html, url)
            if result and result.get('records'):
                page_count += 1
                self._clean_ids(result['records'])
                final_result.extend(result['records'])
            else:
                self.logger.debug("Empty result after %d pages", page_count)
                break
            if len(final_result) >= max_recs:
                break
            try:
                response = self.br.follow_link(text=self._next_page)
                html = response.read()
            except: # failure to find next page link at end of page sequence here
                self.logger.debug("No next link after %d pages", page_count)
                break
                
        if page_count >= max_pages:
            self.logger.warning("Too many page requests - %d - probable run away loop" % page_count)
               
        return final_result

    def get_html_from_uid (self, uid):
        response = self.br.open(self._search_url)
        #self.logger.debug("ID detail start html: %s", response.read())
        fields = {  self._ref_field: uid }
        scrapeutils.setup_form(self.br, self._search_form, fields)
        response = scrapeutils.submit_form(self.br)
        html, url = self._get_html(response)
        result = scrapemark.scrape(self._scrape_ids, html, url)
        if result and result.get('records'):
            self._clean_ids(result['records'])
            for r in result['records']:
                if r.get('uid', '') == uid and r.get('url'):
                    self.logger.debug("Scraped url: %s", r['url'])
                    return self.get_html_from_url(r['url'])
        return None, None
            
"""class NorthernIrelandScraper(PublicAccessScraper): see ulster.py 

    _search_url = 'http://epicpublic.planningni.gov.uk/PublicAccess/zd/zdApplication/application_searchform.aspx'
    _scraper_type = 'NIPublicAccess'
    
    def get_id_batch (self, date_from, date_to): # end date is exclusive, not inclusive
        date_to = date_to + timedelta(days=1) # increment end date by one day
        return super(NorthernIrelandScraper, self).get_id_batch(date_from, date_to)"""

"""class BexleyScraper(PublicAccessScraper): # now Idox

    _search_url = 'http://publicaccess.bexley.gov.uk/publicaccess/tdc/DcApplication/application_searchform.aspx'
    _authority_name = 'Bexley'
        
class DurhamCityScraper(PublicAccessScraper): 

    _search_url = 'http://publicaccess.durhamcity.gov.uk/publicaccess/tdc/DcApplication/application_searchform.aspx'
    _authority_name = 'DurhamCity'
    _disabled = True
    _comment = 'Now County Durham Idox'
    
class ChesterLeStreetScraper(PublicAccessScraper): 

    batch_size = 28 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 28 # min number of days to get when gathering current ids
    _search_url = 'http://planning.chester-le-street.gov.uk/publicaccess/tdc/DcApplication/application_searchform.aspx'
    _authority_name = 'ChesterLeStreet'
    _disabled = True
    _comment = 'Now County Durham Idox'
    
class FenlandScraper(PublicAccessScraper): # now Idox

    _search_url = 'http://www.fenland.gov.uk/publicaccess/tdc/DcApplication/application_searchform.aspx'
    _authority_name = 'Fenland'
    detail_tests = [
        { 'uid': 'F/YR12/0645/F', 'len': 26 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 20 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 7 } ]
    
class HammersmithScraper(PublicAccessScraper): # now Idox

    _search_url = 'http://www.apps.lbhf.gov.uk/PublicAccess/tdc/DcApplication/application_searchform.aspx'
    _authority_name = 'Hammersmith'
    
class KnowsleyScraper(PublicAccessScraper): # now Idox

    _search_url = 'http://publicaccess.knowsley.gov.uk/PublicAccess/tdc/DcApplication/application_searchform.aspx'
    _authority_name = 'Knowsley'
    
class LutonScraper(PublicAccessScraper):

    _search_url = 'http://www.eplan.luton.gov.uk/PublicAccess/tdc/DcApplication/application_searchform.aspx'
    _authority_name = 'Luton'
    _disabled = False
    _comment = 'Now Idox'
    detail_tests = [
        { 'uid': '12/00934/FUL', 'len': 28 } ]
    batch_tests = [ # note date ranges should not overlap
        { 'from': '13/09/2012', 'to': '19/09/2012', 'len': 27 }, 
        { 'from': '13/08/2012', 'to': '13/08/2012', 'len': 7 } ]
        
class MeltonScraper(PublicAccessScraper): # now Idox

    _search_url = 'http://publicaccess.melton.gov.uk/PALiveSystem77/tdc/DcApplication/application_searchform.aspx'
    _authority_name = 'Melton'
    
class OadbyScraper(PublicAccessScraper): # now Idox

    batch_size = 36 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 36 # min number of days to get when gathering current ids
    _search_url = 'http://pa.owbc.net/PublicAccess/tdc/DcApplication/application_searchform.aspx'
    _authority_name = 'Oadby'
    
class OlympicDeliveryScraper(PublicAccessScraper): 

    data_start_target = '2006-09-01'
    batch_size = 28 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 28 # min number of days to get when gathering current ids
    _comment = 'Closed in December 2014'
    _search_url = 'http://planning.london2012.com/publicaccess/tdc/DcApplication/application_searchform.aspx'
    _authority_name = 'OlympicDelivery'
    _disabled = True
    
class SandwellScraper(PublicAccessScraper): # now Idox

    _search_url = 'http://webcaps.sandwell.gov.uk/PublicAccess/tdc/DcApplication/application_searchform.aspx'
    _authority_name = 'Sandwell'
    
class SouthamptonScraper(PublicAccessScraper): # now Idox

    search_url = 'http://publicaccess.southampton.gov.uk/PublicAccess/tdc/DcApplication/application_searchform.aspx'
    _authority_name = 'Southampton'
    
class SouthBucksScraper(PublicAccessScraper): # now Idox
    
    _search_url = 'http://sbdc-paweb.southbucks.gov.uk/publicaccess/tdc/DcApplication/application_searchform.aspx'
    _authority_name = 'SouthBucks'
    
class SouthendScraper(PublicAccessScraper): # now Idox

    _search_url = 'http://planning.southend.gov.uk/PublicAccess/tdc/DcApplication/application_searchform.aspx'
    _authority_name = 'Southend'
    
class StaffordshireMoorlandsScraper(PublicAccessScraper): # now AppSearchServ

    _search_url = 'http://publicaccess.staffsmoorlands.gov.uk/publicaccess/tdc/DcApplication/application_searchform.aspx'
    _authority_name = 'StaffordshireMoorlands'
    
class SwindonScraper(PublicAccessScraper): # now Idox

    _search_url = 'http://195.89.201.121/PublicAccess77/tdc/DcApplication/application_searchform.aspx'
    _authority_name = 'Swindon'
    
class WatfordScraper(PublicAccessScraper): # now Idox
    
    search_url = 'http://ww3.watford.gov.uk/publicaccess/tdc/DcApplication/application_searchform.aspx'

class WaveneyScraper(PublicAccessScraper): # now Idox

    _search_url = 'http://publicaccess.waveney.gov.uk/PASystem77/tdc/DcApplication/application_searchform.aspx'
    _authority_name = 'Waveney'
    
class WestLancashireScraper(PublicAccessScraper): # now Idox

    _search_url = 'http://publicaccess.westlancsdc.gov.uk/PublicAccess/tdc/DcApplication/application_searchform.aspx'
    _authority_name = 'WestLancashire'
    
class WorcestershireScraper(PublicAccessScraper): # now SwiftLG

    batch_size = 42 # batch size for each scrape - number of days to gather to produce at least one result each time
    current_span = 28 # min number of days to get when gathering current ids
    _search_url = 'http://www.worcestershire.gov.uk/PublicAccess/tdc/DcApplication/application_searchform.aspx'
    _authority_name = 'Worcester'
    _scrape_ids = ""
    <table class="whubTable"> <tr />
    {* <tr>
    <td> {{ [records].uid }} </td> <td> <a href="{{ [records].url|abs }}"> </a> </td>
    </tr> *}
    </table>
    ""
    _scrape_max_recs = '<p>A total of {{ max_recs }} matching applications were found.</p>'
    _scrape_min_data = ""
    <input id="idApplicationReferenceValue" value="{{ reference }}">
    <textarea id="idLocationValue"> {{ address }} </textarea>
    <textarea id="idProposalValue"> {{ description }} </textarea>
    ""
    _scrape_optional_data = [
    '<input id="idPlanningPortalReferenceValue" value="{{ planning_portal_id }}">',
    '<input id="idTypeValue" value="{{ application_type }}">',
    '<input id="idStatusValue" value="{{ status }}">',
    '<input id="idDecisionTakenValue" value="{{ decision }}">',
    '<input id="idDecisionLevelValue" value="{{ decided_by }}">',
    '<input id="idCaseOfficerValue" value="{{ case_officer }}">',
    '<input id="idParishValue" value="{{ parish }}">',
    '<input id="idElectoralDivisionCurrentValue" value="{{ ward_name }}">',
    '<input id="idElectoralDivisionCurrentDistrictValue" value="{{ district }}">',
    
    '<input id="idDateReceivedValue" value="{{ date_received }}">',
    '<input id="idDateValidatedValue" value="{{ date_validated }}">',
    '<input id="idDateTargetDeterminationValue" value="{{ target_decision_date }}">',
    '<input id="idDateCommitteeValue" value="{{ meeting_date }}">',
    '<input id="idDateNeighbourConsultationsSentValue" value="{{ neighbour_consultation_start_date }}">',
    '<input id="idDateNeighbourConsultationsExpiryValue" value="{{ neighbour_consultation_end_date }}">',
    '<input id="idDateStandardConsultationsSentValue" value="{{ consultation_start_date }}">',
    '<input id="idDateStandardConsultationsExpiryValue" value="{{ consultation_end_date }}">',
    '<input id="idDateLatestAdvertisementPostedValue" value="{{ last_advertised_date }}">',
    '<input id="idDateLatestAdvertisementExpiryValue" value="{{ latest_advertisement_expiry_date }}">',
    '<input id="idDateOverallExpiryValue" value="{{ application_expires_date }}">',
    '<input id="idDateLatestPublicNoticePostedValue" value="{{ site_notice_start_date }}">',
    '<input id="idDateLatestPublicNoticeExpiryValue" value="{{ site_notice_end_date }}">',

    '<input id="idDateDecisionTakenValue" value="{{ decision_date }}">',
    '<input id="idDateDecisionIssuedValue" value="{{ decision_issued_date }}">',
    '<input id="idDatePermissionExpiryValue" value="{{ permission_expires_date }}">',
    '<input id="idDateDecisionPrintedValue" value="{{ decision_published_date }}">',

    '<input id="idApplicantNameValue" value="{{ applicant_name }}">',
    '<textarea id="idApplicantAddressValue"> {{ applicant_address }} </textarea>',
    '<input id="idAgentNameValue" value="{{ agent_name }}">',
    '<textarea id="idAgentAddressValue"> {{ agent_address }} </textarea>',
    '<input id="idAgentPhoneValue" value="{{ agent_tel }}">',
    ]"""


