import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
import dill
import json
import pandas as pd

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

serialize = dill.dumps(TIME_SERIES_DAILY_ADJUSTED_TO_JSON)

API_KEY = None
with open('api_key', 'r') as f:
    json_content = f.read()
    API_KEY = json.loads(json_content)['alphavantage']

@app.route("/", methods = ["GET", "POST"])
def home():
    stocks = Stock.query.all()
    coins = Coin.query.all()
    return render_template('home.html', stocks = stocks, coins = coins)

@app.route("/query", methods = ["GET", "POST"])
def query():
    for asset in request.args.get('asset'):
        params = {'symbol': asset, 'apikey': API_KEY, 'token': 'test_token'}
        data = requests.post(url = "http://127.0.0.1:5000/run_task", params = params, data = serialize)
        # TO DO #
        ## ADD TO DATABASE ##
    

