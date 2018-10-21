# -*- coding: utf-8 -*-
import os
import sys
from os import path
import flask
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
from flask import request

if __package__ is None:
    sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
else:
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from core.youtube import YouTube
from core.spotify import Spotify
from core.constants import sp_username, html_path
import spotipy
import spotipy.util as util

youtube_path = os.path.dirname(__file__)
# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret.

CLIENT_SECRETS_FILE = os.path.join(youtube_path, "client_secrets.json")

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ['https://www.googleapis.com/auth/youtube']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

app = flask.Flask(__name__)
# Note: A secret key is included in the sample so that it works, but if you
# use this code in your application please replace this with a truly secret
# key. See http://flask.pocoo.org/docs/0.12/quickstart/#sessions.
app.secret_key = os.environ['WOLFG_FLASK_KEY']
scope = 'playlist-modify-public'  # Spotify


class WebInterface(object):
    pass


dj_set_if = WebInterface()
dj_set_if.cmd = '/dj_set'
dj_set_if.parameters = ['dj', 'input_date', 'platform', 'input_date_operator']
dj_set_if.labels = ['DJ', 'Input date', 'Platform']


def init():
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')


@app.route('/', methods=['GET', 'POST'])
def index():
    # if 'credentials' not in flask.session:
    #     return flask.redirect('authorize')
    with open(html_path, 'r') as html_file:
        html_content = html_file.read()
    return html_content.format(parameter_dj = 'dj', charts_cmd = '/charts')


@app.route(dj_set_if.cmd, methods=['GET', 'POST'])
def klaus():
    dj = request.args.get(dj_set_if.parameters[0], type = str).lower()
    input_date = request.args.get(dj_set_if.parameters[1], default = dj_set_if.parameters[1], type = str)
    input_date_operator = request.args.get(dj_set_if.parameters[3], default = dj_set_if.parameters[1], type = str)
    platform = request.args.get(dj_set_if.parameters[2], default = dj_set_if.parameters[2], type = str).lower()

    if platform in ['all', 'yt']:
        yt = get_yt()
        yt.dj_set(dj, input_date, input_date_operator)

    if platform in ['all', 'sp']:
        sp.dj_set(dj, input_date, input_date_operator)

    return 'OK'


@app.route('/charts', methods = ['GET', 'POST'])
def aachen():
    dj = request.args.get('dj', type = str).lower()
    year = request.args.get('year', default = '%', type = str)
    limit = request.args.get('limit', default = '100', type = str)
    threshhold = request.args.get('threshhold', default = '1', type = str)
    platform = request.args.get('platform', default = 'all', type = str).lower()
    order = 'descending'

    if platform in ['all', 'yt']:
        yt = get_yt()
        yt.charts(dj, order, year, limit, threshhold)

    if platform in ['all', 'sp']:
        sp.charts(dj, order, year, limit, threshhold)

    return 'OK'


@app.route('/artist_charts', methods = ['GET', 'POST'])
def artist():
    dj = request.args.get('dj', type = str).lower()
    artist = request.args.get('artist', default = '*', type = str)
    platform = request.args.get('platform', default = 'all', type = str).lower()

    if platform in ['all', 'yt']:
        yt = get_yt()
        yt.artist_charts(dj, artist)

    if platform in ['all', 'sp']:
        sp.artist_charts(dj, artist)

    return 'OK'


@app.route('/pl_queue', methods=['GET', 'POST'])
def queue():
    platform = request.args.get('platform', default = 'all', type = str)

    if platform in ['all', 'yt']:
        yt = get_yt()
        yt.pl_queue()

    if platform in ['all', 'sp']:
        sp.pl_queue()

    return 'OK'


def get_yt():
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')
    credentials = google.oauth2.credentials.Credentials(**flask.session['credentials'])
    yt_client = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials = credentials)
    return YouTube(yt_client)


@app.route('/update', methods = ['GET', 'POST'])
def update():
    platform = request.args.get('platform', default = 'all', type = str)
    if platform in ['all', 'yt']:
        yt = get_yt()
        yt.update_pls()

    if platform in ['all', 'sp']:
        sp.update_pls()
        
    return 'OK'


@app.route('/authorize')
def authorize():
    # Create a flow instance to manage the OAuth 2.0 Authorization Grant Flow
    # steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes = SCOPES)
    flow.redirect_uri = flask.url_for('oauth2callback', _external = True)
    authorization_url, state = flow.authorization_url(
        # This parameter enables offline access which gives your application
        # both an access and refresh token.
        access_type = 'offline',
        # This parameter enables incremental auth.
        include_granted_scopes = 'true')

    # Store the state in the session so that the callback can verify that
    # the authorization server response.
    flask.session['state'] = state

    return flask.redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
    # Specify the state when creating the flow in the callback so that it can
    # verify the authorization server response.
    state = flask.session['state']
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes = SCOPES, state = state)
    flow.redirect_uri = flask.url_for('oauth2callback', _external = True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = flask.request.url
    flow.fetch_token(authorization_response = authorization_response)

    # Store the credentials in the session.
    # ACTION ITEM for developers:
    #     Store user's access and refresh tokens in your data store if
    #     incorporating this code into your real app.
    credentials = flow.credentials
    flask.session['credentials'] = {'token': credentials.token,
                                    'refresh_token': credentials.refresh_token,
                                    'token_uri': credentials.token_uri,
                                    'client_id': credentials.client_id,
                                    'client_secret': credentials.client_secret,
                                    'scopes': credentials.scopes}

    return flask.redirect(flask.url_for('index'))


if __name__ == '__main__':
    # When running locally, disable OAuthlib's HTTPs verification. When
    # running in production *do not* leave this option enabled.
    token = util.prompt_for_user_token(sp_username, scope)

    if token:
        sp_client = spotipy.Spotify(auth = token)
        sp = Spotify(sp_client)
    else:
        print "Can't get token for", sp_username

    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '0'
    app.run('localhost', 8090, debug = True)


