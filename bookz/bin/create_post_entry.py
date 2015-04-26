from bookz.model import session_scope
from bookz.tests import test_model


def create_post_entry(email='itissid@gmail.com', seller_name='Sidharth G    upta'):
    with session_scope() as session:
        test_model.create_random_seller_entry(session, email=email, seller_name=seller_name)
    return True