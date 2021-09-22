#stock_query_viz_app_bokeh_standalone.py

#from threading import Thread

#from flask import Flask, render_template, request, redirect
#from tornado.ioloop import IOLoop

from bokeh.embed import server_document
from bokeh.layouts import column, row
from bokeh.models import Select, MultiChoice, Toggle
from bokeh.plotting import figure, curdoc #,show
from bokeh.server.server import Server
from bokeh.themes import Theme

import requests
import json 
import time
import os

import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar


#app = Flask(__name__)

#def stock_query_viz_app(doc):

key = os.environ.get('ALPHA_API_KEY')

#create new dataframe of all tickers of potential interest by querying Alpha Vantage
def create_ticker_df_all():

    #start as a dictionary
    ticker_df_all = {}

    for ticker in all_tickers: 

        url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={}&apikey={}'.format(ticker, key)

        #I will give it a certain number of tries on each request, with increasing delay time, in case there is too much traffic

        num_request_attempts = 20

        attempts = 0

        timeout = 1

        while attempts < num_request_attempts:

            try:
                time.sleep(timeout)

                response = requests.get(url)

                response_data = response.json() 

                ticker_df = pd.DataFrame.from_dict(response_data['Time Series (Daily)'],orient='index',dtype='float')

                break

            except KeyError:

                if attempts%3==1:
                    #every few seconds, plot a message to let the user know we are waiting for the query results
                    waiting_text = 'Querying from Alpha Vantage API ' + '...'*timeout
                    print(waiting_text)

                time.sleep(timeout)
                attempts += 1
                timeout += 1

        #switch to increasing chronological order
        ticker_df = ticker_df.iloc[::-1]   

        #save in dictionary of dataframes    
        ticker_df_all[ticker]=ticker_df

    #this is the critical step to make it into a multi-index dataframe
    ticker_df_all = pd.concat(ticker_df_all,axis=1)

    #switch the index to datetime format
    ticker_df_all.index = pd.to_datetime(ticker_df.index)

#        #Optional, useful for future modeling/prediction efforts:

#        #Create custom business day frequency based on Federal holidays in the US
#        #bday_us = pd.offsets.CustomBusinessDay(calendar=USFederalHolidayCalendar())

#        #specify that the data is sampled every business (US-based) day   
#        #ticker_df_all.index.freq=bday_us

    return ticker_df_all


#plot the figure from the existing dataframe 'ticker_df_all' and all control selections 
def create_figure():

    #initialize the figure:

    # #optional arguments:
    kw = dict()
    #kw['tools'] = 'pan,box_zoom,hover,reset'
    kw['title'] = 'Recent stocks performance queried using Alpha Vantage API'

    p = figure(width=700, height=400, x_axis_type="datetime",**kw) 

    if (toggle_normalization.active) and (var_select.value not in ['7. dividend amount', '8. split coefficient']):
        p.yaxis.axis_label = var_select.value.title() + ' - Percentage Change' 
        normalize = True
    else:
        p.yaxis.axis_label = var_select.value.title() 
        normalize = False

    #for each selected stock, extract from dataframe and plot:

    for num,ticker in enumerate(ticker_multi_choice.value): 

        xs = ticker_df_all.index 
        ys = ticker_df_all[ticker,var_select.value].values

        if normalize:
            ys = 100*(ys - ys[0])/ys[0]

        # add a line renderer
        p.line(x=xs,y=ys,line_width=2, legend_label = ticker, color=colors_list[ticker]) 

    p.legend.location = 'top_left'

    p.legend.title = 'Stock'
    p.legend.title_text_font_style = "bold"
    p.legend.title_text_font_size = "12px"

    return p


def update_var(attr, old, new):
    #need to only recreate the figure, not update the dataframe
    layout.children[1] = create_figure()

def update_normalization(status):
    #need to only recreate the figure, not update the dataframe
    layout.children[1] = create_figure()

def update_ticker_list(attr, old, new):
    #need to only recreate the figure, not update the dataframe
    layout.children[1] = create_figure()

#Initialize the control widgets

avail_vars = ['1. open', '2. high', '3. low', '4. close', '5. adjusted close', '6. volume', '7. dividend amount', '8. split coefficient']

var_select = Select(title='Quantity of interest:', value='1. open', options=avail_vars, margin=(10,20,10,0)) 
var_select.on_change('value',update_var)


all_tickers = ['AAPL', 'GOOG', 'MSFT', 'FB', 'PFE', 'MRNA', 'JNJ', 'AZN']

colors_list = {'AAPL':'black','GOOG':'red','MSFT':'green','FB':'blue','PFE':'orange','MRNA':'purple','JNJ':'brown','AZN':'grey'}

ticker_multi_choice = MultiChoice(title='Stocks of interest: ', options=all_tickers, value=['AAPL', 'GOOG', 'PFE', 'JNJ'], margin=(10,20,30,0), height=150) 

ticker_multi_choice.on_change("value", update_ticker_list) 


toggle_normalization = Toggle(label='Normalize',active=True, margin=(10,20,30,0))
toggle_normalization.on_click(update_normalization)

controls = column(ticker_multi_choice, var_select, toggle_normalization, width=200, height=600)

#create dataframe by querying Alpha Vantage for all tickers of potential interest

starting_text = 'Starting Alpha Vantage API'
print(starting_text)
ticker_df_all = create_ticker_df_all()

layout = row(controls, create_figure())

curdoc().add_root(layout)


#doc.add_root(layout)
#
# #The following theme has gray background with white dashed grid lines
# doc.theme = Theme(filename="theme.yaml")

    
# @app.route('/', methods=['GET'])
# def stock_query_viz_app_page():
#     script = server_document('http://localhost:5006/stock_query_viz_app')
#     return render_template('about_stock_viz.html', script=script, template="Flask")

# def bk_worker():
#     # Can't pass num_procs > 1 in this configuration. If you need to run multiple
#     # processes, see e.g. flask_gunicorn_embed.py
#     server = Server({'/stock_query_viz_app': stock_query_viz_app}, io_loop=IOLoop(), allow_websocket_origin=["localhost:8000"])
#     server.start()
#     server.io_loop.start()

# #Thread(target=bk_worker).start()

# #if __name__ == '__main__':
# #    print('Opening single process Flask app with embedded Bokeh application on http://localhost:8000/')
# #    print()
# #    print('Multiple connections may block the Bokeh app in this configuration!')
# #    print('See "flask_gunicorn_embed.py" for one way to run multi-process')
# #    app.run(port=8000)


# #Original template from TDI:

# # @app.route('/')
# # def index():
# #   return render_template('index.html')

# # @app.route('/about')
# # def about():
# #   return render_template('about.html')

# # if __name__ == '__main__':
# #   app.run(port=33507)
