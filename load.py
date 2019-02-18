import geo
import psycopg2
import json
import cenpy
import us
import os
import pandas as pd

conn = psycopg2.connect(user='geogeist', password='password',
                        host='localhost', port='5432')

geo_info = {
	"type": "name",
	"properties": {
		"name": "EPSG:3857"
	}
}

def load_tracts(state_fips, county):
	print(county)
	dt = geo.get_tract_data(state_fips, county)
	cur = conn.cursor()
	for index, row in dt.iterrows():
		print(row.TRACT)
		geog = row.geometry.__geo_interface__
		geog["crs"] = geo_info 
		geog = json.dumps(geog)
		
		data_json = geo.data_json(row)
		geo.draw_chart(data_json, 'tract', row.TRACT, state_fips)

		query = "INSERT into tracts (state, county, name, data, geog)" + " VALUES (%s, %s, %s, %s, (ST_Multi(ST_Transform(ST_GeomFromGeoJSON(%s),4326))))"
		values = (state_fips, county, row.TRACT, json.dumps(data_json), geog)
		cur.execute(query, values)

	conn.commit()
	cur.close()

def load_places(state_fips):
	dt = geo.get_place_data(state_fips)

	cur = conn.cursor()

	for index, row in dt.iterrows():
		print(row.LSAD_NAME)
		geog = row.geometry.__geo_interface__
		geog["crs"] = geo_info 
		geog = json.dumps(geog)

		data_json = geo.data_json(row)
		geo.draw_chart(data_json, 'place', row.LSAD_NAME, state_fips)
		
		query = "INSERT into places (state, name, data, geog)" + " VALUES (%s, %s, %s, ST_Force2D(ST_Multi(ST_Transform(ST_GeomFromGeoJSON(%s),4326))))"
		values = (state_fips, row.LSAD_NAME, json.dumps(data_json), geog)
		cur.execute(query, values)

	conn.commit()
	cur.close()

def load_counties(state_fips):
	dt = geo.get_county_data(state_fips)

	cur = conn.cursor()

	for index, row in dt.iterrows():
		print(row.BASENAME)
		geog = row.geometry.__geo_interface__
		geog["crs"] = geo_info 
		geog = json.dumps(geog)

		data_json = geo.data_json(row)
		geo.draw_chart(data_json, 'county', row.BASENAME, state_fips)
	
		query = "INSERT into counties (state, county, name, data, geog)" + " VALUES (%s, %s, %s, %s, ST_Force2D(ST_Multi(ST_Transform(ST_GeomFromGeoJSON(%s),4326))))"
		values = (state_fips, row.COUNTY, row.BASENAME, json.dumps(data_json), geog)
		cur.execute(query, values)
		conn.commit()
		load_tracts(state_fips, row.COUNTY)


	cur.close()

def load_states():
	cnx = cenpy.base.Connection('DECENNIALSF12010')
	cnx.set_mapservice('State_County')

	data = cnx.query(geo.get_cols(), geo_unit = 'state:*')
	geodata = cnx.mapservice.query(layer=0, where='state is not null')
	dt = pd.merge(data, geodata, left_on='state', right_on='STATE', how='outer')
	cur = conn.cursor()

	for index, row in dt.iterrows():
		print(row.BASENAME)
		geog = row.geometry.__geo_interface__
		geog["crs"] = geo_info 
		geog = json.dumps(geog)

		data_json = geo.data_json(row)
		geo.draw_chart(data_json, 'state', row.BASENAME, row.STATE)

		query = "INSERT into states (state, name, data, geog)" + " VALUES (%s, %s, %s, ST_Force2D(ST_Multi(ST_Transform(ST_GeomFromGeoJSON(%s),4326))))"
		values = (row.STATE, row.BASENAME, json.dumps(data_json), geog)
		cur.execute(query, values)

	conn.commit()
	cur.close()

def test_county():
	cur = conn.cursor()
	cur.execute("SELECT c.name FROM counties c WHERE ST_Covers(c.geog, 'SRID=4326;POINT(-121.2273314 38.6950877)'::geography)")
	print(cur.fetchone())
	conn.commit()
	cur.close()


#load_states()
#load_tracts('06', '067')
load_counties('06')
#load_places('06')

conn.close()