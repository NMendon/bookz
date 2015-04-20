from flask import Flask, request, render_template, session, redirect, url_for
import flask
from requests_oauthlib import OAuth2Session
import requests

from bookz.utils import oauth_utils
from bookz.model import session_scope
from bookz.model.model import Book, Course, CourseBook, Post, Seller

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
# We shall use this token
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
        return redirect('authorization/'+provider)

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
    user_info=user_info_response.json()

    seller_id = None

    with session_scope() as db_session:
        this_user = Seller(name=user_info['name'], email=user_info['email'])
        that_user = db_session.query(Seller).filter_by(email=user_info['email']).first()
        if not that_user or that_user.email != user_info['email']:
            db_session.add(this_user)
            db_session.flush() # We need this ID
            _LOGGER.warn("Adding a user {} to the session".format(that_user))
            seller_id = this_user.id
        else:
            _LOGGER.info("User already exists", that_user)
            seller_id = that_user.id


    results = []
    with session_scope() as db_session:
        res = db_session.query(Post.course_book_id, Course.name, Book.name, Book.author, Book.edition, Post.price, Post.last_modified_date).\
            join(CourseBook, Post.course_book_id==CourseBook.id).\
            join(Course, Course.id==CourseBook.course_id).\
            join(Book, Book.id==CourseBook.book_id).\
            filter(Post.seller_id==seller_id).all()
        for _, course_name, book_name, author, edition, price, lmd in res:
            results.append({
                'book_name': book_name,
                'author': author,
                'edition': edition,
                'course_name': course_name,
                'price': price,
                'last_modified_date': lmd.strftime('%m/%d/%Y')
            })

    return render_template(
        'sellers_page.html', user_info=user_info, results=results)

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
    oauth_config = oauth_utils.get_oauth_config_wrapper(app, None)
    app.secret_key = oauth_config.client_secret
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

######### For database session to be removed when the application shuts down. #########
from bookz.model import db_session


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


if '__main__' in __name__:
    start_server()
