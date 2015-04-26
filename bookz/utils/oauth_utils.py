import json
from collections import namedtuple

oath_object = namedtuple(
    'Oauth', [
        'provider', 'client_id', 'client_secret', 'redirect_uri',
        'authorization_base_url', 'token_url',
        'scope', 'user_info_uri'
    ]
)


# Just the config for oauth in the deployed file
# TODO: try extracting this stuff to a class for extensibility
# when you add more oauth clients like FB/Twitter. Lots of things specific to google
def get_oauth_config_wrapper(app, provider):
    # TODO: Read from users opt or from etc based on the env
    with open(app.config['AUTH_JSON']) as f:
        auth = json.load(f)[provider]
        # This is necessary to secure the cookies so users can't see/modify them
        # http://flask.pocoo.org/docs/0.10/quickstart/#sessions
        google_oauth_obj = oath_object(
            provider='Generic provider 'if not provider else provider,
            client_id=auth['client_id'],
            client_secret=auth['client_secret'],
            redirect_uri=auth['redirect_uris'][app.config['ENV']],

            # OAuth endpoints given in the API documentation
            authorization_base_url=auth['authorization_base_url'],
            token_url=auth['token_uri'],
            scope=[
                auth['scope']
            ],
            user_info_uri=auth['user_info_uri']
        )
        return google_oauth_obj