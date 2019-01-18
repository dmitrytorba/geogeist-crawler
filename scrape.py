import geo
import psycopg2
import json

conn = psycopg2.connect(user='geogeist', password='password',
                        host='localhost', port='5432')

def insert_counties():
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

def get_county():
	cur = conn.cursor()
	cur.execute("SELECT c.name WHERE ST_Covers(c.geog, 'SRID=4326;POINT(-121.2273314 38.6950877)'::geography) FROM counties c")
	print(cur.fetchone())
	conn.commit()
	cur.close()

get_county()

conn.close()