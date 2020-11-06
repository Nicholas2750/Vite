from flask import Flask, request, render_template, redirect
from flask_mysqldb import MySQL
import flask_login
import hashlib, uuid
import gpxpy
import sqlqueries
import parser
import os

app = Flask(__name__, static_url_path='/static', template_folder='html')
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'vite_data'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.secret_key = os.urandom(24)
mysql = MySQL(app)
login_manager = flask_login.LoginManager(app)

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

@app.route('/')
def index():
  query = request.args.get('query')

  if query == None:
    query = '%'

  rides = execute_query(sqlqueries.get_all_rides.format(query=query))

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
      add_ride_query = sqlqueries.add_ride.format(athlete_id=3, activity_name=data['name'], time=data['time'].strftime('%Y-%m-%d %H:%M:%S'))
      execute_query(add_ride_query) # Insert into ride table
      ride_id = execute_query(sqlqueries.get_last_insert_id)[0]['LAST_INSERT_ID()'] # Get ride_id

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
    return redirect('/')

  return None

@app.route('/ride/<path:ride_id>', methods=['GET'])
def get_ride(ride_id):
  ride = execute_query(sqlqueries.get_ride.format(activity_id=ride_id))[0]
  datapoints = execute_query(sqlqueries.get_data_point.format(activity_id=ride_id))

  packed_data = {}

  for point in datapoints:
    for key in point:
      if point[key] == None:
        point[key] = 0
      if key in packed_data:
        packed_data[key].append(point[key])
      else:
        packed_data[key] = [point[key]]

  return render_template('ride.html', ride=ride, datapoints=packed_data)

@app.route('/delete/ride/<path:ride_id>', methods=['POST'])
def delete_ride(ride_id):
  execute_query(sqlqueries.delete_ride.format(activity_id=ride_id))
  return redirect('/')

@app.route('/update/ride/<path:ride_id>', methods=['POST'])
def update_ride(ride_id):
  new_name = request.form['newname']
  execute_query(sqlqueries.update_ride.format(activity_id=ride_id, activity_name=new_name))
  return redirect(f'/ride/{ride_id}')


@app.route('/register', methods=['POST'])
def register():
  username = request.form['username']
  password = request.form['password']

  salt = str(uuid.uuid4())
  hashed_password = hashlib.sha512((password + salt).encode('utf-8')).hexdigest()

  execute_query(sqlqueries.register_user.format(username=username, salt=salt, hashed_password=hashed_password))

  return redirect('/login')


@app.route('/login', methods=['POST'])
def login():
  username = request.form['username']
  password = request.form['password']

  salt = str(execute_query(sqlqueries.get_salt.format(username=username))[0]['Salt'])
  hashed_password = hashlib.sha512((password + salt).encode('utf-8')).hexdigest()

  can_login = str(execute_query(sqlqueries.login.format(username=username, hashed_password=hashed_password))[0]['COUNT(1)'])

  if can_login:
    flask_login.login_user(load_user(username), remember=True)

  return redirect('/')

@app.route('/logout', methods=['GET'])
def logout():
  flask_login.logout_user()
  return redirect('/')

if __name__ == '__main__':
  app.run(host='0.0.0.0')
