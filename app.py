from flask import Flask, render_template
import mysql

app = Flask(__name__)

@app.route('/')
def index():
  return 'Hello from our DigitalOcean server'

if __name__ == '__main__':
    app.run(host='0.0.0.0')
