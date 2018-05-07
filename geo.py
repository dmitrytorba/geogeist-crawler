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

def cached_query(state_fips, geo_unit, cols=[], is_map=False):
    file_name = 'census_state_' + state_fips + '_' + geo_unit
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
            data = conn.mapservice.query(layer=layers[geo_unit],
                                         where='STATE='+state_fips)
        else:
            data = conn.query(cols,
                              geo_unit = geo_unit + ':*',
                              geo_filter = {'state':state_fips})
    data.to_pickle(file_name)
    return data

def get_place_data(state_fips):
    cols = conn.varslike('H00[0123]*', engine='fnmatch')
    cols.append('NAME')

    data = cached_query(state_fips, 'place', cols=cols)
    geodata = cached_query(state_fips, 'place', is_map=True)
    
    d = pd.merge(data, geodata, left_on='place', right_on='PLACE', how='outer')

    # find only non-NaN entries (are the NaNs bugs??)
    d = d.query('CENTLAT == CENTLAT')

    return d

def get_tract_data(state_fips):
    cols = conn.varslike('H00[0123]*', engine='fnmatch')
    cols.append('NAME')

    data = cached_query(state_fips, 'tract', cols=cols)
    geodata = cached_query(state_fips, 'tract', is_map=True)
    
    return data, geodata

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


    if len(place_here.index) > 0:
        here = place_here.iloc[0]
        data['place'] = {
            'name': here.BASENAME,
            'population': here.POP100
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
