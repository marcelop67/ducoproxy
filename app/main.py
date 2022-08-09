from flask import Flask, abort
import logging
import duco

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

@app.route('/')
def main():
    try:
        info = duco.getinfo()
    except Exception as err:
        app.logger.exception('An exception occured')
        return abort(500)
    else:
        return info

@app.route('/log')
def log():
    try:
        result = duco.writelog()
    except Exception as err:
        app.logger.exception('An exception occured')
        return abort(500)
    else:
        return result


@app.route('/check/<string:location>/<string:field>/<float:threshold>')
def check(location, field, threshold):
    try:
        result = duco.chksensor(location, field, threshold)
    except KeyError as err:
        return abort(404)
    except Exception as err:
        app.logger.exception('An exception occured')
        return abort(500)
    else:
        return result
 
if __name__ == '__main__':
    # Only for debugging while developing
    app.run(debug=True)
