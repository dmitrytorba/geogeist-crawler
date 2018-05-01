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
	flask run

install:
	npm install

clean:
	rm static/main.js
	rm static/main.css
	rm ./*.pkl
