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

def cached_query(state_fips, cols=[], is_map=False):
    file_name = 'census_state_' + state_fips
    if is_map:
        file_name += '.map'
    file_name += '.pkl'

    try:
        data = pd.read_pickle(file_name)
    except:
        print('downloading census for state_fips='+state_fips)
        if is_map:
            data = conn.mapservice.query(layer=36,
                                         where='STATE='+state_fips)
        else:
            data = conn.query(cols,
                              geo_unit = 'place:*',
                              geo_filter = {'state':state_fips})
    data.to_pickle(file_name)
    return data

def get_data(lat, lon):
    r = requests.get('https://geo.fcc.gov/api/census/area',
                     params={'format':'json', 'lat':lat, 'lon': lon})
    fcc_data = r.json()['results'][0]

    cols = conn.varslike('H00[0123]*', engine='fnmatch')
    cols.append('NAME')

    data = cached_query(fcc_data['state_fips'], cols=cols)
    geodata = cached_query(fcc_data['state_fips'], is_map=True)
    
    d = pd.merge(data, geodata, left_on='place', right_on='PLACE', how='outer')

    # find only non-NaN entries (are the NaNs bugs??)
    d = d.query('CENTLAT == CENTLAT')

    # sort by distance to here
    lat_delta = d.CENTLAT.apply(float)-lat
    lon_delta = d.CENTLON.apply(float)-lon
    d['dist'] = (lat_delta.apply(math.pow, args=[2])+lon_delta.apply(math.pow, args=[2])).apply(math.sqrt)
    d = d.sort_values(by=['dist'])
    
    # find places near here
    how_near = 0.2
    lat_near = abs(d.CENTLAT.apply(float)-lat)<how_near
    lon_near = abs(d.CENTLON.apply(float)-lon)<how_near
    near = d[lat_near & lon_near]

    # convert projections
    inProj = pyproj.Proj(init='epsg:4326')
    outProj = pyproj.Proj(init='epsg:3857')
    census_coord = pyproj.transform(inProj,outProj,lon,lat)

    # search for geometry that contains location
    here = near[near.geometry.apply(lambda x: x.contains_point(census_coord))]

    data = {}
    if len(here.index) > 0:
        here = here.iloc[0]
        data['name'] = here.BASENAME
        data['population'] = here.POP100
    return data

if __name__ == "__main__":
    # CDP Polygon 
    #lat = 38.6950677
    #lon = -121.2273321
    # Incorporated Polygon with holes 
    lat=38.7937531
    lon=-121.2420338
    print(get_data(lat,lon))
