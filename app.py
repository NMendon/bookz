from bookz.utils.forms import BookForm
from flask import Flask, request, render_template, session, redirect, flash
from requests_oauthlib import OAuth2Session
import requests
import datetime as dt

from bookz.utils import oauth_utils
from bookz.model import session_scope
from bookz.model.model import Book, Course, CourseBook, Post, Seller
from bookz.model import dal

app = Flask(__name__, template_folder='bookz/templates', static_folder="bookz/static")
import os
import json

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
    # We use this provider everywhere to get the oauth token
    # Perhaps we should encapsulate it?
    session['provider'] = provider
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
            _LOGGER.info("User already exists %s" % that_user)
            seller_id = that_user.id

    session['seller_id'] = seller_id
    results = []
    with session_scope() as db_session:
        res = db_session.query(Post.id,  Course.name, Book.name, Book.author, Book.edition, Post.price, Post.last_modified_date).\
            join(CourseBook, Post.course_book_id==CourseBook.id).\
            join(Course, Course.id==CourseBook.course_id).\
            join(Book, Book.id==CourseBook.book_id).\
            filter(Post.seller_id==seller_id).\
            filter(Post.status == 'A').all()
        for post_id, course_name, book_name, author, edition, price, lmd in res:
            results.append({
                'post_id': post_id,
                'book_name': book_name,
                'author': author,
                'edition': edition,
                'course_name': course_name,
                'price': price,
                'last_modified_date': lmd.strftime('%m/%d/%Y')
            })

    return render_template(
        'sellers_page.html', user_info=user_info, results=results, provider=provider)

@app.route('/seller/add_book', methods=["GET", "POST"])
def add_book():
    oauth_token = session.get('oauth_token')
    if oauth_token is None or not session.get('seller_id', None):
        return redirect('authorization/' + session['provider'])
    # Else return the page with the list of courses loaded in
    if request.method == "POST":
        if not request.form:
            raise ValueError("Expected a form in the request")
        _LOGGER.info(request.form)
        form = BookForm(request.form)
        if form.validate():
            with session_scope() as db_session:
                cbid = db_session.query(CourseBook.id) \
                    .filter(CourseBook.course_id==int(form.course.data)) \
                    .filter(CourseBook.book_id==int(form.book.data)).all()
                if cbid and cbid[0]:
                    post = Post(
                        seller_id=session.get('seller_id'),
                        course_book_id=cbid[0][0], comments=form.comments.data, price=form.price.data,
                        created_date=dt.datetime.utcnow(), last_modified_date=dt.datetime.utcnow())
                    db_session.add(post)
                else:
                    raise ValueError(
                        "Uh oh.. cbid not found for course_id = %s book_id = %s" %(
                        form.course.data, form.book.data))
            return redirect('/seller_page/' + session['provider'])
        else:
            _LOGGER.warn("Errors: %s " % form.errors)
            return render_template('add_book.html', form=form, form_errors=form.errors)
    elif request.method == "GET":
        return render_template('add_book.html')

@app.route('/courses/get_courses', methods=['GET'])
def fetch_courses():
    oauth_token = session.get('oauth_token')
    if oauth_token is None:
        return redirect('authorization/' + session['provider'])
    if not session.get('courses', None):
        courses = []
        with session_scope() as db_session:
            res = db_session.query(Course.id, Course.name, Course.desc)
            for _id, name, desc in res:
                courses.append({"id": _id, "name": name, "desc": desc})
        session['courses'] = courses
    return json.dumps(session.get('courses'))

@app.route('/courses/get_books', methods=["GET"])
def fetch_course_books():
    app.logger.info(request)
    oauth_token = session.get('oauth_token')
    if oauth_token is None:
        return redirect('authorization/' + session['provider'])
    if not session.get('courses', None):
        raise ValueError('Looks like you navigated to this route before calling /seller/add_book')
    # Now get the books
    results = []
    with session_scope() as db_session:
        res = db_session.query(
            Book.id, Book.name, Book.author, Book.ean, Book.edition).join(
                CourseBook).filter(CourseBook.course_id == request.args.get('course')).all()
        for book_id, name, author, ean, edition in res:
            results.append({
                "id": book_id,
                "name": name,
                "author": author,
                "ean": ean,
                "edition": edition
            })

    return json.dumps(results)

@app.route('/seller_page/delete_post/<post_id>', methods=["GET", "POST"])
def delete_post(post_id):
    oauth_token = session.get('oauth_token')
    seller_id = session.get('seller_id', None)
    if oauth_token is None or not seller_id:
        return redirect('authorization/' + session['provider'])
    dal.deactivate_post_from_id(post_id, seller_id)
    return redirect('seller_page/' + session['provider'])

@app.route('/seller_page/edit_post/<post_id>', methods=["GET", "POST"])
def edit_post(post_id):
    """
    Based on the post_id and the seller_id we update the post
    :param post_id:
    :return:
    """
    oauth_token = session.get('oauth_token')
    session_id = session.get('seller_id', None)
    if oauth_token is None or not session_id:
        return redirect('authorization/' + session['provider'])
    if request.method == "GET":
        with session_scope() as db_session:
            res = db_session.query(
                    CourseBook.course_id, Course.name.label('course_name'), CourseBook.book_id,
                    Book.name.label('book_name'), Book.author,
                    Book.ean, Book.edition, Post.comments, Post.price).\
                join(Course, Course.id==CourseBook.course_id).\
                join(Post, Post.course_book_id==CourseBook.id).\
                join(Book, Book.id==CourseBook.book_id).\
                filter(Post.id == post_id).\
                filter(Post.seller_id == session_id).\
                all()
            if res and res[0]:
                _LOGGER.info(res[0])
                return render_template('edit_post.html', post={
                    'post_id': post_id,
                    'book': {
                        'id': res[0].book_id,
                        'name': res[0].book_name
                    },
                    'course': {
                        'id': res[0].course_id,
                        'name': res[0].course_name
                    },
                    'author': res[0].author,
                    'edition': res[0].edition,
                    'price': res[0].price,
                    'comments': res[0].comments,
                    'provider': session['provider']
                })

            else:
                return redirect('seller_page'+session['provider'])
    elif request.method == "POST":
        if not request.form:
            raise ValueError("Expected a form in the request")
        form = BookForm(request.form)
        if form.validate():
            dal.update_post_from_id(
                post_id, session['seller_id'], price=form.price.data,
                book_id=form.book.data, course_id=form.course.data, comments=form.comments.data)
        elif 'price' in form.errors and len(form.errors) == 1:
            # The price was incorrect
            flash('%s (Price)' % form.errors['price'][0])
            _LOGGER.info("Could not validate form %s" % form.errors)
        # TODO: display an error message instead?
        return redirect('seller_page/' + session['provider'])


######## Utility methods to start stop a server ###########
# Also the main tox entry point. Make sure you export these incase you are gonna start things from the outside
def start_server():

    #### TODO: Remove these once you have SSL set up###
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = 'True'
    #### Remove the above when SSL is set up####

    ### TODO: Abstract this ugliness using some injection mechanism
    app.config.from_envvar("APP_CONFIG_FILE")
    # TODO: Use google's secret key.. for now..
    oauth_config = oauth_utils.get_oauth_config_wrapper(app, "google")
    app.secret_key = oauth_config.client_secret
    app.config['SECRET_KEY']  = oauth_config.client_secret
    app.config['SESSION_TYPE'] = 'filesystem'
    # Set up logging based on what was set
    import logging
    from bookz.utils import logging_utils as lu
    #if app.config['LOGGING_CONFIG_FILE']:
    #    lu.setup_logging(app.config['LOGGING_CONFIG_FILE'])
    global _LOGGER
    _LOGGER = app.logger
    #else:
    #    raise ValueError("Did not find LOGGING_CONFIG_FILE in the app config")
    app.run(debug=True if app.config['DEBUG'] == 'True' else False)

# TODO: get the server port and append it instead of hardcoding it...
def stop_server():
    try:
        requests.post(
            'http://127.0.0.1:5000/shutdown')
    except requests.exceptions.ConnectionError as e:
        print 'Not detecting a started server..'

if '__main__' in __name__:
    start_server()
