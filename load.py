import geo
import psycopg2
import json
import cenpy
import us
import os

conn = psycopg2.connect(user='geogeist', password='password',
                        host='localhost', port='5432')

geo_info = {
	"type": "name",
	"properties": {
		"name": "EPSG:3857"
	}
}

def load_counties():
	state_fips = '06'
	dt = geo.get_county_data(state_fips)

	cur = conn.cursor()

	for index, row in dt.iterrows():
		print(row.BASENAME)
		geog = row.geometry.__geo_interface__
		geog["crs"] = geo_info 
		geog = json.dumps(geog)
		data_json = { 'county': geo.data_json(row) }
		geo.draw_chart(data_json, 'county', row.BASENAME, state_fips)
		f = open(data_json['county']['population']['chart'], 'rb')
		population_chart = f.read()
		f.close()
		f = open(data_json['county']['occupied']['race_chart'], 'rb')
		race_chart = f.read()
		f.close()
		f = open(data_json['county']['occupied']['finance_chart'], 'rb')
		finance_chart = f.read()
		f.close()
		f = open(data_json['county']['occupied']['household_chart'], 'rb')
		household_chart = f.read()
		f.close()
		query = "INSERT into counties (state, name, data, population_chart, race_chart, finance_chart, household_chart, geog)" + " VALUES (%s, %s, %s, %s, %s, %s, %s, ST_Multi(ST_Transform(ST_GeomFromGeoJSON(%s),4326)))"
		values = (state_fips, row.BASENAME, json.dumps(data_json), population_chart, race_chart, finance_chart, household_chart, geog)
		cur.execute(query, values)

	conn.commit()
	cur.close()

def load_states():
	gov = cenpy.base.Connection('CBP2012')
	gov.set_mapservice('State_County')
	
	cur = conn.cursor()
	for state in us.states.STATES:
		geodata = gov.mapservice.query(layer=0, where='STATE=' + state.fips).iloc[0]
		geog = geodata.geometry.__geo_interface__
		geog["crs"] = geo_info 
		geog = json.dumps(geog)
		print(geodata.BASENAME)
		cur.execute("INSERT into states (state, name, arealand, areawater, geog) VALUES (%s, %s, %s, %s, ST_Multi(ST_Transform(ST_GeomFromGeoJSON(%s),4326)))",
			(geodata.STATE, geodata.BASENAME, int(geodata.AREALAND), int(geodata.AREAWATER), geog))

	conn.commit()
	cur.close()

def test_county():
	cur = conn.cursor()
	cur.execute("SELECT c.name FROM counties c WHERE ST_Covers(c.geog, 'SRID=4326;POINT(-121.2273314 38.6950877)'::geography)")
	print(cur.fetchone())
	conn.commit()
	cur.close()


load_counties()

conn.close()