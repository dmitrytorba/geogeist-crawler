import cenpy as c
import pandas as pd
import cenpy.tiger as tiger
import requests
import numpy as np
import pysal
import math
import pyproj

def get_data(lat, lon):
    r = requests.get('https://geo.fcc.gov/api/census/area',
                     params={'format':'json', 'lat':lat, 'lon': lon})
    fcc_data = r.json()['results'][0]

    conn = c.base.Connection('DecennialSF12010')
    conn.set_mapservice('tigerWMS_Census2010')

    cols = conn.varslike('H00[0123]*', engine='fnmatch')
    cols.append('NAME')

    file_name = 'census_data_state_' + fcc_data['state_fips'] + '.pkl'
    try:
        data = pd.read_pickle(file_name)
    except:
        print('downloading census for state_fips=' + fcc_data['state_fips'])
        data = conn.query(cols,
                      geo_unit = 'place:*',
                      geo_filter = {'state':fcc_data['state_fips']})
    data.to_pickle(file_name)
    
    file_name = 'census_geodata_state_' + fcc_data['state_fips'] + '.pkl'
    try:
        geodata = pd.read_pickle(file_name)
    except:
        print('downloading geodata for state_fips=' + fcc_data['state_fips'])
        geodata = conn.mapservice.query(layer=36, where='STATE = '+fcc_data['state_fips'])
        geodata.to_pickle(file_name)
    
    d = pd.merge(data, geodata, left_on='place', right_on='PLACE', how='outer')

    # find only non-NaN entries (are the NaNs bugs??)
    d = d.query('CENTLAT == CENTLAT')
    
    lat_delta = d.CENTLAT.apply(float)-lat
    lon_delta = d.CENTLON.apply(float)-lon
    d['dist'] = (lat_delta.apply(math.pow, args=[2])+lon_delta.apply(math.pow, args=[2])).apply(math.sqrt)
    d = d.sort_values(by=['dist'])
    
    here = d.iloc[0]
    inProj = pyproj.Proj(init='epsg:4326')
    outProj = pyproj.Proj(init='epsg:3857')
    census_coord = pyproj.transform(inProj,outProj,lon,lat)
    if here.geometry.contains_point(census_coord):
        print('found!')

    # find places near here
    how_near = 0.2
    lat_near = abs(d.CENTLAT.apply(float)-lat)<how_near
    lon_near = abs(d.CENTLON.apply(float)-lon)<how_near
    near = d[lat_near & lon_near]

    # here = d[near.geometry.contains_point((lat, lon))]
    
    # near.geometry.apply(pysal.cg.shapes.Polygon.contains_point, args=[(lat,lon)])

    print(here)
    data = {}
    data['name'] = here.BASENAME
    data['population'] = here.POP100
    return data

if __name__ == "__main__":
    lat = 38.6950677
    lon = -121.2273321
    print(get_data(lat,lon))
