DROP DATABASE geogeist;
CREATE DATABASE geogeist;
\c geogeist;
CREATE EXTENSION postgis;
	
--CREATE EXTENSION postgis_topology;
--CREATE EXTENSION fuzzystrmatch;
--CREATE EXTENSION postgis_tiger_geocoder;

do $$ begin
   if not exists
      (select * from pg_catalog.pg_user where usename = 'geogeist') then
          create role geogeist login password 'password';
          grant all on database geogeist to geogeist;   
       end if;
end $$;

create table if not exists states 
(
	gid serial primary key, 
	state text UNIQUE, 
	name text, 
	data json, 
	area numeric,
	centroid geography(POINT),
	geog geography(MULTIPOLYGON)
);

grant all privileges on table states to geogeist;
grant usage, select on sequence states_gid_seq to geogeist;

create table if not exists counties
(
	gid serial primary key, 
	state text, 
	county text UNIQUE,
	name text,
	data json, 
	area numeric,
	centroid geography(POINT),
	geog geography(MULTIPOLYGON)
);

grant all privileges on table counties to geogeist;
grant usage, select on sequence counties_gid_seq to geogeist;

create table if not exists places 
(
	gid serial primary key, 
	state text, 
	name text UNIQUE,
	data json, 
	geog geography(MULTIPOLYGON)
);

grant all privileges on table places to geogeist;
grant usage, select on sequence places_gid_seq to geogeist;

create table if not exists tracts
(
	gid serial primary key, 
	state text, 
	county text,
	name text,
	data json, 
	objid text UNIQUE,
	area numeric,
	centroid geography(POINT,4326),
	geog geography(MULTIPOLYGON,4326)
);

grant all privileges on table tracts to geogeist;
grant usage, select on sequence tracts_gid_seq to geogeist;


