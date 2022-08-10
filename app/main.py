from flask import Flask, abort
from werkzeug.exceptions import HTTPException
import logging
import json
import duco

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

@app.errorhandler(HTTPException)
def handle_exception(err):
    app.logger.exception('An exception occured')
    response = err.get_response()
    response.data = json.dumps({
        'code': err.code,
        'name': err.name,
        'description': err.description,
    })
    response.content_type = 'application/json'
    return response

@app.route('/')
def main():
    try:
        data = duco.getinfo()
    except Exception as err:
        return abort(500)
    else:
        return data

@app.route('/log')
def log():
    try:
        data = duco.writelog()
    except Exception as err:
        return abort(500)
    else:
        return data

@app.route('/check/<string:location>/<string:field>/<float:threshold>')
def check(location, field, threshold):
    try:
        result = duco.chksensor(location, field, threshold)
    except KeyError as err:
        return abort(404)
    except Exception as err:
        return abort(500)
    else:
        return result
 
if __name__ == '__main__':
    # Only for debugging while developing
    app.run(debug=True)
