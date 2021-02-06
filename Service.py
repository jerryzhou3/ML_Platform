from flask import Flask, jsonify, request, abort
import json
import requests
import pandas as pd
import dill
import multiprocessing as mp
import time

app = Flask(__name__)

TOKEN = 'test_token'

execute_queue = mp.Queue(10)
result_queue = mp.Queue(10)

def execute_task(exe_q, res_q):
    while True:
        task = exe_q.get()
        parser = dill.loads(task['parser'])
        data = parser(symbol = task['asset'], apikey = task['apikey'])
        res_q.put(data)
        

@app.route('/task_receiver', methods = ['GET', 'POST'])
def task_receiver():
    token = request.args.get('token')
    if token != TOKEN:
        return "wrong token", 401
    
    try:
        task = {"parser": request.data, "asset": request.args.get('asset'), "apikey": request.args.get('apikey')}
        execute_queue.put(task, timeout = 5)
        # p = mp.Process(target = execute_queue, args = (execute_queue, result_queue))
        # p.start()
        return "success", 200
    except mp.Queue.Full:
        return "timeout", 408
    

# @app.route('/task_executor')
# def task_executor():
#     while not execute_queue.empty():

@app.route("/health_checker")
def health_checker():
    return "success", 200


if __name__ == "__main__":
    app.run(host = "0.0.0.0", port = 80, debug = True)