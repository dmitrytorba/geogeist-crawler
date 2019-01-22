DROP DATABASE geogeist;
CREATE DATABASE geogeist;
\c geogeist;
CREATE EXTENSION postgis;
	
#CREATE EXTENSION postgis_topology;
#CREATE EXTENSION fuzzystrmatch;
#CREATE EXTENSION postgis_tiger_geocoder;

do $$ begin
   if not exists
      (select * from pg_catalog.pg_user where usename = 'geogeist') then
          create role geogeist login password 'password';
          grant all on database geogeist to geogeist;   
       end if;
end $$;

create table if not exists counties
(
	gid serial primary key, 
	state text, 
	name text, 
	geog geography(MULTIPOLYGON)
);

grant all privileges on table counties to geogeist;
grant usage, select on sequence counties_gid_seq to geogeist;