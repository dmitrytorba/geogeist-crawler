import matplotlib
matplotlib.use('Agg')
import cenpy as c
import pandas as pd
import cenpy.tiger as tiger
import requests
import numpy as np
import pysal
import math
import pyproj
import os
import urllib3.exceptions
import time

conn = c.base.Connection('DECENNIALSF12010')
conn.set_mapservice('tigerWMS_Census2010')
apikey = os.environ['APIKEY']

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
                'incorp': 34,
                'cdp': 36,
                'tract': 14
                }
            w = 'STATE=' + state_fips
            if geo_unit == 'tract':
               w = 'county=' + county
            try: 
                data = conn.mapservice.query(layer=layers[geo_unit], where=w)
            except HTTPError as err:
                print('map server query returns error ' + err.code)
                if err.code == 500:
                    print('this map needs re-download: ' + w)
                    # throttle any subsequent requests
                    time.sleep(120)
                else:
                    raise
        else:
            g_filter = { 'state': state_fips }
            if geo_unit == 'tract':
                g_filter['county'] = county
            try:
                data = conn.query(cols,
                                  geo_unit = geo_unit + ':*',
                                  geo_filter = g_filter,
                                  apikey = apikey)
            except HTTPError as err:
                print('data server query returns error ' + err.code)
                if err.code == 500:
                    print('this data needs re-download: ' + w)
                    # throttle any subsequent requests
                    time.sleep(120)
                else:
                    raise
    data.to_pickle(file_name)
    return data

def get_cols():
    population_age = conn.varslike('P0120[01234][0-9]', engine='fnmatch')
    races = conn.varslike('H00600[2-8]', engine='fnmatch')
    household = conn.varslike('H01300[2-8]', engine='fnmatch')
    other_vars = ['LSAD_NAME','H003001','H003002','H003003',
                  'H004002','H004003','H004004',
                  'H011001','H011002','H011003','H011004',
                  'H005006','H005007', 'H007001', 'P001001']
    cols = population_age + races + household + other_vars
    return cols

def get_place_data(state_fips):
    data = cached_query(state_fips, 'place', cols=get_cols())
    geodata = cached_query(state_fips, 'cdp', is_map=True)
    geodata = geodata.append(cached_query(state_fips, 'incorp', is_map=True))

    d = pd.merge(data, geodata, left_on='place', right_on='PLACE', how='outer')

    # find only non-NaN entries (are the NaNs bugs??)
    d = d.query('CENTLAT == CENTLAT')

    return d

def get_tract_data(state_fips, county):
    data = cached_query(state_fips, 'tract', cols=get_cols(), county=county)
    geodata = cached_query(state_fips, 'tract', is_map=True, county=county)
    
    d = pd.merge(data, geodata, left_on='tract', right_on='TRACT', how='outer')

    d = d.query('CENTLAT == CENTLAT')

    return d

def get_county_data(state_fips):
    cols = ['NAME']
 
    data = cached_query(state_fips, 'county', cols=get_cols())
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

# https://api.census.gov/data/2010/dec/sf1/variables.html
def data_json(here):
    here = here.fillna(0)
    return {
            'name': here.LSAD_NAME,
            'population': {
                'total': here.P001001,
                'total-male': here.P012002,
                'total-female': here.P012026,
                'male': {
                    ' 0-5': here.P012003,
                    ' 5-9': here.P012004,
                    '10-14': here.P012005,
                    '15-19': int(here.P012006) + int(here.P012007),
                    '20-24': int(here.P012008) + int(here.P012009) + int(here.P012010),
                    '25-29': here.P012011,
                    '30-34': here.P012012,
                    '35-39': here.P012013,
                    '40-44': here.P012014,
                    '45-49': here.P012015,
                    '50-54': here.P012016,
                    '55-59': here.P012017,
                    '60-64': int(here.P012018) + int(here.P012019),
                    '65-69': int(here.P012020) + int(here.P012021),
                    '70-74': here.P012022,
                    '75-79': here.P012023,
                    '80-84': here.P012024,
                    '85+': here.P012025,
                },
                'female': {
                    ' 0-5': here.P012027,
                    ' 5-9': here.P012028,
                    '10-14': here.P012029,
                    '15-19': int(here.P012030) + int(here.P012031),
                    '20-24': int(here.P012032) + int(here.P012033) + int(here.P012034),
                    '25-29': here.P012035,
                    '30-34': here.P012036,
                    '35-39': here.P012037,
                    '40-44': here.P012038,
                    '45-49': here.P012039,
                    '50-54': here.P012040,
                    '55-59': here.P012041,
                    '60-64': int(here.P012042) + int(here.P012043),
                    '65-69': int(here.P012044) + int(here.P012045),
                    '70-74': here.P012046,
                    '75-79': here.P012047,
                    '80-84': here.P012048,
                    '85+': here.P012049,
                },
            }, 
            'houses': here.H003001,
            'occupied': {
                'total': {
                    'houses': here.H003003,
                    'people': here.H011001
                },
                'finance': {
                    'people': {
                        'mortgage': here.H011002,
                        'free-and-clear': here.H011003,
                        'renting': here.H011004

                    }, 
                    'houses': {
                        'mortgage': here.H004002,
                        'free-and-clear': here.H004003,
                        'renting': here.H004004
                    } 
                },
                'races': {
                    'white': here.H006002,
                    'black': here.H006003,
                    'asian': here.H006004,
                    'islander': here.H006005,
                    'native': here.H006006,
                    'other': here.H006007,
                    'mixed': here.H006008,
                    'hispanic': here.H007001,
                },
                'household-size-houses': {
                    '1': here.H013002,
                    '2': here.H013003,
                    '3': here.H013004,
                    '4': here.H013005,
                    '5': here.H013006,
                    '6': here.H013007,
                    '7+': here.H013008,
                }
            },
            'vacant': {
                'total': here.H003002,
                'seasonal': here.H005006,
                'migrants': here.H005007,
            }
        }
def get_data(lat, lon):
    print('get data: ' + str(lat) + ', ' + str(lon))
    r = requests.get('https://geo.fcc.gov/api/census/area',
                     params={'format':'json', 'lat':lat, 'lon': lon})
    if r.status_code == requests.codes.ok:
        fcc_data = r.json()['results'][0]
        state_fips = fcc_data['state_fips']
    else:
        print('geo.fcc.gov error')
        state_fips = '06'

    counties = get_county_data(state_fips)
    counties_near = find_near(counties, lat, lon, 1)
    county_here = find_here(counties_near, lat, lon)
    
    places = get_place_data(state_fips)
    places_near = find_near(places, lat, lon, 0.1)
    place_here = find_here(places_near, lat, lon)
    
    data = {}
    if len(county_here.index) > 0:
        here = county_here.iloc[0]
        data['county'] = data_json(here)
        draw_chart(data['county'], 'county', here.COUNTY, state_fips)
        # tracts need county filter to download without crashing
        tracts = get_tract_data(state_fips, county=here.COUNTY)
        tracts_near = find_near(tracts, lat, lon, 0.05)
        tract_here = find_here(tracts_near, lat, lon)
        if len(tract_here.index) > 0:
            here = tract_here.iloc[0]
            data['tract'] = data_json(here)
            draw_chart(data['tract'], 'tract', here.tract, state_fips)
        
    if len(place_here.index) > 0:
        here = place_here.iloc[0]
        data['place'] = data_json(here)
        draw_chart(data['place'], 'place', here.place, state_fips)

    return data

def draw_chart(data, res, code, state_fips):
    path = "static/population_" + state_fips + "_" + res + "_" + code + ".png"
    male_pop = data['population']['male']
    female_pop = data['population']['female']
    df = pd.DataFrame({'Male': male_pop, 'Female': female_pop}).astype(int)
    plot = df.plot(kind='bar', title='Population Age and Gender')
    fig = plot.get_figure()
    fig.savefig(path)
    data['population']['chart'] = path

    occupied = data['occupied']

    path = "static/race_" + state_fips + "_" + res + "_" + code + ".png"
    df = pd.DataFrame({ '': occupied['races'] }).astype(int)
    plot = df.plot.pie(y=0, labels=None, title='Householders', autopct='%1.0f%%')
    fig = plot.get_figure()
    fig.savefig(path)
    occupied['race_chart'] = path

    path = "static/household_size_" + state_fips + "_" + res + "_" + code + ".png"
    df = pd.DataFrame({ '': occupied['household-size-houses'] }).astype(int)
    plot = df.plot(kind='bar', title='Household Size', legend=None)
    fig = plot.get_figure()
    fig.savefig(path)
    occupied['household_chart'] = path

    path = "static/finance_" + state_fips + "_" + res + "_" + code + ".png"
    df = pd.DataFrame({ '': occupied['finance']['houses'] }).astype(int)
    plot = df.plot.pie(y=0, labels=None, title='Home Ownership', autopct='%1.0f%%')
    fig = plot.get_figure()                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               
    fig.savefig(path)
    occupied['finance_chart'] = path

    matplotlib.pyplot.close('all')
  
if __name__ == "__main__":
    # CDP Polygon 
    #lat = 38.6950677
    #lon = -121.2273321
    # Incorporated Polygon with holes 
    lat=38.7937531
    lon=-121.2420338
    print(get_data(lat,lon))
    #print(get_tract_data('06'))
