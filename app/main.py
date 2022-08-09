from flask import Flask
import requests
import duco

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

@app.route('/')
def main():
    return duco.getinfo()

@app.route('/log')
def log():
    return duco.writelog()

@app.route('/check/<string:location>/<string:field>/<float:threshold>')
def check(location, field, threshold):
    return duco.chksensor(location, field, threshold)
 
if __name__ == '__main__':
    # Only for debugging while developing
    app.run(debug=True)
