from flask_mysqldb import MySQL



def get_connection(app):
  app.config['MYSQL_HOST'] = 'localhost'
  app.config['MYSQL_USER'] = 'vite_user'
  app.config['MYSQL_PASSWORD'] = 'password'
  app.config['MYSQL_DB'] = 'vite_data'

  return MySQL(app)

def execute_query(app, query):
  mysql = get_connection(app)

  cursor = mysql.connection.cursor()
  cursor.execute(query)
  cursor.close()
