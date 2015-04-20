from bookz.model import init_db
from bookz.model.model import Book, Course, CourseBook, Post, Seller

from sqlalchemy import and_

import logging
import random

def create_random_seller_entry(
        db_session,
        seller_name='Namrata Mendon', email='numi@gmail.com',
        book_name_prefix='Stats', course_name_prefix='Statistics',
        course_name_override=None, book_name_override=None,
        logger=logging.getLogger(__name__)):
    """
    For a fixed given seller
    """
    init_db()
    this_user = Seller(seller_name, email=email)

    that_user = db_session.query(Seller).filter_by(email=email).first()

    if not that_user or that_user.email != this_user.email:
        db_session.add(this_user)
        db_session.flush() # We need this ID
        logger.warn("Adding a user {} to the session".format(that_user))
        that_user = this_user
    else:
        logger.info("User already exists", that_user)

    random_course_name = '%s-%d' % (course_name_prefix, random.randint(4000, 4999))
    this_course = Course(name=random_course_name,
               desc='This is '+random_course_name)
    random_book_name = '%s-%d' % (book_name_prefix, random.randint(4000, 4999))
    this_book = Book(name=random_book_name, author='Sensei', edition=random.randint(1,3), ean=random.randint(1000, 100000))

    that_course = is_present(Course, Course.name, random_course_name, this_course, db_session)
    that_book = is_present(Book, Book.name, random_book_name, this_book, db_session)

    if that_course:
        logger.warn("Found the course {}".format(that_course))
    else:
        db_session.add(this_course)
        db_session.flush()
        that_course = this_course
    if that_book:
        logger.warn("Found the book {}".format(that_book))
    else:
        db_session.add(this_book)
        db_session.flush()
        that_book = this_book

    this_course_book = CourseBook(
                book_id=that_book.id,
                course_id=that_course.id)

    # Check if the course book entry was present. If a CourseBook entry was not found for the given book.id & course.id
    # we insert it into the table
    that_course_book = db_session.query(CourseBook).filter(
        and_(CourseBook.book_id == that_book.id and CourseBook.course_id == that_course.id)).all()

    cb_is_present = False
    if that_course_book:
        logger.info("Already extant course-book entry")
    else:
        # Just create the row for now. But ideally you should check why that wor
        db_session.add(this_course_book)
        db_session.flush()
        that_course_book = this_course_book

    # Create a post for this seller
    # At this point we should have a un
    print '**Seller id: ', that_user.id
    post = Post(
        seller_id=that_user.id,
        course_book_id=that_course_book.id,
        comments="Test entry #%d" % (random.randint(0, 9999)))

    db_session.add(post)
    db_session.flush()

    print 'For Seller %s Book %s and Course %s Created a post entry %s'% (this_user, that_book, that_course, post)
    return post

def is_present(entity, entity_attr, val, target, db_session):
    for j in db_session.query(entity).filter(entity_attr.is_(val)).all():
        if target is j:
            return j
    return False
