from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

from bookz.utils.db_utils import _session_scope_wrapper

# TODO: Probably change this out for the location of the real DB Server
# Best way to do this is through some external config/ENV vars set at
# deploy time.
engine = create_engine('sqlite:////tmp/test.db', convert_unicode=True)

# import this context manager where you do your model querying
session_scope = _session_scope_wrapper(engine)
Base = declarative_base()

# Hmm not sure why these 2 lines are needed when I copied it
with session_scope() as db_session:
    Base.query = db_session.query_property()


def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    import bookz.model.model
    Base.metadata.create_all(bind=engine)