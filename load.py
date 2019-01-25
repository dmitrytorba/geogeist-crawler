import geo
import psycopg2
import json
import cenpy
import us

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
		geog = row.geometry.__geo_interface__
		geog["crs"] = geo_info 
		geog = json.dumps(geog)
		cur.execute("INSERT into counties (state, name, geog) VALUES (%s, %s, ST_Multi(ST_Transform(ST_GeomFromGeoJSON(%s),4326)))",
			(state_fips, row.BASENAME, geog))

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

load_states()
load_counties()

conn.close()