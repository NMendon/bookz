from contextlib import contextmanager
from sqlalchemy.orm import scoped_session, sessionmaker
import logging
_LOGGER = logging.getLogger(__name__)

def _session_scope_wrapper(engine):
    @contextmanager
    def session_scope():
        """Provide a transactional scope around a series of operations."""
        _LOGGER.debug('Opening a database session')
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
            _LOGGER.debug('Closing a database session')
            session.close()
    return session_scope