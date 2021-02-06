import os
from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
import requests
import dill
import json
import pandas as pd
import time

project_dir = os.path.dirname(os.path.abspath(__file__))
db_file = "sqlite:///{}".format(os.path.join(project_dir, "database.db"))

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = db_file

db = SQLAlchemy(app)

class Stock(db.Model):
    code = db.Column(db.String(80), unique = True, nullable = False, primary_key = True)
    date = db.Column(db.DateTime, unique = False, nullable = False, primary_key = True)
    open = db.Column(db.Float, unique = False, nullable = False)
    high = db.Column(db.Float, unique = False, nullable = False)
    low = db.Column(db.Float, unique = False, nullable = False)
    close = db.Column(db.Float, unique = False, nullable = False)
    adjusted_close = db.Column(db.Float, unique = False, nullable = False)
    volume = db.Column(db.Integer, unique = False, nullable = False)
    dividend = db.Column(db.Float, unique = False, nullable = False)
    split = db.Column(db.Float, unique = False, nullable = False)

    def __repr__(self):
        return "<Code: {}, Open: {}, High: {}, Low: {}, Close: {}, Adjusted Close: {}, Volume: {}, Dividend Amount: {}, Split Coefficient: {}>"\
            .format(self.code, self.open, self.high, self.low, self.close, self.adjusted_close, self.volume, self.dividend, self.split)

class Coin(db.Model):
    code = db.Column(db.String(80), unique = True, nullable = False, primary_key = True)
    date = db.Column(db.DateTime, unique = False, nullable = False, primary_key = True)
    exchange_rate_usdc = db.Column(db.Float, unique = False, nullable = False)

    def __repr__(self):
        return "<Asset: {}, USDC Rate: {}>".format(self.code, self.exchange_rate_usdc)

API_KEY = None
with open('api_key', 'r') as f:
    json_content = f.read()
    API_KEY = json.loads(json_content)['alphavantage']

def TIME_SERIES_DAILY_ADJUSTED_TO_JSON(symbol, outputsize = 'compact', datatype = 'json', apikey = API_KEY):
    api_url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&outputsize={outputsize}&datatype={datatype}&apikey={apikey}'
    response = requests.get(api_url)
    json_content = json.loads(response.content)
    time_series = json_content['Time Series (Daily)']
    df = pd.DataFrame.from_dict(time_series, orient = 'index', dtype = 'float')
    df.rename(columns = {'1. open': 'open', '2. high': 'high', '3. low': 'low', '4. close': 'close', '5. adjusted close': 'adjusted close', '6. volume': 'volume', '7. dividend amount': 'dividend amount', '8. split coefficient': 'split coefficient'}, inplace = True)
    columns = ['open', 'high', 'low', 'close', 'adjusted close', 'volume', 'dividend amount', 'split coefficient']
    df = df[columns]
    return df.to_json(orient = 'index')

TIME_SERIES_DAILY_ADJUSTED_TO_JSON_SERIALIZED = dill.dumps(TIME_SERIES_DAILY_ADJUSTED_TO_JSON)

SERVICES = {"ec2-18-167-84-46.ap-east-1.compute.amazonaws.com": {"port": 80, "task_count": 0, "healthy": 1}, \
    "ec2-18-162-143-65.ap-east-1.compute.amazonaws.com": {"port": 80, "task_count": 0, "healthy": 1}}
TASK_TABLE = {"ec2-18-167-84-46.ap-east-1.compute.amazonaws.com": [], "ec2-18-162-143-65.ap-east-1.compute.amazonaws.com": []}

MAX_TASKS_PER_SERVICE = 2
MAX_TASKS_TOTAL = 4
CURRENT_TASK_COUNT = 0


@app.route("/", methods = ["GET", "POST"])
def home():
    stocks = Stock.query.all()
    coins = Coin.query.all()
    return render_template('home.html', stocks = stocks, coins = coins)

@app.route("/task_assigner", methods = ["GET", "POST"])
def task_assigner():
    for asset in request.args.get('asset'):
        # parse task
        params = {'asset': asset, 'apikey': API_KEY, 'token': 'test_token'}
        service_to_assign = None
        min_task_count = float('inf')
        # find the least busy server
        for service, info in SERVICES.items():
            if info['task_count'] < min_task_count and info['healthy']:
                min_task_count = info['task_count']
                service_to_assign = service
        # post task to service
        response = requests.post(url = f"http://{service_to_assign}:{SERVICES[service_to_assign]['port']}/task_assigner", \
            params = params, data = TIME_SERIES_DAILY_ADJUSTED_TO_JSON_SERIALIZED)
        # update task table and counter if task assignment successful
        if response.text == 'success':
            CURRENT_TASK_COUNT += 1
            service_to_assign['task_count'] += 1
            TASK_TABLE[service_to_assign].append(asset) 

@app.route("/task_result_receiver", methods = ["GET", "POST"])
def task_result_receiver():
    # get variables and data
    CURRENT_TASK_COUNT -= 1
    dns = request.args.get('DNS')
    SERVICES[dns]['task_count'] -= 1
    asset = request.args.get('asset')
    TASK_TABLE[dns].remove(asset)
    date = request.args.get('date')
    data = request.json
    # insert data to database
    stock_data = Stock(code = asset, date = date, open = data['open'], high = data['high'], low = data['low'], close = data['close'], \
        adjusted_close = data['adjusted close'], volume = data['volume'], dividend = data['dividend amount'], split = data['split coefficient'])
    db.session.add(stock_data)
    db.session.commit()
    return "success", 200
    
@app.route("/health_checker", methods = ["GET"])
def health_checker():
    status = {}
    for service in SERVICES:
        try:
            response = requests.get(f"http://{service}:{SERVICES[service]['port']}/health_checker")
            if response.text == "success":
                SERVICES[service]['health'] = 1
                status[service] = "healthy"
        except:
            SERVICES[service]['health'] = 0
            status[service] = "not healthy"
    return jsonify({"service status": status}), 200
            



if __name__ == "__main__":
    app.run(host = "0.0.0.0", port = 5001, debug = True)