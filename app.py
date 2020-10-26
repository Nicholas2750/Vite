from flask import Flask, request, render_template
import mysql

app = Flask(__name__, static_url_path='/static', template_folder='html')

@app.route('/')
def index():
  return render_template('index.html')

@app.route('/<path:path>')
def serve_html(path):
  return render_template(f'{path}.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0')
