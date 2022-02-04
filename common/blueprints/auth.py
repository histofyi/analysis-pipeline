from flask import Blueprint, current_app, request, make_response, redirect
from authlib.integrations.flask_client import OAuth
from six.moves.urllib.parse import urlencode
import jwt
import datetime
import logging

from common.decorators import check_user, templated


auth_handlers = Blueprint('auth_handlers', __name__)



@auth_handlers.get('/login')
def login__handler():
    return current_app.auth0.authorize_redirect(redirect_uri='http://localhost:5000/auth/callback')


@auth_handlers.get('/logout')
def logout_handler():
    params = {'returnTo': 'http://localhost:5000/', 'client_id': current_app.config['AUTH0_CLIENT_ID']}
    resp = make_response(redirect(current_app.auth0.api_base_url + '/v2/logout?' + urlencode(params)))
    resp.delete_cookie(current_app.config['JWT_COOKIE_NAME'])
    return resp


@auth_handlers.route('/callback')
def callback_handler():
    # Handles response from token endpoint
    try:
        current_app.auth0.authorize_access_token()
        resp = current_app.auth0.get('userinfo')
        userinfo = resp.json()
        if userinfo['email'] in current_app.config['USERS']:
            token = jwt.encode(payload=userinfo, key=current_app.config['JWT_SECRET'], algorithm='HS256')
            response = make_response(redirect(current_app.config['LOGIN_REDIRECT_ROUTE']))
            response.set_cookie(current_app.config['JWT_COOKIE_NAME'], token, expires = datetime.datetime.now() + datetime.timedelta(days=30))
            return response
        else:
            return redirect('/auth/not-allowed/users')
    except:
        return redirect('/')


@auth_handlers.get('/not-allowed/<string:privilege>')
@templated('not-allowed')
def not_allowed_handler(privilege):
    return {'privilege': privilege}


