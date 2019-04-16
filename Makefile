BABEL_CMD = node_modules/.bin/babel
SASS_CMD = sassc
BABEL_ARGS = --source-maps-inline 
SASS_SRC = sass
JS_SRC = js 

build: static/main.css static/main.js 

static/main.css: main.sass
	sassc $? > $@

static/main.js: js/graph.es6.js js/main.es6.js 
	$(BABEL_CMD) js --out-file $@

run: build
	FLASK_APP=server.py flask run ${FLASK_ARGS}

install:
	mkdir -p static
	npm install
	sudo apt install python3 python3-pip python3-venv
	python3 -m pip install --user virtualenv
	python3 -m venv venv
	. venv/bin/activate
	pip install -r requirements.txt

map:
	MAP_KEY=`cat map_key.txt` python3 maps.py

clean:
	rm -f static/main.js
	rm -f static/main.css
	rm -f static/*.png
	rm -f ./*.pkl

db:
	psql "sslmode=disable user=postgres host=localhost" -f schema.sql

upload:
	gsutil rsync -d static gs://geogeist-227901.appspot.com/static

connect:
	./bin/cloud_sql_proxy -U geogeist -h 127.0.0.1  --port 5433