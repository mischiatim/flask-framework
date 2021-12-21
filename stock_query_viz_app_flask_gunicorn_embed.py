#simple version to interact with the standalone Bokeh server hosted in a separate heroku app, as suggested in: 
#https://discourse.bokeh.org/t/bokeh-server-embedded-in-gunicorn-flask-hosted-to-cloud/6199

from flask import Flask, render_template
from bokeh.embed import server_session #,server_document
from bokeh.client import pull_session

BOKEH_URL = "https://stock-query-viz-bokeh.herokuapp.com/stock_query_viz_app_bokeh_standalone"


app = Flask(__name__)


@app.route('/', methods=['GET'])
def stock_query_viz_app_page():
    with pull_session(url=BOKEH_URL) as session:
        script = server_session(session_id=session.id, url=BOKEH_URL)
        return render_template('about_stock_viz.html', script=script, template="Flask")


if __name__ == '__main__':
    print('This script is intended to be run with gunicorn. e.g.')
    print()
    print('    gunicorn -w 4 stock_query_viz_app_flask_gunicorn_embed:app')
    print()
    print('will start the app on four processes')
    import sys
    sys.exit()
    
