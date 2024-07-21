from dash import Dash, html, dcc
import dash_daq as daq
from dash.dependencies import Input, Output
import matplotlib
import dash_bootstrap_components as dbc
matplotlib.use("Agg")
from plotly import graph_objects as go
from polygon import RESTClient
from urllib3 import HTTPResponse
import config
import json
import pandas as pd
import talib
import numpy as np
from ai_prediction import lossgain
from typing import cast
import datetime


# Connect to Polygon REST API
client = RESTClient(config.API_KEY)

# Dash Setup
app = Dash(__name__,external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[
        {"name": "viewport",
         "content": "width=device-width, initial-scale=1"}
    ])
app.layout = html.Div( [
        
    html.H1('Stock Graphs', style={'color': 'black', 'font-weight': 'bold','font-family':"arial", 'margin':'20px'}),
    html.Div([
    html.P("Choose a stock:", style={'font-style': 'italic',
        'font-weight': 'bold',
        'margin':'20px',
        'display':'flex'}),
    dcc.Dropdown(
            id="stock-val",
            options=[
                {'label':"Apple", 'value':"AAPL"},
                {'label':"Google", 'value':"GOOGL"},
                {'label':"Tesla", 'value':"TSLA"},
                {'label':"Amazon", 'value':"AMZN"},
                {'label':"Netflix", 'value':"NFLX"},
                {'label':"Microsoft", 'value':"MSFT"},
                {'label':"Nvidia", 'value':"NVDA"},



            ], 
            className='dropdown-class-1',
            value="AAPL",
            style={'margin':'10px','width':'60%'}
        ), 
], style={'width':'60%', "display":'flex'}),
    html.Div([
    html.Div(children='Start date:', style={
        'font-style': 'italic',
        'font-weight': 'bold',
        'margin':'20px'
    }),

    dbc.Input(
        id="start",
        type="text",
        value=str((datetime.datetime.today()-datetime.timedelta(366)).strftime('%Y-%m-%d')),
        style={'margin':'20px', 'width':'10%'}
    ),
    html.Div(children='End date:', style={
        'font-style': 'italic',
        'font-weight': 'bold',
        'margin':'20px',
        'display':'flex'
    }),
    dbc.Input(
        id="end",
        type="text",
        value=str(datetime.datetime.today().strftime('%Y-%m-%d')),
        style={'margin':'20px', 'width':'10%'}
    ),
    ], style={'display':'flex'}),
    dcc.Graph(id="stock-graph", style={'width':'500', 'height':'400'}),
    html.Div([
        dbc.Button(children="Click on me for tomorrow's price increase prediction for this stock!" ,id='pred-button'),
        html.P(id="prediction-button", children="")
    ],  style={'margin':'20px'})
], id="app")

@app.callback(Output('stock-graph', 'figure'), [Input("stock-val", component_property='value'), Input("start", component_property="value"),Input("end", component_property="value")])
def graph(stock_val, start, end):
    # Receive the data
    aggs = cast(
        HTTPResponse,
        client.get_aggs(
            stock_val,
            1,
            'day',
            start,
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
    
    closeList = np.array(closeList)
    ema_8 = talib.EMA(closeList, 8)
    ema_13 = talib.EMA(closeList, 13)
    ema_21 = talib.EMA(closeList, 21)
    ema_55 = talib.EMA(closeList, 55)

    

    upper, middle, lower = talib.BBANDS(closeList, timeperiod=20, nbdevdn=2,matype=0)
    times = []
    for time in timestamp:
        times.append(pd.Timestamp(time, tz='GMT', unit="ms"))

    fig = go.Figure()

    fig.add_trace(go.Candlestick(x=times, open=openList, high=highList, low=lowList,close=closeList,name=stock_val))
    fig.add_trace(go.Scatter(x=times,y=upper, name='Bollinger Band Upper'))
    fig.add_trace(go.Scatter(x=times,y=middle, name='Bollinger Band Middle'))
    fig.add_trace(go.Scatter(x=times,y=lower, name='Bollinger Band Lower'))
    fig.add_trace(go.Scatter(x=times,y=ema_8, name='EMA 8'))
    fig.add_trace(go.Scatter(x=times,y=ema_13, name='EMA 13'))
    fig.add_trace(go.Scatter(x=times,y=ema_21, name='EMA 21'))
    fig.add_trace(go.Scatter(x=times,y=ema_55, name='EMA 55'))
    fig.update_layout(transition_duration=500)
    fig.update_layout(xaxis_rangeslider_visible=False)
    return fig


@app.callback(Output('prediction-button', 'children'), [Input("stock-val", component_property='value'),Input("end", component_property="value"),Input('pred-button', 'n_clicks')], prevent_initial_call=True)
def run_ai(stock_val, end, _):
    return lossgain(stock_val, end)



if __name__ == "__main__":
    app.run_server(debug=True)