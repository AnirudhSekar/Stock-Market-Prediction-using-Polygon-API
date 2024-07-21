from polygon import RESTClient
import matplotlib
matplotlib.use("Agg")
from polygon import RESTClient
from urllib3 import HTTPResponse
import config
import json
import pandas as pd
import numpy as np
from typing import cast
import datetime
import tensorflow as tf
from keras.layers import LSTM, Bidirectional, Dense
from keras.models import Sequential
from sklearn.preprocessing import MinMaxScaler

client = RESTClient(config.API_KEY)
def lossgain(stock_val, end):
        
        aggs = cast(
            HTTPResponse,
            client.get_aggs(
                stock_val,
                1,
                'day',
                str((datetime.datetime.today()-datetime.timedelta(366*2)).strftime('%Y-%m-%d')),
                end,
                raw = True
            ),
            )
        data = json.loads(aggs.data)
        closeList = []
        openList = []
        highList = []
        lowList = []
        timestamp = []
        lossgain= []
        
        for item in data:
            if item == 'results':
                rawData = data[item]
        for bar in rawData:
            for category in bar:
                if category == "c":
                    closeList.append(bar[category])
                elif category == "h":
                    highList.append(bar[category])
                elif category == 'l':
                    lowList.append(bar[category])
                elif category == 'o':
                    openList.append(bar[category])
                elif category == 't':
                    timestamp.append(bar[category])
        for i in range(len(openList)):
                lossgain.append(closeList[i]-openList[i])
        times = []
        for time in timestamp:
            times.append(pd.Timestamp(time, tz='GMT', unit="ms"))
        print(times[-1])
        # Make LossGain a time series
        lossgain = np.array(lossgain).astype(float)
        scaler = MinMaxScaler(feature_range=(0, 1))
        lossgain = scaler.fit_transform(lossgain.reshape(-1, 1))

        # Function to create the dataset with input features and labels
        def create_dataset(series, look_back=1):
            X, y = [], []
            for i in range(len(series) - look_back):
                X.append(series[i:(i + look_back), 0])
                y.append(series[i + look_back, 0])
            return np.array(X), np.array(y)
        
        # Change the lookback to whatever you feel has the best results
        lookback=1
        if stock_val == "NFLX" or stock_val == "TSLA":  
            lookback = 5
        X, y = create_dataset(lossgain, lookback)

        # Reshape input to be [samples, time steps, features]
        X = np.reshape(X, (X.shape[0], X.shape[1], 1))

        # Split the data into training and testing sets
        train_size = int(len(X) * 0.8)
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]

        # Create AI model
        print(X_train.shape)
        model = Sequential([
            Bidirectional(LSTM(50, input_shape=(21, 1), return_sequences=True)),
            Bidirectional(LSTM(50, return_sequences=True)),
            (LSTM(50)),
            Dense(1)
        ])
        model.compile(optimizer=tf.optimizers.legacy.Adam(0.0001), loss="mae", metrics=["MeanSquaredError", "RootMeanSquaredError"])
        model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=10, batch_size=32, verbose=2)

        test_predictions = model.predict(X_test)
        test_predictions = scaler.inverse_transform(test_predictions.reshape(-1,1))
        return (f"Prediction of price increase for {stock_val}: {test_predictions[-1][0]:.2f}")

