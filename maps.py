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
	cur.execute("SELECT name,ST_AsGeoJSON(geog),ST_AsGeoJSON(centroid),state,data,gid FROM tracts;")
	rows = cur.fetchall()
	for row in rows:
		name = row[0]
		geog = json.loads(row[1])
		centroid = json.loads(row[2])["coordinates"]
		state = row[3]
		data_json = row[4]
		gid = row[5]
		# TODO: handle multipolygons
		coords = geog["coordinates"][0][0]
		for item in coords:
			item.reverse()
		poly = polyline.encode(coords)

		url = "https://maps.googleapis.com/maps/api/staticmap?size=400x400&center=%s,%s&zoom=14&path=%senc:%s&key=%s" % (centroid[1],centroid[0],"fillcolor:0xAA000033%7Ccolor:0xFFFFFF00%7C",poly,MAP_KEY)
		filename = "static/tract_map_%s-%s.png" % (state, name)
		urllib.request.urlretrieve(url, filename)

		data_json['map'] = filename

		print(state + "-" + name)
		cur.execute("UPDATE tracts SET data = %s WHERE gid = %s", (json.dumps(data_json), gid))
	conn.commit()
	cur.close()


tracts()
conn.close()