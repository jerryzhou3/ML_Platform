from flask import Flask, jsonify, request, abort
import json
import requests
import pandas as pd
import dill

app = Flask(__name__)

TOKEN = 'test_token'

@app.route('/run_task', methods = ['GET', 'POST'])
def run_task():
    token = request.args.get('token')
    if token != TOKEN:
        return jsonify({'status code': 401})
    parser = dill.loads(request.data)
    data = parser(symbol = request.args.get('symbol'), apikey = request.args.get('apikey'))
    return data
    # return jsonify({'params': params, 'parser': parser, 'token': token})

if __name__ == "__main__":
    app.run(host = "0.0.0.0", port = 5000, debug = True)