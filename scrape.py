import geo
import psycopg2
import json

conn = psycopg2.connect(user='geogeist', password='password',
                        host='localhost', port='5432')

def insert_county():
	state_fips = '06'
	dt = geo.get_county_data(state_fips)
	alameda = dt.iloc[0]
	geog = alameda.geometry.__geo_interface__

	cur = conn.cursor()

	geog["crs"] = {
		"type": "name",
		"properties": {
			"name": "EPSG:3857"
		}
	}
	geog = json.dumps(geog)
	cur.execute("INSERT into counties (state, name, geog) VALUES (%s, %s, ST_Multi(ST_Transform(ST_GeomFromGeoJSON(%s),4326)))",
		(state_fips, alameda.BASENAME, geog))
	#cur.execute("SELECT ")

	conn.commit()
	cur.close()

def test_distance():
	cur = conn.cursor()
	cur.execute("SELECT ST_Distance('SRID=4326;POINT(-121.2273314 38.6950877)'::geography, c.geog) FROM counties c")
	print(cur.fetchone())
	conn.commit()
	cur.close()

test_distance()

conn.close()