import geo
import psycopg2
import json
import cenpy
import us
import os
import pandas as pd
import click

conn = psycopg2.connect(user='geogeist', password=os.environ['DBPASS'],
                        host='localhost', port='5432')

geo_info = {
	"type": "name",
	"properties": {
		"name": "EPSG:3857"
	}
}

@click.group()
def cli():
    pass

@click.command()
@click.option('--state', help='State FIPS code')
@click.option('--county', help='County code')
def tracts(state, county):
	dt = geo.get_tract_data(state, county)
	cur = conn.cursor()
	for index, row in dt.iterrows():
		print(row.STATE + "-" + row.TRACT)
		geog = row.geometry.__geo_interface__
		geog["crs"] = geo_info 
		geog = json.dumps(geog)
		centroid = "SRID=4326;POINT(" + row.CENTLON.replace("+", "") + " " + row.CENTLAT.replace("+", "") + ")"
		
		data_json = geo.data_json(row)
		geo.draw_chart(data_json, 'tract', row.TRACT, state)

		query = "INSERT into tracts (state, county, name, data, centroid, objid, area, geog) VALUES (%s, %s, %s, %s, %s, %s, %s, ST_Multi(ST_Transform(ST_GeomFromGeoJSON(%s),4326)))"
		values = (row.STATE, row.COUNTY, row.TRACT, json.dumps(data_json), centroid, row.OBJECTID, row.AREALAND, geog)

		cur.execute(query, values)

		conn.commit()
	cur.close()

@click.command()
@click.option('--state', help='State FIPS code')
def places(state):
	dt = geo.get_place_data(state)

	cur = conn.cursor()

	for index, row in dt.iterrows():
		print(row.LSAD_NAME)
		geog = row.geometry.__geo_interface__
		geog["crs"] = geo_info 
		geog = json.dumps(geog)
		centroid = "SRID=4326;POINT(" + row.CENTLON.replace("+", "") + " " + row.CENTLAT.replace("+", "") + ")"

		data_json = geo.data_json(row)
		geo.draw_chart(data_json, 'place', row.LSAD_NAME, state)
		
		query = "INSERT into places (state, name, data, centroid, area, geog)" + " VALUES (%s, %s, %s, %s, %s, ST_Force2D(ST_Multi(ST_Transform(ST_GeomFromGeoJSON(%s),4326))))"
		values = (row.STATE, row.LSAD_NAME, json.dumps(data_json), centroid, row.AREALAND, geog)
		cur.execute(query, values)

	conn.commit()
	cur.close()

@click.command()
@click.option('--state', help='State FIPS code')
@click.option('--load-tracts', default=False, help='Load tracts from each county')
def counties(state, load_tracts):
	print('Loading counties from state ' + state)
	dt = geo.get_county_data(state)

	cur = conn.cursor()

	for index, row in dt.iterrows():
		print(row.BASENAME)
		geog = row.geometry.__geo_interface__
		geog["crs"] = geo_info 
		geog = json.dumps(geog)
		centroid = "SRID=4326;POINT(" + row.CENTLON.replace("+", "") + " " + row.CENTLAT.replace("+", "") + ")"

		data_json = geo.data_json(row)
		geo.draw_chart(data_json, 'county', row.BASENAME, state)
	
		query = """INSERT into counties (state, county, name, data, centroid, area, geog)
					VALUES (%s, %s, %s, %s, %s, %s, ST_Force2D(ST_Multi(ST_Transform(ST_GeomFromGeoJSON(%s),4326))))"""
		values = (row.STATE, row.COUNTY, row.BASENAME, json.dumps(data_json), centroid, row.AREALAND, geog)
		cur.execute(query, values)
		conn.commit()
		if load_tracts:
			tracts(state, row.COUNTY)


	cur.close()

@click.command()
@click.option('--load-counties', default=False, help='Load counties from each state')
@click.option('--load-tracts', default=False, help='Load tracts from each county')
def states(load_counties, load_tracts):
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
		centroid = "SRID=4326;POINT(" + row.CENTLON.replace("+", "") + " " + row.CENTLAT.replace("+", "") + ")"

		data_json = geo.data_json(row)
		geo.draw_chart(data_json, 'state', row.BASENAME, row.STATE)

		query = """INSERT into states (state, name, data, centroid, area, geog)
					VALUES (%s, %s, %s, %s, %s, ST_Force2D(ST_Multi(ST_Transform(ST_GeomFromGeoJSON(%s),4326))))"""
		values = (row.STATE, row.BASENAME, json.dumps(data_json), centroid, row.AREALAND, geog)
		cur.execute(query, values)
		if load_counties:
			counties(row.STATE, load_tracts)

	conn.commit()
	cur.close()

def test_county():
	cur = conn.cursor()
	cur.execute("SELECT c.name FROM counties c WHERE ST_Covers(c.geog, 'SRID=4326;POINT(-121.2273314 38.6950877)'::geography)")
	print(cur.fetchone())
	conn.commit()
	cur.close()

cli.add_command(states)
cli.add_command(places)
cli.add_command(counties)
cli.add_command(tracts)

if __name__ == '__main__':
    cli()

conn.close()
