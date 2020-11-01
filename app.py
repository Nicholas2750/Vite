from flask import Flask, request, render_template
import mysql
import gpxpy
import sqlqueries
import parser

app = Flask(__name__, static_url_path='/static', template_folder='html')

@app.route('/')
def index():
  return render_template('index.html')

@app.route('/<path:path>')
def serve_html(path):
  return render_template(f'{path}.html')

@app.route('/ride', methods=['GET', 'POST', 'PUT', 'DELETE'])
def get_ride():
  if request.method == 'GET':
    pass
  elif request.method == 'POST':
    files = request.files.getlist("file")
    rides = ""
    for ride in files:
      rides += str(parser.parse_ride(ride))

    return rides

  elif request.method == 'PUT':
    pass
  elif request.method == 'DELETE':
    pass
  print(sqlqueries.get_ride)
  pass

'''
@app.route('/race', methods=['GET', 'POST', 'PUT'])
def get_race():
  if request.method == 'GET':
    pass
  elif request.method == 'POST':
    pass
  elif request.method == 'PUT':
    pass
  print(sqlqueries.get_race)
  pass

@app.route('/athlete', methods=['GET', 'POST', 'PUT', 'DELETE'])
def get_athlete():
  if request.method == 'GET':
    pass
  elif request.method == 'POST':
    pass
  elif request.method == 'PUT':
    pass
  elif request.method == 'DELETE':
    pass
  print(sqlqueries.get_athlete)
  pass

@app.route('/data_point', methods=['GET'])
def get_data_point():
  if request.method == 'GET':
    pass
  print(sqlqueries.get_data_point)
  pass
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0')
