import psycopg2
import os
import json
import polyline
import urllib.request
from urllib.error import HTTPError

conn = psycopg2.connect(user='geogeist', password=os.environ['DBPASS'],
						host='localhost', port='5432')

MAP_KEY = os.environ['MAP_KEY']
URL_MAX = 8192

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
		filename = "static/tract_map_%s-%s.png" % (state, name)
		if os.path.exists(filename):
			print('map already exists: ' + filename)
		else:
			# TODO: handle multipolygons
			coords = geog["coordinates"][0][0]
			for item in coords:
				item.reverse()
			poly = polyline.encode(coords)

			url = "https://maps.googleapis.com/maps/api/staticmap?size=400x400&center=%s,%s&zoom=14&path=%senc:%s&key=%s" % (centroid[1],centroid[0],"fillcolor:0xAA000033%7Ccolor:0xFFFFFF00%7C",poly,MAP_KEY)

			try:
				urllib.request.urlretrieve(url, filename)

				data_json['map'] = filename

				print("rendered: " + filename)
				cur.execute("UPDATE tracts SET data = %s WHERE gid = %s", (json.dumps(data_json), gid))
			except HTTPError as err:
				print("render failed: " + filename)

	conn.commit()
	cur.close()

def calc_zoom(area):
	if area > 50000000:
		zoom = '11'
	elif area > 10000000:
		zoom = '12'
	elif area > 3000000:
		zoom = '13'
	elif area > 1000000:
		zoom = '14'
	else:
		zoom = '15'
	return zoom

def places():
	cur = conn.cursor()
	cur.execute("SELECT name,ST_AsGeoJSON(geog),ST_AsGeoJSON(centroid),state,data,gid,area FROM places;")
	rows = cur.fetchall()
	for row in rows:
		name = row[0]
		geog = json.loads(row[1])
		centroid = json.loads(row[2])["coordinates"]
		state = row[3]
		data_json = row[4]
		gid = row[5]
		area = row[6]
		# TODO: handle multipolygons
		coords = geog["coordinates"][0][0]
		for item in coords:
			item.reverse()
		poly = polyline.encode(coords)
		zoom = calc_zoom(area)

		url = "https://maps.googleapis.com/maps/api/staticmap?size=400x400&center=%s,%s&zoom=%s&path=%senc:%s&key=%s" % (centroid[1],centroid[0],zoom,"fillcolor:0xAA000033%7Ccolor:0xFFFFFF00%7C",poly,MAP_KEY)
		if len(url) < URL_MAX:
			filename = "static/place_map_%s-%s.png" % (state, name)
			urllib.request.urlretrieve(url, filename)

			data_json['map'] = filename

			print(state + "-" + name)
			cur.execute("UPDATE places SET data = %s WHERE gid = %s", (json.dumps(data_json), gid))
		else:
			print("Failed (too big): " + state + "-" + name)
	conn.commit()
	cur.close()


def counties():
	cur = conn.cursor()
	cur.execute("SELECT name,ST_AsGeoJSON(geog),ST_AsGeoJSON(centroid),state,data,gid,area FROM counties;")
	rows = cur.fetchall()
	for row in rows:
		name = row[0]
		geog = json.loads(row[1])
		centroid = json.loads(row[2])["coordinates"]
		state = row[3]
		data_json = row[4]
		gid = row[5]
		area = row[6]
		# TODO: handle multipolygons
		coords = geog["coordinates"][0][0]
		for item in coords:
			item.reverse()
		poly = polyline.encode(coords)
		zoom = calc_zoom(area)

		url = "https://maps.googleapis.com/maps/api/staticmap?size=400x400&center=%s,%s&zoom=%s&path=%senc:%s&key=%s" % (centroid[1],centroid[0],zoom,"fillcolor:0xAA000033%7Ccolor:0xFFFFFF00%7C",poly,MAP_KEY)
		if len(url) < URL_MAX:
			filename = "static/county_map_%s-%s.png" % (state, name)
			urllib.request.urlretrieve(url, filename)

			data_json['map'] = filename

			print(state + "-" + name)
			cur.execute("UPDATE counties SET data = %s WHERE gid = %s", (json.dumps(data_json), gid))
		else:
			print("Failed (too big): " + state + "-" + name)
	conn.commit()
	cur.close()


tracts()
conn.close()