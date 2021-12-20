"""
    Embed bokeh server session into a flask framework
    Adapted from bokeh-master/examples/howto/serve_embed/flask_gunicorn_embed.py
"""

import os
import time
import asyncio
import logging
from threading import Thread

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from bokeh import __version__ as bokeh_release_ver
from bokeh.application import Application
from bokeh.application.handlers import FunctionHandler
from bokeh.models import Select, MultiChoice, Toggle #ColumnDataSource, Slider
from bokeh.plotting import figure
#from bokeh.sampledata.sea_surface_temperature import sea_surface_temperature
from bokeh.server.server import BaseServer
from bokeh.server.tornado import BokehTornado
from bokeh.server.util import bind_sockets
from bokeh.themes import Theme
from bokeh.layouts import column, row
from bokeh.resources import get_sri_hashes_for_version

#My specific imports
import requests
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar

from config import (
    cwd,
    set_bokeh_port,
    FLASK_PORT,
    FLASK_ADDR,

    BOKEH_ADDR,
    BOKEH_PATH,
    BOKEH_URL,
    BOKEH_CDN
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


BOKEH_BROWSER_LOGGING = """
    <script type="text/javascript">
      Bokeh.set_log_level("debug");
    </script>
"""

def bkapp(doc):
    """ Bokeh App

    Arguments:
        doc {Bokeh Document} -- bokeh document

    Returns:
        Bokeh Document --bokeh document with plots and interactive widgets
    """
    
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
                
                time.sleep(timeout)
                
                try:

                    response = requests.get(url)

                    response_data = response.json() 
            
                    ticker_df = pd.DataFrame.from_dict(response_data['Time Series (Daily)'],orient='index',dtype='float')
                
                    break
                    
                except KeyError:

                    if attempts%3==1:
                        #every few seconds, plot a message to let the user know we are waiting for the query results
                        waiting_text = 'Querying from Alpha Vantage API ' + '...'*timeout
                        print(waiting_text)
                        timeout += 1

                    attempts += 1
                    
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
    
    doc.theme = Theme(filename=os.path.join(cwd(), 'theme.yaml'))
    
    layout = row(controls, create_figure())
    
    return doc.add_root(layout)


def bokeh_cdn_resources():
    """Create script to load Bokeh resources from CDN based on
       installed bokeh version.

    Returns:
        script -- script to load resources from CDN
    """
    included_resources = [
        f'bokeh-{bokeh_release_ver}.min.js',
        f'bokeh-api-{bokeh_release_ver}.min.js',
        f'bokeh-tables-{bokeh_release_ver}.min.js',
        f'bokeh-widgets-{bokeh_release_ver}.min.js'
    ]

    resources = '\n    '
    for key, value in get_sri_hashes_for_version(bokeh_release_ver).items():
        if key in included_resources:
            resources += '<script type="text/javascript" '
            resources += f'src="{BOKEH_CDN}/{key}" '
            resources += f'integrity="sha384-{value}" '
            resources += 'crossorigin="anonymous"></script>\n    '

    resources += BOKEH_BROWSER_LOGGING
    return resources


def  get_sockets():
    """bind to available socket in this system

    Returns:
        sockets, port -- sockets and port bind to
    """
    _sockets, _port = bind_sockets('0.0.0.0', 0)
    set_bokeh_port(_port)
    return _sockets, _port


def bk_worker(sockets, port):
    """ Worker thread to  run Bokeh Server """
    _bkapp = Application(FunctionHandler(bkapp))
    asyncio.set_event_loop(asyncio.new_event_loop())

    websocket_origins = [f"{BOKEH_ADDR}:{port}", f"{FLASK_ADDR}:{FLASK_PORT}"]
    bokeh_tornado = BokehTornado({BOKEH_PATH: _bkapp},
                                 extra_websocket_origins=websocket_origins,
                                 **{'use_xheaders': True})

    bokeh_http = HTTPServer(bokeh_tornado, xheaders=True)
    bokeh_http.add_sockets(sockets)
    server = BaseServer(IOLoop.current(), bokeh_tornado, bokeh_http)
    server.start()
    server.io_loop.start()


if __name__ == '__main__':
    bk_sockets, bk_port = get_sockets()
    t = Thread(target=bk_worker, args=[bk_sockets, bk_port], daemon=True)
    t.start()
    bokeh_url = BOKEH_URL.replace('$PORT', str(bk_port))
    log.info("Bokeh Server App Running at: %s", bokeh_url)
    while True:
        time.sleep(0.05)
