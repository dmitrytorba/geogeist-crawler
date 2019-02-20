import psycopg2
import os
import json
import polyline
import urllib.request

conn = psycopg2.connect(user='geogeist', password='password',
                        host='localhost', port='5432')

MAP_KEY = os.environ['MAP_KEY']

def tracts():
	cur = conn.cursor()
	cur.execute("SELECT name,ST_AsGeoJSON(geog),ST_AsGeoJSON(centroid),state FROM tracts limit 1;")
	tract = cur.fetchone()
	name = tract[0]
	geog = json.loads(tract[1])
	centroid = json.loads(tract[2])["coordinates"]
	state = tract[3]
	# TODO: handle multipolygons
	coords = geog["coordinates"][0][0]
	poly = polyline.encode(coords)
	print(coords)

	url = "https://maps.googleapis.com/maps/api/staticmap?size=400x400&center=%s,%s&zoom=14&path=%senc:%s&key=%s" % (centroid[0],centroid[1],"fillcolor:0xAA000033%7Ccolor:0xFFFFFF00%7C",poly,MAP_KEY)
	filename = "static/tract_map_%s-%s.png" % (state, name)
	urllib.request.urlretrieve(url, filename)
	print(url)
	conn.commit()
	cur.close()


tracts()
conn.close()