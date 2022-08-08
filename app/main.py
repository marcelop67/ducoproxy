from flask import Flask
import duco

app = Flask(__name__)

@app.route('/')
def main():
    return duco.get(log_output=False)

@app.route('/log')
def log():
    return duco.get(log_output=True)

if __name__ == '__main__':
    # Only for debugging while developing
    app.run(debug=True)
