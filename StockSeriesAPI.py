#!/usr/bin/env python
# coding: utf-8

# In[1]:


import json
import requests
import pandas as pd


# In[2]:


API_KEY = None
with open('api_key', 'r') as f:
    json_content = f.read()
    API_KEY = json.loads(json_content)['alphavantage']


# In[3]:


def TIME_SERIES_DAILY_ADJUSTED(symbol, outputsize = 'compact', datatype = 'json', apikey = API_KEY):
    api_url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&outputsize={outputsize}&datatype={datatype}&apikey={apikey}'
    response = requests.get(api_url)
    json_content = json.loads(response.content)
    return json_content['Time Series (Daily)']

def TIME_SERIES_TO_CSV(time_series, columns = ['open', 'high', 'low', 'close', 'adjusted close', 'volume', 'dividend amount', 'split coefficient']):
    df = pd.DataFrame.from_dict(time_series, orient = 'index')
    df.rename(columns = {'1. open': 'open', '2. high': 'high', '3. low': 'low', '4. close': 'close', '5. adjusted close': 'adjusted close', '6. volume': 'volume', '7. dividend amount': 'dividend amount', '8. split coefficient': 'split coefficient'}, inplace = True)
    df = df[columns]
    return df

