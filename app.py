from flask import Flask, request, render_template, redirect
from flask_mysqldb import MySQL
from flask_caching import Cache
from pymongo import MongoClient
import flask_login
import hashlib, uuid
import gpxpy
import requests
import sqlqueries
import mongoqueries
import parser
import os
from datetime import datetime, timedelta

app = Flask(__name__, static_url_path='/static', template_folder='html')
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'vite_data'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.secret_key = os.urandom(24)

mysql = MySQL(app)
mongo = MongoClient('localhost', 27017)
login_manager = flask_login.LoginManager(app)

api_url = "http://api.worldweatheronline.com/premium/v1/past-weather.ashx"
api_key = "c0b4ddbacb034b6986b212012202811"

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

class User(flask_login.UserMixin):
  def __init__(self, username, active=True):
    self.username = username
    self.active = active

  def get_id(self):
    return self.username

  def is_active(self):
    return self.active

  def is_anonymous(self):
    return False

  def is_authenticated(self):
    return True

@login_manager.user_loader
def load_user(username):
    return User(username)

@app.context_processor
def inject_user():
    return dict(user=flask_login.current_user)

def execute_query(query):
  cursor = mysql.connection.cursor()
  cursor.execute(query)
  result = cursor.fetchall()
  cursor.close()
  mysql.connection.commit()
  return result

def execute_procedure(procedure, args=[]):
  cursor = mysql.connection.cursor()
  cursor.callproc(procedure, args)
  result = cursor.fetchall()
  cursor.close()
  mysql.connection.commit()
  return result


@app.route('/')
def index():
  query = request.args.get('query')

  if query == None:
    query = '%'

  rides = execute_query(sqlqueries.get_all_rides.format(query=query, username=flask_login.current_user.get_id()))

  return render_template('index.html', rides=rides)

@app.route('/<path:path>')
def serve_html(path):
  return render_template(f'{path}.html')

@app.route('/ride', methods=['GET', 'POST'])
def get_rides():
  if request.method == 'GET':
    pass
  elif request.method == 'POST': # Add ride
    files = request.files.getlist("file")
    rides = ""
    for ride in files:
      data = parser.parse_ride(ride)
      add_ride_query = sqlqueries.add_ride.format(username=flask_login.current_user.get_id(), activity_name=data['name'], time=data['time'].strftime('%Y-%m-%d %H:%M:%S'))
      execute_query(add_ride_query) # Insert into ride table
      ride_id = execute_query(sqlqueries.get_last_insert_id)[0]['LAST_INSERT_ID()'] # Get ride_id

      athlete_id = execute_query(sqlqueries.get_user.format(username=flask_login.current_user.get_id()))[0]['AthleteID']
      mongo.db.Ride.insert({
          "ActivityID": ride_id, 
          "AthleteID": athlete_id, 
          "ActivityName": data['name'], 
          "Time": data['time']
      })
        
      for datapoint in data['datapoints']: # Insert data points 
        add_data_point = sqlqueries.add_data_point.format(time_stamp=datapoint.get('time', 'null'), 
            activity_id=ride_id, 
            elevation=datapoint.get('elevation', 'null'), 
            power=datapoint.get('power', 'null'), 
            temperature=datapoint.get('temperature', 'null'), 
            cadence=datapoint.get('cadence', 'null'), 
            latitude=datapoint.get('latitude', 'null'), 
            longitude=datapoint.get('longitude', 'null'), 
            heartrate=datapoint.get('heartrate', 'null'))
        execute_query(add_data_point)
        
        mongo.db.DataPoint.insert({
            "TimeStamp": datapoint.get('time', None), 
            "ActivityID": ride_id, 
            "Elevation": datapoint.get('elevation', None), 
            "Power": datapoint.get('power', None), 
            "Temperature": datapoint.get('temperature', None), 
            "Cadence": datapoint.get('cadence', None), 
            "Latitude": datapoint.get('latitude', None), 
            "Longitude": datapoint.get('longitude', None), 
            "Heartrate": datapoint.get('heartrate', None)
        })
    return redirect('/')

  return None

@app.route('/ride/<path:ride_id>', methods=['GET'])
def get_ride(ride_id):
  HUMAN_EFFICIENCY_LEVEL = 0.22
  MINUTE = 60

  ride = execute_query(sqlqueries.get_ride.format(activity_id=ride_id, username=flask_login.current_user.get_id()))[0]
  data_point_count = execute_query(sqlqueries.get_row_count.format(Table="DataPoint", activity_id=ride_id))[0]['COUNT(TimeStamp)']
  datapoints = execute_query(sqlqueries.get_data_point.format(activity_id=ride_id, interval=2))
  if 0 <= data_point_count and data_point_count < MINUTE:
    smoothed_data = execute_query(sqlqueries.get_data_point.format(activity_id=ride_id, interval=1))
    lat_long_data = execute_query(sqlqueries.get_lat_long.format(activity_id=ride_id, interval=1))
  elif MINUTE < data_point_count and data_point_count <= 2 * MINUTE:
    smoothed_data = execute_query(sqlqueries.get_data_point.format(activity_id=ride_id, interval=5))
    lat_long_data = execute_query(sqlqueries.get_lat_long.format(activity_id=ride_id, interval=2))
  elif 2 * MINUTE < data_point_count and data_point_count < 5 * MINUTE:
    smoothed_data = execute_query(sqlqueries.get_data_point.format(activity_id=ride_id, interval=10))
    lat_long_data = execute_query(sqlqueries.get_lat_long.format(activity_id=ride_id, interval=4))
  elif 5 * MINUTE <= data_point_count and data_point_count < 10 * MINUTE:
    smoothed_data = execute_query(sqlqueries.get_data_point.format(activity_id=ride_id, interval=30))
    lat_long_data = execute_query(sqlqueries.get_lat_long.format(activity_id=ride_id, interval=6))
  elif 10 * MINUTE <= data_point_count and data_point_count < 60 * MINUTE:
    smoothed_data = execute_query(sqlqueries.get_data_point.format(activity_id=ride_id, interval=60))
    lat_long_data = execute_query(sqlqueries.get_lat_long.format(activity_id=ride_id, interval=8))
  elif 60 * MINUTE <= data_point_count and data_point_count < 120 * MINUTE:
    smoothed_data = execute_query(sqlqueries.get_data_point.format(activity_id=ride_id, interval=90))
    lat_long_data = execute_query(sqlqueries.get_lat_long.format(activity_id=ride_id, interval=10))
  else: # Over 2 hours
    smoothed_data = execute_query(sqlqueries.get_data_point.format(activity_id=ride_id, interval=300))
    lat_long_data = execute_query(sqlqueries.get_lat_long.format(activity_id=ride_id, interval=15))

  stats=[]
  calorie_count = execute_query(sqlqueries.calculate_calories.format(efficiency_value=HUMAN_EFFICIENCY_LEVEL, activity_id=ride_id))
  calorie_val = calorie_count[0][list(calorie_count[0].keys())[0]]

  if calorie_val:
    calorie_count = [int(calorie_count[0][list(calorie_count[0].keys())[0]])]
    calorie_count.append(round(calorie_count[0] / 563, 1))  # Amount of Big Mac's burned
  else:
    calorie_count = None
  stats.append(calorie_count)

  elapsed_time = execute_query(sqlqueries.get_elapsed_time.format(activity_id=ride_id, row_count=data_point_count-1, username=flask_login.current_user.get_id()))
  start_time = elapsed_time[0]['TimeStamp']
  end_time = elapsed_time[1]['TimeStamp']
  stats.append(str(end_time - start_time))

  
  r = requests.get(api_url, 
                      params={"key": api_key,
                              "date": datapoints[0]['TimeStamp'].strftime("%Y-%m-%d"),
                              "q": "{}, {}".format(datapoints[0]['Latitude'], datapoints[0]['Longitude']),
                              "format": "json"}).json()

  wind_speed = float(r['data']['weather'][0]['hourly'][0]['windspeedKmph'])
  wind_direction = r['data']['weather'][0]['hourly'][0]['winddirDegree']
    
  distance = mongoqueries.get_distance_of_ride(mongo, ride['ActivityId'])

  weight = execute_query(sqlqueries.get_profile.format(username=flask_login.current_user.get_id()))[0]['Weight']

  if weight:
    cdA = execute_procedure("calculate_cda", [ride['ActivityId'], weight, distance, wind_speed, wind_direction])[0]['var_cdA']
  else:
    cdA = execute_procedure("calculate_cda", [ride['ActivityId'], 90, distance, wind_speed, wind_direction])[0]['var_cdA']
    cdA = str(cdA) + " (No weight data found in profile. Used 90 Kilogram for calculation by default)"

    
  stats.append(cdA)
    
  latitude_longitude = {}
  for point in lat_long_data:
    for key in point:
      if point[key] != None:
        if key in latitude_longitude:
          latitude_longitude[key].append(point[key])
        else:
          latitude_longitude[key] = [point[key]]

  packed_data = {}
  for point in datapoints:
    for key in point:
      if point[key] == None:
        point[key] = 0
      if key in packed_data:
        packed_data[key].append(point[key])
      else:
        packed_data[key] = [point[key]]

  packed_smooth_data = {}
  for point in smoothed_data:
    for key in point:
      if point[key] == None:
        point[key] = 0
      if key in packed_smooth_data:
        packed_smooth_data[key].append(point[key])
      else:
        packed_smooth_data[key] = [point[key]]

  return render_template('ride.html', ride=ride, datapoints=packed_data, calorie_count=calorie_count, latitude_longitude=latitude_longitude, stats=stats, smooth_datapoints=packed_smooth_data)

@app.route('/delete/ride/<path:ride_id>', methods=['POST'])
def delete_ride(ride_id):
  # Get ride again to assure proper access control.
  # If user is trying to delete other people's ride, it simply sends an error back to the user.
  execute_query(sqlqueries.get_ride.format(activity_id=ride_id, username=flask_login.current_user.get_id()))[0]

  execute_query(sqlqueries.delete_ride.format(activity_id=ride_id))
    
  mongo.db.Ride.delete_one({"ActivityID": int(ride_id)})
  mongo.db.DataPoint.delete_many({"ActivityID": int(ride_id)})
    
  return redirect('/')

@app.route('/update/ride/<path:ride_id>', methods=['POST'])
def update_ride(ride_id):
  # Get ride again to assure proper access control.
  # If user is trying to update other people's ride, it simply sends an error back to the user.
  execute_query(sqlqueries.get_ride.format(activity_id=ride_id, username=flask_login.current_user.get_id()))[0]
  new_name = request.form['newname']
  execute_query(sqlqueries.update_ride.format(activity_id=ride_id, activity_name=new_name))

  mongo.db.Ride.update_one({"ActivityID": int(ride_id)}, {"$set": {"ActivityName": new_name}})

  return redirect(f'/ride/{ride_id}')


@app.route('/register', methods=['POST'])
def register():
  username = request.form['username']
  password = request.form['password']

  salt = str(uuid.uuid4())
  hashed_password = hashlib.sha512((password + salt).encode('utf-8')).hexdigest()

  execute_query(sqlqueries.add_athlete)
  athlete_id = execute_query(sqlqueries.get_last_insert_id)[0]['LAST_INSERT_ID()'] # Get ride_id
  mongo.db.Athlete.insert({"AthleteID": athlete_id})

  try:
    execute_query(sqlqueries.register_user.format(username=username, salt=salt, hashed_password=hashed_password, athlete_id=athlete_id))
    mongo.db.Auth.insert({"Username": username, "Salt": salt, "Hash": hashed_password, "AthleteID": athlete_id})
  except:
    return render_template('register.html', alert="An account with the same username already exists")

  return redirect('/login')


@app.route('/login', methods=['POST'])
def login():
  username = request.form['username']
  password = request.form['password']

  try:
    salt = str(execute_query(sqlqueries.get_salt.format(username=username))[0]['Salt'])
    hashed_password = hashlib.sha512((password + salt).encode('utf-8')).hexdigest()

    can_login = int(execute_query(sqlqueries.login.format(username=username, hashed_password=hashed_password))[0]['COUNT(1)'])
  except:
    return render_template('login.html', alert="You have entered the wrong username / password")

  if can_login:
    flask_login.login_user(load_user(username), remember=True)
    return redirect('/')
  
  return render_template('login.html', alert="You have entered the wrong username / password")


@app.route('/logout', methods=['GET'])
def logout():
  flask_login.logout_user()
  return redirect('/')


@app.route('/profile', methods=['GET'])
def get_profile():
  profile = execute_query(sqlqueries.get_profile.format(username=flask_login.current_user.get_id()))[0]
  stats = execute_query(sqlqueries.agg_user_data_point.format(username=flask_login.current_user.get_id()))[0]

  return render_template('profile.html', profile=profile, stats=stats)


@app.route('/profile', methods=['POST'])
def update_profile():
  name = request.form['name']
  dateofbirth = request.form['dateofbirth']
  weight = request.form['weight']

  try:
    execute_query(sqlqueries.update_profile.format(
      username=flask_login.current_user.get_id(),
      name=name,
      dateofbirth=dateofbirth,
      weight=weight
      ))
    
    athlete_id = execute_query(sqlqueries.get_user.format(username=flask_login.current_user.get_id()))[0]['AthleteID']
    mongo.db.Athlete.update_one({"AthleteID": athlete_id}, 
                                {"$set": {"Name": name, "DateOfBirth": dateofbirth}})

    return redirect('/profile')

  except:
    profile = execute_query(sqlqueries.get_profile.format(username=flask_login.current_user.get_id()))[0]
    stats = execute_query(sqlqueries.agg_user_data_point.format(username=flask_login.current_user.get_id()))

    return render_template('profile.html', profile=profile, stats=stats, alert="You input was not formatted correctly")

@app.route('/global', methods=['GET'])
@cache.cached(timeout=600)
def get_global():
  stats = {}

  stats['totalmiles'] = mongoqueries.get_global_miles(mongo)
  stats['yearlymiles'] = mongoqueries.get_global_miles_last_year(mongo)
  stats['monthlymiles'] = mongoqueries.get_global_miles_last_month(mongo)
  stats['weeklymiles'] = mongoqueries.get_global_miles_last_week(mongo)

  stats['totalhours'] = mongoqueries.get_global_hours(mongo)
  stats['yearlyhours'] = mongoqueries.get_global_hours_last_year(mongo)
  stats['monthlyhours'] = mongoqueries.get_global_hours_last_month(mongo)
  stats['weeklyhours'] = mongoqueries.get_global_hours_last_week(mongo)

  stats['totalcalories'] = mongoqueries.get_global_calories(mongo)
  stats['yearlycalories'] = mongoqueries.get_global_calories_last_year(mongo)
  stats['monthlycalories'] = mongoqueries.get_global_calories_last_month(mongo)
  stats['weeklycalories'] = mongoqueries.get_global_calories_last_week(mongo)

  return render_template('global.html', stats=stats)

@app.route('/leaderboard', methods=['GET'])
@cache.cached(timeout=600)
def get_leaderboard():
  leaderboard = mongoqueries.get_leaderboard(mongo)

  return render_template('leaderboard.html', leaderboard=leaderboard)

@app.route('/fame', methods=['GET'])
@cache.cached(timeout=600)
def get_hall_of_fame():
  stats = {}
  stats['max_elevation'] = mongoqueries.get_athlete_max_elevation(mongo)
  stats['min_elevation'] = mongoqueries.get_athlete_min_elevation(mongo)
  stats['max_temperature'] = mongoqueries.get_athlete_max_temperature(mongo)
  stats['min_temperature'] = mongoqueries.get_athlete_min_temperature(mongo)
  stats['max_cadence'] = mongoqueries.get_athlete_max_cadence(mongo)
  stats['max_power'] = mongoqueries.get_athlete_max_power(mongo)
  stats['max_heartrate'] = mongoqueries.get_athlete_max_heartrate(mongo)

  return render_template('fame.html', stats=stats)

if __name__ == '__main__':
  app.run(host='0.0.0.0')
