from flask import Flask, render_template, request 
import geo
import json
import numpy
app = Flask(__name__)

@app.route('/')
def main_page():
    return render_template('main.tpl')

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

# https://stackoverflow.com/questions/27050108/convert-numpy-type-to-python
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, numpy.integer):
            return int(obj)
        elif isinstance(obj, numpy.floating):
            return float(obj)
        elif isinstance(obj, numpy.ndarray):
            return obj.tolist()
        else:
            return super(NumpyEncoder, self).default(obj)

@app.route('/data')
def data():
    lon = float(request.args.get('lon'))
    lat = float(request.args.get('lat'))
    # TODO: check input
    return json.dumps(geo.get_data(lat, lon),cls=NumpyEncoder)
