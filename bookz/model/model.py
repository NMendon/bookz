from sqlalchemy import Column, Integer, String, Sequence, ForeignKey, DateTime, Boolean, Numeric
from sqlalchemy.orm import relationship
from bookz.model import Base

import datetime

class Seller(Base):
    __tablename__ = 'seller'

    id = Column(Integer, Sequence('seller_id_seq'), primary_key=True, autoincrement=True)
    # TODO: keeping just the name for now. Ideally we may want this to be first and last name
    name = Column(String(100), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    posts = relationship("Post", backref="seller")

    def __init__(self, name=None, email=None):
        self.name = name
        self.email = email

    def __repr__(self):
        return '<Seller %d %r>' % (self.id if self.id else -1, self.name)

class Book(Base):
    __tablename__ = 'book'

    id = Column(Integer, Sequence('book_id_seq'), primary_key=True)
    course_books = relationship("CourseBook", backref='book')

    name = Column(String(100), nullable=False)
    author = Column(String(100), nullable=False)
    edition = Column(String(100))
    # Note the default
    ean = Column(Integer, default=-1)
    def __init__(self, name=None, author=None, edition=None, ean=None):
        self.name = name
        self.author = author
        self.edition = edition
        self.ean = ean

    def __repr__(self):
        return '<Book %d %r %r %r, %r>' % (self.id if self.id else -1, self.name, self.author, self.edition, self.ean)

class Course(Base):
    __tablename__ = 'course'
    id = Column(Integer, Sequence('course_id_seq'), primary_key=True)
    course_books = relationship("CourseBook", backref='course')

    name = Column(String(100), nullable=False)
    desc = Column(String(200))

    def __init__(self, name=None, desc=None):
        self.name = name
        self.desc = desc

    def __repr__(self):
        return '<Book %d %r %r>' % (self.id if self.id else -1, self.name, self.desc)

class CourseBook(Base):
    __tablename__ = 'course_book'
    id = Column(Integer, Sequence('course_id_seq'), primary_key=True)
    course_id = Column(Integer, ForeignKey('course.id'), nullable=False)
    book_id = Column(Integer, ForeignKey('book.id'), nullable=False)

    # Note there is no back ref as in the Posts as its perfectly ok for an entry to exist here without one
    # in the Post table.
    posts = relationship("Post")

    def __init__(self, course_id=None, book_id=None):
        self.course_id = course_id
        self.book_id = book_id

    def __repr__(self):
        return '<CourseBook %d %d %d>' % (
            self.id if self.id else -1,
            self.course_id if self.course_id else -1,
            self.book_id if self.book_id else -1)

class Post(Base):
    __tablename__ = 'post'

    id = Column(Integer, Sequence('post_id_seq'), primary_key=True)
    seller_id = Column(Integer, ForeignKey('seller.id'), nullable=False)
    course_book_id = Column(Integer, ForeignKey('course_book.id'), nullable=False)
    comments = Column(String(500))
    created_date = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    price = Column(Numeric, nullable=False)
    # TODO: Change field in original model
    is_sold = Boolean(name='is_sold_constraint')
    last_modified_date = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    def __init__(self, seller_id=None, course_book_id=None, comments=None, price=None,
                 created_date=None, last_modified_date=None):
        self.seller_id = seller_id
        self.course_book_id = course_book_id
        self.comments = comments
        self.created_date = created_date
        self.price = price
        self.last_modified_date = last_modified_date

    def __repr__(self):
        return '<Post %d %d %s %d %r %r>' % (
            self.id or -1, self.seller_id or -1,
            self.course_book_id or -1, self.price,
            self.comments or '', self.created_date or '')

