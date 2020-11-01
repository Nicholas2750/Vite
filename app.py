from flask import Flask, request, render_template, redirect
from flask_mysqldb import MySQL
import gpxpy
import sqlqueries
import parser

app = Flask(__name__, static_url_path='/static', template_folder='html')
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'vite_data'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

def execute_query(query):
  cursor = mysql.connection.cursor()
  cursor.execute(query)
  result = cursor.fetchall()
  cursor.close()
  mysql.connection.commit()
  return result

@app.route('/')
def index():
  return render_template('index.html', rides=[{'name':'test', 'id':1}])

@app.route('/<path:path>')
def serve_html(path):
  return render_template(f'{path}.html')

@app.route('/ride', methods=['GET', 'POST', 'PUT', 'DELETE'])
def get_rides():
  if request.method == 'GET':
    pass
  elif request.method == 'POST': # Add ride
    files = request.files.getlist("file")
    rides = ""
    for ride in files:
      data = parser.parse_ride(ride)
      add_ride_query = sqlqueries.add_ride.format(athlete_id=1, activity_name=data['name'], time=data['time'].strftime('%Y-%m-%d %H:%M:%S'))
      execute_query(add_ride_query) # Insert into ride table
      ride_id = execute_query(sqlqueries.get_last_insert_id)[0]['LAST_INSERT_ID()'] # Get ride_id

      for datapoint in data['datapoints']: # Insert data points 
        add_data_point = sqlqueries.add_data_point.format(time_stamp=datapoint['time'], 
                                                          activity_id=ride_id, 
                                                          elevation=datapoint['elevation'], 
                                                          power=datapoint['power'], 
                                                          temperature=datapoint['temperature'], 
                                                          cadence=datapoint['cadence'], 
                                                          latitude=datapoint['latitude'], 
                                                          longitude=datapoint['longitude'], 
                                                          heartrate=datapoint['heartrate'])
        execute_query(add_data_point)
    return "Success!"

  elif request.method == 'PUT':
    pass
  elif request.method == 'DELETE':
    pass
  print(sqlqueries.get_ride)
  pass

@app.route('/ride/<path:ride_id>', methods=['GET'])
def get_ride(ride_id):
  return render_template('ride.html', ride={'name': 'test ride', 'id': ride_id})

@app.route('/delete/ride/<path:ride_id>', methods=['POST'])
def delete_ride(ride_id):
  return redirect('/')

@app.route('/update/ride/<path:ride_id>', methods=['POST'])
def update_ride(ride_id):
  return render_template('ride.html', ride={'name': 'test ride'})

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
