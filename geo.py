import cenpy as c
import pandas as pd
import cenpy.tiger as tiger
import requests
import numpy as np
import pysal
import math
import pyproj

conn = c.base.Connection('DecennialSF12010')
conn.set_mapservice('tigerWMS_Census2010')

def cached_query(state_fips, geo_unit, cols=[], is_map=False, county=''):
    file_name = 'census_state_' + state_fips + '_' + geo_unit
    if geo_unit == 'tract':
        file_name += '_' + county
    if is_map:
        file_name += '.map'
    file_name += '.pkl'

    try:
        data = pd.read_pickle(file_name)
    except:
        if is_map:
            layers = {
                'county': 100,
                'place': 36,
                'tract': 14
                }
            w = 'STATE=' + state_fips
            if geo_unit == 'tract':
               w = 'county=' + county 
            data = conn.mapservice.query(layer=layers[geo_unit], where=w)
        else:
            g_filter = { 'state': state_fips }
            #if geo_unit == 'tract':
            #    g_filter['county'] = county
            data = conn.query(cols,
                              geo_unit = geo_unit + ':*',
                              geo_filter = g_filter)
    data.to_pickle(file_name)
    return data

def get_place_data(state_fips):
    population_age = conn.varslike('P01200[01234][0-9]', engine='fnmatch')
    races = conn.varslike('H006000[2-8]', engine='fnmatch')
    household = conn.varslike('H013000[2-8]', engine='fnmatch')
    other_vars = ['NAME','H0030001','H0030002','H0030003',
                  'H0040002','H0040003','H0040004',
                  'H0110001','H0110002','H0110003','H0110004',
                  'H0050006','H0050007', 'H0070001']
    cols = population_age + races + household + other_vars

    data = cached_query(state_fips, 'place', cols=cols)
    geodata = cached_query(state_fips, 'place', is_map=True)
    
    d = pd.merge(data, geodata, left_on='place', right_on='PLACE', how='outer')

    # find only non-NaN entries (are the NaNs bugs??)
    d = d.query('CENTLAT == CENTLAT')

    return d

def get_tract_data(state_fips, county):
    cols = ['NAME', 'H0030001','H0030002','H0030003']
    data = cached_query(state_fips, 'tract', cols=cols)
    geodata = cached_query(state_fips, 'tract', is_map=True, county=county)
    
    d = pd.merge(data, geodata, left_on='tract', right_on='TRACT', how='outer')

    d = d.query('CENTLAT == CENTLAT')

    return d

def get_county_data(state_fips):
    cols = ['NAME']
 
    data = cached_query(state_fips, 'county', cols=cols)
    geodata = cached_query(state_fips, 'county', is_map=True)

    d = pd.merge(data, geodata, left_on='county', right_on='COUNTY', how='outer')
    
    return d

def find_near(d, lat, lon, how_near):
    # sort by distance to here
    lat_delta = d.CENTLAT.apply(float)-lat
    lon_delta = d.CENTLON.apply(float)-lon
    d['dist'] = (lat_delta.apply(math.pow, args=[2])+
                 lon_delta.apply(math.pow, args=[2])).apply(math.sqrt)
    d = d.sort_values(by=['dist'])
    
    # find places near here
    lat_near = abs(d.CENTLAT.apply(float)-lat)<how_near
    lon_near = abs(d.CENTLON.apply(float)-lon)<how_near
    near = d[lat_near & lon_near]

    return near

def find_here(near, lat, lon):
    # convert projections
    inProj = pyproj.Proj(init='epsg:4326')
    outProj = pyproj.Proj(init='epsg:3857')
    census_coord = pyproj.transform(inProj,outProj,lon,lat)

    # search for geometry that contains location
    # TODO: optimize such that search stops after first 'here' is found
    here = near[near.geometry.apply(lambda x: x.contains_point(census_coord))]

    return here

def get_data(lat, lon):
    r = requests.get('https://geo.fcc.gov/api/census/area',
                     params={'format':'json', 'lat':lat, 'lon': lon})
    fcc_data = r.json()['results'][0]

    counties = get_county_data(fcc_data['state_fips'])
    counties_near = find_near(counties, lat, lon, 1)
    county_here = find_here(counties_near, lat, lon)
    
    places = get_place_data(fcc_data['state_fips'])
    places_near = find_near(places, lat, lon, 0.1)
    place_here = find_here(places_near, lat, lon)
    
    data = {}
    if len(county_here.index) > 0:
        here = county_here.iloc[0]
        data['county'] = {
            'name': here.BASENAME,
            'population': here.POP100
        }
        tracts = get_tract_data(fcc_data['state_fips'], county=here.COUNTY)
        tracts_near = find_near(tracts, lat, lon, 0.05)
        tract_here = find_here(tracts_near, lat, lon)
        if len(tract_here.index) > 0:
            here = tract_here.iloc[0]
            data['tract'] = {
                'name': here.BASENAME,
                'population': here.POP100
            }
        
    if len(place_here.index) > 0:
        here = place_here.iloc[0]
        print(here)
        data['place'] = {
            'name': here.BASENAME,
            'population': {
                'total': here.POP100,
                'male': {
                    'total': here.P0120002,
                    'under-5': here.P0120003,
                    '5-9': here.P0120004,
                    '10-14': here.P0120005,
                    '15-17': here.P0120006,
                    '18-19': here.P0120007,
                    '20': here.P0120008,
                    '21': here.P0120009,
                    '22-24': here.P0120010,
                    '25-29': here.P0120011,
                    '30-34': here.P0120012,
                    '35-39': here.P0120013,
                    '40-44': here.P0120014,
                    '45-49': here.P0120015,
                    '50-54': here.P0120016,
                    '55-59': here.P0120017,
                    '60-61': here.P0120018,
                    '62-64': here.P0120019,
                    '65-66': here.P0120020,
                    '67-69': here.P0120021,
                    '70-74': here.P0120022,
                    '75-79': here.P0120023,
                    '80-84': here.P0120024,
                    '85+': here.P0120025,
                },
                'female': {
                    'total': here.P0120026,
                    'under-5': here.P0120027,
                    '5-9': here.P0120028,
                    '10-14': here.P0120029,
                    '15-17': here.P0120030,
                    '18-19': here.P0120031,
                    '20': here.P0120032,
                    '21': here.P0120033,
                    '22-24': here.P0120034,
                    '25-29': here.P0120035,
                    '30-34': here.P0120036,
                    '35-39': here.P0120037,
                    '40-44': here.P0120038,
                    '45-49': here.P0120039,
                    '50-54': here.P0120040,
                    '55-59': here.P0120041,
                    '60-61': here.P0120042,
                    '62-64': here.P0120043,
                    '65-66': here.P0120044,
                    '67-69': here.P0120045,
                    '70-74': here.P0120046,
                    '75-79': here.P0120047,
                    '80-84': here.P0120048,
                    '85+': here.P0120049,
                },
            }, 
            'houses': here.H0030001,
            'occupied': {
                'total': {
                    'houses': here.H0030003,
                    'people': here.H0110001
                },
                'mortgage': {
                    'houses': here.H0040002,
                    'people': here.H0110002
                },
                'free-clear': {
                    'houses': here.H0040003,
                    'people': here.H0110003
                },
                'renters': {
                    'houses': here.H0040004,
                    'people': here.H0110004
                },
                'races': {
                    'white': here.H0060002,
                    'black': here.H0060003,
                    'asian': here.H0060004,
                    'islander': here.H0060005,
                    'native': here.H0060006,
                    'other': here.H0060007,
                    'mixed': here.H0060008,
                    'hispanic': here.H0070001,
                },
                'household-size-houses': {
                    '1': here.H0130002,
                    '2': here.H0130003,
                    '3': here.H0130004,
                    '4': here.H0130005,
                    '5': here.H0130006,
                    '6': here.H0130007,
                    '7+': here.H0130008,
                }
            },
            'vacant': {
                'total': here.H0030002,
                'seasonal': here.H0050006,
                'migrants': here.H0050007,
            }
        }

    return data

if __name__ == "__main__":
    # CDP Polygon 
    lat = 38.6950677
    lon = -121.2273321
    # Incorporated Polygon with holes 
    #lat=38.7937531
    #lon=-121.2420338
    print(get_data(lat,lon))
    #print(get_tract_data('06'))