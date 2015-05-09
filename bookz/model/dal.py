import logging
from bookz.model.model import CourseBook, Post, Book, Course, Seller
from bookz.model import session_scope

from datetime import datetime as dt

_LOGGER = logging.getLogger(__name__)


def post_from_course_book_id(
        seller_id, course_id, book_id, price, comments=None):
    """
    Use this for generating a post ID you want to add to the DB
    """
    with session_scope() as db_session:
        course_book_id = db_session.query(CourseBook.id) \
            .filter(CourseBook.course_id == course_id) \
            .filter(CourseBook.book_id == book_id).all()
        if course_book_id and len(course_book_id) > 0:
            post = Post(
                seller_id=seller_id,
                course_book_id=course_book_id[0][0], comments=comments, price=price)


def deactivate_post_from_id(post_id, seller_id, status='D'):
    """
    Deactivate a post based on the post and its seller.
    """
    with session_scope() as db_session:
        db_session.query(Post).filter(Post.id==post_id, Post.seller_id==seller_id).update({
            Post.status: status})


def get_posts_by_seller_id(seller_id, active=set('A')):
    """
    Returns the seller's posts(only returns the active ones by default.
    """
    results = []
    with session_scope() as db_session:
        res = db_session.query(Post.id,  Course.name, Book.name, Book.author, Book.edition, Post.price, Post.comments,
                               Post.last_modified_date). \
            join(CourseBook, Post.course_book_id == CourseBook.id). \
            join(Course, Course.id == CourseBook.course_id). \
            join(Book, Book.id == CourseBook.book_id). \
            filter(Post.seller_id == seller_id). \
            filter(Post.status == 'A').all()
        for post_id, course_name, book_name, author, edition, price, comments, lmd in res:
            results.append({
                'post_id': post_id,
                'book_name': book_name,
                'author': author,
                'edition': edition,
                'course_name': course_name,
                'price': price,
                'comments': comments,
                'last_modified_date': lmd.strftime('%m/%d/%Y')
            })
    return results


def update_post_from_id(post_id, seller_id, price, book_id, course_id, comments=None):
    """
    Given a unique post ID update this function updates it. This is a routine for updating a post for a user.
    """
    with session_scope() as db_session:
        course_book_id = db_session.query(CourseBook.id) \
            .filter(CourseBook.course_id == course_id) \
            .filter(CourseBook.book_id == book_id).all()
        if course_book_id and len(course_book_id) > 0:
            db_session.query(Post).filter(Post.id==post_id, Post.seller_id==seller_id).update({
                'course_book_id': course_book_id[0][0],
                'comments': comments, 'price': price,
                'last_modified_date': dt.utcnow()})
        else:
            raise ValueError(post_id, seller_id, price, book_id, course_id, comments)
            _LOGGER.warn("No course book id found")


def get_books_for_course(course_id):
    """
    Return books for a specified course id
    """
    s = set()
    with session_scope() as db_session:
        res = db_session.query(Book.name).\
            join(CourseBook, CourseBook.book_id == Book.id).\
            filter(CourseBook.course_id == course_id).all();
        s.update(r.name for r in res)
    return s


def get_author_for_course_id_book_name(course_id, book_name):
    s = set()
    with session_scope() as db_session:
        res = db_session.query(Book.author).\
            join(CourseBook, CourseBook.book_id == Book.id).\
            filter(Book.name == book_name). \
            filter(CourseBook.course_id == course_id).\
            all();
        s.update(r.author for r in res)
    return s


def get_edition_for_course_id_book_name_author_name(course_id, book_name, author_name):
    s = set()
    with session_scope() as db_session:
        res = db_session.query(Book.edition).\
            join(CourseBook, CourseBook.book_id == Book.id).\
            filter(Book.name == book_name). \
            filter(CourseBook.course_id == course_id).\
            filter(Book.author == author_name).\
            all();
        s.update(r.edition for r in res)
    return s


def get_course_book_id_by_course_book_name(course_id, book_name, author_name, edition):
    s = set()
    with session_scope() as db_session:
        res = db_session.query(CourseBook.id).\
            join(Book, Book.id == CourseBook.book_id). \
            join(Course, Course.id == CourseBook.course_id). \
            filter(Book.name == book_name). \
            filter(CourseBook.course_id == course_id).\
            filter(Book.author == author_name). \
            filter(Book.edition == edition).\
            all();
        s.update(r.id for r in res)
    return s


def get_search_results_for_data(course_id, book_name, author_name, edition):
    if course_id is None:
        raise ValueError('Course ID cannot be empty')
    res = []
    with session_scope() as db_session:
        query_builder = db_session.query(
                CourseBook.id, Book.name.label('book_name'), Book.author, Book.edition,
                Course.name.label('course_name'), Post.price, Post.comments, Post.last_modified_date,
                Seller.email).\
            join(Post, Post.course_book_id == CourseBook.id).\
            join(Seller, Seller.id == Post.seller_id).\
            join(Book, Book.id == CourseBook.book_id). \
            join(Course, Course.id == CourseBook.course_id).\
            filter(CourseBook.course_id == course_id).\
            filter(Post.status == 'A')
        if book_name:
            query_builder = query_builder.filter(Book.name == book_name)
        if author_name:
            query_builder = query_builder.filter(Book.author == author_name)
        if edition:
            query_builder = query_builder.filter(Book.edition == edition)
        # TODO: probably munge the email into backend anonymized thingy..
        for r in query_builder.all():
            res.append({
                'book_name': r.book_name,
                'author': r.author,
                'edition': r.edition,
                'course_name': r.course_name,
                'price': r.price,
                'comments': r.comments,
                'last_modified_date': r.last_modified_date.strftime('%m/%d/%Y'),
                'email': r.email
            })
    return res
