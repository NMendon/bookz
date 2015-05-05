from bookz.app import configure_server

if '__main__' in __name__:
    """
    Only for local debugging mode!
    """
    _app = configure_server()
    _app.run()