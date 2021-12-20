# Stock Visualization App on Heroku using Bokeh server app integrated within a Flask app  

This project is a simple exercise to test how an interactive Bokeh server application (with Python callbacks) 
can be integrated within a Flask app for deployment on Heroku.
The Bokeh app reads recent historical data from a few stocks (pharmaceutical and technology) using the Alpha Vantage API,
and plots them within an interactive window. A few widgets can be used to change the stocks or variables shown.
The finished product is the Heroku app: https://stock-query-viz.herokuapp.com

Combining Bokeh server app + Flask app is tricky on Heroku.
I adopted the solution from the following repository:
https://github.com/hmanuel1/covid/tree/master/app/utest
(See also the discussion at https://discourse.bokeh.org/t/hosting-a-flask-bokeh-server-app-in-heroku/5490/8.)

## Technical Description

This application wraps the Flask App into Tornado framework. Implements a HTTP reverse-proxy using Flask and a Web Socket reverse-proxy using Tornado.
The files `Procfile`, `requirements.txt`, and `runtime.txt` were set appropriately for use by Heroku, before pushing the repository to Heroku using Heroku CLI
A useful reference is the Heroku [quickstart guide](https://devcenter.heroku.com/articles/getting-started-with-python).

## Instructions for locally testing the application combining Bokeh server app + Flask app as a single command:

1. Open config.yaml file and change "heroku" to "local" in first line and save it.
2. In your terminal run the following command:

``` Python
python run.py
```

3. Open http://127.0.0.1:8000/ in your internet browser to see Bokeh App embedded into Flask framework.

## Instructions for locally testing each application (Bokeh server app + Flask app) independently

1. Open config.yaml file and change "heroku" to "local" in first line and save it.
2. In your terminal run the following command:

``` Python
python bkapp.py
```

3. Open the url displayed in your terminal with your internet browser to see the Bokeh server app.

4. Open a second terminal session without closing the one running bkapp.py and run the following command from the same directory.

``` Python
python app.py
```

5. Open http://127.0.0.1:8000/ in your internet browser to see Bokeh server app embedded into Flask framework.

## Notes

I first followed the instructions provided in the Bokeh documentation:
https://github.com/bokeh/bokeh/blob/2.4.0/examples/howto/server_embed/flask_gunicorn_embed.py
for embedding Bokeh server app within a Flask app, but this did not work when deployed to Heroku.
See file 'stock_query_viz_app_flask_gunicorn_embed.py'.
This version was supposed to run by calling 'gunicorn -w 4 stock_query_viz_app_flask_gunicorn_embed:app' (see Procfile_gunicorn). 

I also created a version in which the Bokeh app is standalone: stock_query_viz_app_bokeh_standalone.py
This version must be run by calling 'bokeh serve --show stock_query_viz_app_bokeh_standalone' for local testing, 
and works when deployed on Heroku by renaming the file stock_query_viz_app_bokeh_standalone.py as 'main', 
creating a Heroku app 'stock-query-viz-bokeh.herokuapp.com' tied to the repository
and specifying the following command in 'Procfile' (see Procfile_bokeh_standalone):
web: bokeh serve --port=$PORT --allow-websocket-origin=stock-query-viz-bokeh.herokuapp.com --address=0.0.0.0 --use-xheaders stock_query_viz_app_bokeh_standalone

Finally, there is another version of the Flask app for local testing: see stock_query_viz_app_flask_embed.py
This was created following the Bokeh documentation in:
https://github.com/bokeh/bokeh/blob/2.4.0/examples/howto/server_embed/flask_embed.py, 
and works (locally) by calling 'python stock_query_viz_app_flask_embed.py' and opening http://localhost:8000/ in a web browser.