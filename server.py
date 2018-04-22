from flask import Flask, render_template, request 
import geo
import json
app = Flask(__name__)

@app.route('/')
def main_page():
    return render_template('main.tpl')

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/data')
def data():
    lon = float(request.args.get('lon'))
    lat = float(request.args.get('lat'))
    # TODO: check input
    return json.dumps(geo.get_data(lat, lon))
