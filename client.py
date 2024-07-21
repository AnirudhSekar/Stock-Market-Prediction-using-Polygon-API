# Imports
from polygon import rest
from urllib3 import HTTPResponse
from typing import cast
from datetime import datetime as dt
import config
import json 
import talib
import numpy as np
import pandas as pd

def getData():
    # Connect to Polygon
    client = rest.RESTClient(config.API_KEY)
    closeList = []
    timeList = []
    endDate = dt.today().strftime('%Y-%m-%d')
    # Aggregate to HTTP Request 
    aggs = cast(
        HTTPResponse, 
        client.get_aggs({
            ''
        })
    )