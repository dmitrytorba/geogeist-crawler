import geo
import psycopg2
import json
import cenpy

conn = psycopg2.connect(user='geogeist', password='password',
                        host='localhost', port='5432')

def load_counties():
	state_fips = '06'
	dt = geo.get_county_data(state_fips)

	cur = conn.cursor()

	for index, row in dt.iterrows():
		geog = row.geometry.__geo_interface__


		geog["crs"] = {
			"type": "name",
			"properties": {
				"name": "EPSG:3857"
			}
		}
		geog = json.dumps(geog)
		cur.execute("INSERT into counties (state, name, geog) VALUES (%s, %s, ST_Multi(ST_Transform(ST_GeomFromGeoJSON(%s),4326)))",
			(state_fips, row.BASENAME, geog))
	#cur.execute("SELECT ")

	conn.commit()
	cur.close()

def load_states():
	conn = cenpy.base.Connection('CBP2012')
	conn.set_mapservice('State_County')

	for i in range(1, 3): 
		geodata = conn.mapservice.query(layer=0, where='STATE=' + str(i))
		print(geodata.BASENAME)
		print(geodata.geometry)


def test_county():
	cur = conn.cursor()
	cur.execute("SELECT c.name FROM counties c WHERE ST_Covers(c.geog, 'SRID=4326;POINT(-121.2273314 38.6950877)'::geography)")
	print(cur.fetchone())
	conn.commit()
	cur.close()

load_counties()

conn.close()