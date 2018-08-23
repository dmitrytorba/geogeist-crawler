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
	python3 -m venv venv
	. venv/bin/activate
	pip install -r requirements.txt

clean:
	rm -f static/main.js
	rm -f static/main.css
	rm -f ./*.pkl
