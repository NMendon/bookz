import logging
from bookz.model.model import CourseBook, Post
from bookz.model import session_scope

from datetime import datetime as dt

_LOGGER = logging.getLogger(__name__)

def update_post(post):
    pass

"""
Use this for generating a post ID you want to add to the DB
"""
def post_from_course_book_id(
        seller_id, course_id, book_id, price, comments=None):
    with session_scope() as db_session:
        course_book_id = db_session.query(CourseBook.id) \
            .filter(CourseBook.course_id == course_id) \
            .filter(CourseBook.book_id == book_id).all()
        if course_book_id and len(course_book_id) > 0:
            post = Post(
                seller_id=seller_id,
                course_book_id=course_book_id[0][0], comments=comments, price=price)

def deactivate_post_from_id(post_id, seller_id):
    """
    Deactivate a post based on the post and its seller.
    """
    with session_scope() as db_session:
        db_session.query(Post).filter(Post.id==post_id, Post.seller_id==seller_id).update({
            Post.status: 'D'})

def get_posts_by_seller_id():
    pass

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
