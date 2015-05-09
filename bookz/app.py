from logging.handlers import WatchedFileHandler
from bookz.utils.forms import BookForm, BuyerForm, DeletePostConfirmation
from bookz.utils import logging_utils
from flask import Flask, request, render_template, session, redirect, flash, url_for
from requests_oauthlib import OAuth2Session
import requests
import datetime as dt

from bookz.utils import oauth_utils
from bookz.model import session_scope
from bookz.model.model import Book, Course, CourseBook, Post, Seller
from bookz.model import dal

app = Flask(__name__, template_folder='templates', static_folder="static")
import os
import json

_LOGGER = None


@app.route('/')
def login():
    return render_template('index.html')

@app.route("/logout")
def logout():
    session["__invalidate__"] = True
    return redirect("/")

@app.after_request
def remove_if_invalid(response):
    if "__invalidate__" in session:
        response.delete_cookie(app.session_cookie_name)
        if 'oauth_token' in session:
            session.pop('oauth_token')
        session.pop("__invalidate__")
    return response

@app.route('/buyer', methods=['GET', 'POST'])
def buyer():
    if request.method == 'GET':
        provider = session.get('provider', None)
        _LOGGER.info("Provider: %s" % provider)
        return render_template('buyer.html', provider=provider)
    if request.method == 'POST':
        if not request.form:
            raise ValueError("Expected a form in the request")
        form = BuyerForm(request.form)
        if form.validate():
            res = dal.get_search_results_for_data(
                int(form.course.data), form.book.data, form.author.data, form.edition.data)
            _LOGGER.info("** results %s " % res)
            # If the buyer is also logged in as a seller
            provider = session.get('provider', None)
            _LOGGER.info("Provider: %s" % provider)
            return render_template('buyer_search.html', results=res, provider=provider)
        else:
            _LOGGER.warn("Errors: %s " % form.errors)
            # Get the data for the given information in the form
            provider = session.get('provider', None)
            _LOGGER.info("Provider: %s" % provider)
            return render_template(
                'buyer.html', form=form, form_errors=form.errors, provider=provider)

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
    _LOGGER.debug("Redirect URI: %s ", authorization_url)
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
    # TODO: validate that the provider is in the list of valid providers as well
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
    except Exception as e:
        _LOGGER.info(e)
        return redirect('/authorization/' + provider)
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
    results = dal.get_posts_by_seller_id(seller_id)
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
                cbid = dal.get_course_book_id_by_course_book_name(
                    int(form.course.data), form.book.data, form.author.data, form.edition.data)
                if cbid:
                    post = Post(
                        seller_id=session.get('seller_id'),
                        course_book_id=cbid.pop(), comments=form.comments.data, price=form.price.data,
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

@app.route('/course/get_courses', methods=['GET'])
def fetch_courses():
    # oauth_token = session.get('oauth_token')
    # if oauth_token is None:
    #     return redirect('authorization/' + session['provider'])
    courses = []
    with session_scope() as db_session:
        res = db_session.query(Course.id, Course.name, Course.desc).all()
        _LOGGER.debug("Courses: %s " % res)
        for _id, name, desc in res:
            courses.append({"value": _id, "label": name, "desc": desc})
    return json.dumps(courses)

def _list_dd_json(res):
  return   [{'label': r, 'value': r} for r in res]

@app.route('/course/get_books', methods=["GET"])
def fetch_course_books():
    # app.logger.info(request)
    # oauth_token = session.get('oauth_token')
    # if oauth_token is None:
    #     return redirect('authorization/' + session['provider'])
    course = request.args.get('course')
    if not course:
        raise ValueError('Looks like you navigated to this route incorrectly')
    # Now get the books
    results = []
    with session_scope() as db_session:
        results = dal.get_books_for_course(course)
    _LOGGER.info("Results: %s " % results)
    return json.dumps(_list_dd_json(results))

@app.route('/course/get_author', methods=["GET"])
def fetch_author_for_course_book():
    # app.logger.info(request)
    # oauth_token = session.get('oauth_token')
    # if oauth_token is None:
    #     return redirect('authorization/' + session['provider'])
    course = request.args.get('course')
    book = request.args.get('book')
    if not course or not book:
        _LOGGER.warn('Looks like you navigated to this route incorrectly')
        return ''
    with session_scope() as db_session:
        results = dal.get_author_for_course_id_book_name(course, book)
    return json.dumps(_list_dd_json(results))

@app.route('/course/get_edition', methods=["GET"])
def fetch_editions_for_course_book_author():
    # app.logger.info(request)
    # oauth_token = session.get('oauth_token')
    # if oauth_token is None:
    #     return redirect('authorization/' + session['provider'])
    course = request.args.get('course')
    book = request.args.get('book')
    author = request.args.get('author')
    if not course or not book:
        _LOGGER.warn('Looks like you navigated to this route incorrectly')
        return ''
    with session_scope() as db_session:
        results = dal.get_edition_for_course_id_book_name_author_name(course, book, author)
    return json.dumps(_list_dd_json(results))

_form_reason_map = {
    1: 'S',
    2: 'R',
    3: 'E'
}
@app.route('/seller_page/delete_post/<post_id>', methods=["POST"])
def delete_post(post_id):
    oauth_token = session.get('oauth_token')
    seller_id = session.get('seller_id', None)
    if oauth_token is None or not seller_id:
        return redirect('authorization/' + session['provider'])
    if not request.form:
        raise ValueError("Expect a form")
    form = DeletePostConfirmation(request.form)
    if not form.validate():
        flash('%s' % '\n'.join(form.errors['reason']))
        redirect('seller_page/'+session['provider'])
    else:
        dal.deactivate_post_from_id(
            post_id, seller_id,
            _form_reason_map[int(form.reason.data)])
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
def configure_server():
    #### TODO: Remove these once you have SSL set up###
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = 'True'
    #### Remove the above when SSL is set up####

    ### TODO: Abstract some of this ugliness using some injection mechanism
    app.config.from_envvar("APP_CONFIG_FILE")
    # TODO: Use generic secret key. Use google's secret key.. for now..
    oauth_config = oauth_utils.get_oauth_config_wrapper(app, "google")
    app.secret_key = oauth_config.client_secret
    app.config['SECRET_KEY']  = oauth_config.client_secret
    app.config['SESSION_TYPE'] = 'filesystem'
    app.debug = True if app.config['DEBUG'] == 'True' else False
    # Set up some logging...
    global _LOGGER
    _LOGGER = app.logger
    logging_utils.setup_logging(app)
    print 'Starting the app server'
    return app

# TODO: get the server port and append it instead of hardcoding it...
def stop_server():
    try:
        requests.post(
            'http://127.0.0.1:5000/shutdown')
    except requests.exceptions.ConnectionError as e:
        print 'Not detecting a started server..'
