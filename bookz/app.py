from flask import Flask, request, render_template, session, redirect, url_for
import flask
from requests_oauthlib import OAuth2Session
import requests

from bookz.utils import oauth_utils

app = Flask(__name__) #, template_folder='bookz/templates')
import os

import logging
_LOGGER = logging.getLogger(__name__)

@app.route('/')
def login():
    return render_template('index.html')

@app.route('/shutdown', methods=['POST'])
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server??')
    func()
    return 'Server shutting down...'

# Step 1 redirect user to the provider to ask for his consent
@app.route('/authorization/<provider>')
def authorization(provider):
    oauth_config = oauth_utils.get_oauth_config_wrapper(app, provider=provider)
    google = OAuth2Session(
        oauth_config.client_id, scope=oauth_config.scope,
        redirect_uri=oauth_config.redirect_uri)

    # Redirect user to Google for authorization
    authorization_url, state = google.authorization_url(
        oauth_config.authorization_base_url,
        # online for refresh token
        # force to always make user click authorize
        access_type="online")
    # State is used to prevent CSRF, keep this for later.
    app.logger.debug("Redirect URI: "+authorization_url)
    session['oauth_state'] = state
    return redirect(authorization_url)

# Step 2: If the user authorizes. We ask the provider for a token
# We shall use this tokem
@app.route('/oauth2callback/<provider>', methods=["GET"])
def authorized(provider):
    # This is where the user control flow lands after the user authorizes
    # the app to access their data
    # Note that the full callbackurl from the OAuth provider
    # google, facebook etc will be in the request
    oauth_config = oauth_utils.get_oauth_config_wrapper(app, provider=provider)
    google = OAuth2Session(
        oauth_config.client_id, scope=oauth_config.scope,
        redirect_uri=oauth_config.redirect_uri)
    token = google.fetch_token(
        oauth_config.token_url, client_secret=oauth_config.client_secret,
        authorization_response=request.url)
    session['oauth_token'] = token
    return redirect('seller_page/'+provider)

@app.route('/seller_page/<provider>')
def sellers_page(provider):
    # If we already have the access token we can fetch resources.
    # This means step 3 of the 3 legged oauth handshake was completed.
    # We attempt to display the sellers page with his information
    oauth_config = oauth_utils.get_oauth_config_wrapper(app, provider=provider)
    oauth_token = session.get('oauth_token')
    if oauth_token is None:
        return redirect(url_for('authorization/'+provider))

    # Back here after step 3
    try:
        # TODO: Need this to be based on the type of provider
        google = OAuth2Session(
            client_id=oauth_config.client_id, token=oauth_token)
        user_info_response = google.get(oauth_config.user_info_uri)
    except:
        session['oauth_token'] = google.refresh_token(
                oauth_config.authorization_base_url, client_id=oauth_config.client_id,
                client_secret=oauth_config.client_secret)
        google = OAuth2Session(oauth_config.client_id, token=oauth_token)
        user_info_response = google.get(oauth_config.user_info_uri)

    return render_template(
        'sellers_page.html', user_info=user_info_response.json())

######## Utility methods to start stop a server ###########
# Also the main tox entry point. Make sure you export these incase you are gonna start things from the outside
def start_server():

    #### TODO: Remove these once you have SSL set up###
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = 'True'
    #### Remove the above when SSL is set up####

    ### TODO: Abstract this ugliness using some injection mechanism
    app.config.from_envvar("APP_CONFIG_FILE")
    app.run(debug=True if app.config['DEBUG'] == 'True' else False)
    flask.g['env'] = app.config['ENV']
    # Set up logging based on what was set
    import logging
    from bookz.utils import logging_utils as lu
    if app.config['LOGGING_CONFIG_FILE']:
        lu.setup_logging( app.config['LOGGING_CONFIG_FILE'])
        global _LOGGER
        _LOGGER = logging.getLogger(__name__)
    else:
        raise ValueError("Did not find LOGGING_CONFIG_FILE in the app config")

# TODO: get the server port and append it instead of hardcoding it...
def stop_server():
    try:
        requests.post(
            'http://127.0.0.1:5000/shutdown')
    except requests.exceptions.ConnectionError as e:
        print 'Not detecting a started server..'

if '__main__' in __name__:
    start_server()
