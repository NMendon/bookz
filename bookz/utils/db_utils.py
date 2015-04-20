from contextlib import contextmanager
from sqlalchemy.orm import scoped_session, sessionmaker

def _session_scope_wrapper(engine):
    @contextmanager
    def session_scope():
        """Provide a transactional scope around a series of operations."""
        session = scoped_session(sessionmaker(autocommit=False,
                                             autoflush=False,
                                             bind=engine))
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            print 'Closing a database session'
            session.close()
    return session_scope