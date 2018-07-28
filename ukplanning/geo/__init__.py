from osgb import eastnorth_to_osgb, osgb_to_lonlat, lonlat_to_eastnorth, osgb_to_eastnorth
from geo_helper import turn_osgb36_into_wgs84, turn_eastingnorthing_into_osgb36, turn_eastingnorthing_into_osie36, turn_osie36_into_wgs84
from geo_helper import turn_wgs84_into_osgb36, turn_osgb36_into_eastingnorthing, turn_wgs84_into_osie36, turn_osie36_into_eastingnorthing
from math import radians, cos, sin, asin, sqrt, pi
import urllib2
import re
import sys
sys.path.append('..')

MINUKLNG = -11.0 # now includes most westerly point of Ireland as well
MAXUKLNG = 4.0
MINUKLAT = 48.0
MAXUKLAT = 62.0
MAXEAST = 800000.0 # metres from origin of GB grid (max 6 digits)
MAXNORTH = 1300000.0 # 7 digits to cover Shetland
LOWEAST = 10000.0 
LOWNORTH = 100000.0 
MAXEAST_IE = 400000.0 # metres from origin of IE grid
MAXNORTH_IE = 500000.0 
LOWEAST_IE = 1000.0 
LOWNORTH_IE = 1000.0 


try:
  import json
except:
  import simplejson as json


'''standardized to wgs84 (if possible)'''


def os_easting_northing_to_latlng(easting, northing, grid='GB'):
    '''Convert easting, northing to latlng assuming altitude 200m'''
    if grid == 'GB':
        oscoord = turn_eastingnorthing_into_osgb36(easting, northing)
        latlng = turn_osgb36_into_wgs84(oscoord[0], oscoord[1], 200)
    elif grid == 'IE':
        oscoord = turn_eastingnorthing_into_osie36(easting, northing)
        latlng = turn_osie36_into_wgs84(oscoord[0], oscoord[1], 200)
    return latlng[0], latlng[1]
    
def latlng_to_os_easting_northing(lat, lng, grid='GB'):
    '''Convert latlng to easting, northing assuming altitude 200m'''
    if grid == 'GB':
        oscoord = turn_wgs84_into_osgb36(lat, lng, 200)
        eastnorth = turn_osgb36_into_eastingnorthing(oscoord[0], oscoord[1])
    elif grid == 'IE':
        oscoord = turn_wgs84_into_osie36(lat, lng, 200)
        eastnorth = turn_osie36_into_eastingnorthing(oscoord[0], oscoord[1])
    return int(round(eastnorth[0], 0)), int(round(eastnorth[1], 0))
    
def eastnorth_float(east, north): 
    """ scraped eastings/northings are normally 6 integer digits, corresponding to metres (although metre northings for Shetland can require 7 digits)
    (4 digits = units of 100m, 6 digits = units of 1m - see http://www.ordnancesurvey.co.uk/resources/maps-and-geographic-resources/calculating-distances-using-grid-references.html)
    but some (Planning Explorer) systems return both values as 7 digits - assumed to require decimal point after six chars
    other cases one has fewer digits -> assumed to require right zero padding to six digits (NO LONGER CATERED FOR)
    in other cases one of the coordinates has fewer than 6 digits = assumed to be just systems which omit any leading zeroes -> OK as they are (implicit left zero padding)
    """
    if isinstance(east, float) and isinstance(north, float):
        #if east >= 1000000.0 or north >= 1000000.0:
        #    return east / 10.0, north / 10.0
        #else:
        return east, north
    else:
        east = str(east).strip()
        north = str(north).strip()
        if '.' not in east and '.' not in north:
            if len(east) == len(north) and len(east) > 6: # only applies if same string length
                return float(east[:6] + '.' + east[6:]), float(north[:6] + '.' + north[6:]) 
            """elif len(east) == 6 and len(north) == 5:
                return float(east), float(north.ljust(6, '0')) # pad north to six characters with zeroes on the right (least significant)
            elif len(east) == 5 and len(north) == 6:
                return float(east.ljust(6, '0')), float(north) # pad east to six characters with zeroes on the right (least significant)"""
        return float(east), float(north)
        
def lnglat_from_applic(applic):
    if 'latitude' in applic and 'longitude' in applic:
        result = lnglat_from_app_lnglat(applic)# any directly specified longitude/latitude values get priority
        if result:
            return result
    return lnglat_from_app_eastnorth(applic)
        
def lnglat_from_app_lnglat(applic):
    # try to use valid latitude and longitude values if they exist
    try:
        lat = float(applic['latitude'])
        lng = float(applic['longitude'])
        if lng > MINUKLNG and lng < MAXUKLNG and lat > MINUKLAT and lat < MAXUKLAT:
            return lng, lat
    except:
        pass
    return None
                 
def lnglat_from_app_eastnorth(applic):
    # try to get valid lat and lng from easting, northing or OS grid ref values if they exist
    # NB need postcode information to say whether it is on the Irish or GB grids
    east = None; north = None
    pc = applic.get('postcode')
    url = applic.get('url')
    if (pc and pc.startswith('BT')) or (url and 'planningni.gov.uk/' in url): 
        grid = 'IE' # Eire and Northern Ireland easting/northing values are relative to Irish grid
    else:
        grid = 'GB'
    try:
        if applic.get('easting') and applic.get('northing'):
            east, north = eastnorth_float(applic['easting'], applic['northing'])
        elif applic.get('os_grid_ref'):
            if ',' in applic['os_grid_ref']: # sometimes easting, northing are put in the os_grid_ref field by mistake
                coords = applic['os_grid_ref'].split(',')
                east, north = eastnorth_float(coords[0], coords[1])
            else:
                east, north = osgb_to_eastnorth(applic['os_grid_ref'])
        if grid == 'GB':
            if east <= 0.0 or north <= 0.0 or east >= MAXEAST or north >= MAXNORTH:
                # sanity check - make sure the values are within the GB grid range
                return None
            elif east <= LOWEAST and north <= LOWNORTH: # in lower left SW Atlantic
                return None
        elif grid == 'IE':
            if east <= 0.0 or north <= 0.0 or east >= MAXEAST_IE or north >= MAXNORTH_IE:
                # sanity check - make sure the values are within the IE grid range
                return None
            elif east <= LOWEAST_IE and north <= LOWNORTH_IE: # in lower left SW Atlantic
                return None
    except:
        return None
    if not east and not north:
        return None
    try: 
        result = os_easting_northing_to_latlng(east, north, grid)
        lat = float(result[0])
        lng = float(result[1])
        if lng > MINUKLNG and lng < MAXUKLNG and lat > MINUKLAT and lat < MAXUKLAT:
            # sanity check - make sure the converted values are within the UK/Irish rough lat lon range
            return lng, lat
    except:
        pass
    return None
    
def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points on the earth
    """
    R = 6372.8 # Earth radius in kilometers
    
    dLat = radians(lat2 - lat1)
    dLon = radians(lon2 - lon1)
    lat1 = radians(lat1)
    lat2 = radians(lat2)
    
    a = sin(dLat/2)**2 + cos(lat1)*cos(lat2)*sin(dLon/2)**2
    c = 2*asin(sqrt(a))
    
    return R * c
    
def great_circle(lon, lat, radius, npoints=32):
    """
    Return a list of points representing a great circle around a point
    see http://stackoverflow.com/questions/6753099/google-maps-v3-drawing-circle-using-haversine-formula-and-polyline
    """
    if npoints < 4:
        return None
    R = 6372.8 # Earth radius in kilometers
    
    cLat = (radius / R) * (180.0 / pi)
    cLng = cLat / cos(lat * pi / 180.0)
    
    points = []
    for i in range(npoints): # 360 deg = 2pi radians
        degrees = 360.0 * i / npoints
        theta = degrees * pi / 180.0 # convert to radians
        circleY = lon + (cLng * cos(theta))          
        circleX = lat + (cLat * sin(theta))
        points.append( [ circleY, circleX ] )
        
    points.append (points[0]) # polygon so add final point same as first
    return points
    

