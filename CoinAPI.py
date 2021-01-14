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
    API_KEY = json.loads(json_content)['coinapi']


# In[3]:


def Coin_Exchange_Rate(asset = 'BTC'):
    url = f'https://rest-sandbox.coinapi.io/v1/exchangerate/{asset}?apikey={API_KEY}'
    response = requests.get(url)
    json_content = json.loads(response.content)
    return json_content['rates']

def Coin_Exchange_Rate_To_csv(data):
    df = pd.DataFrame.from_records(data)
    df.set_index('asset_id_quote', inplace = True)
    return df

