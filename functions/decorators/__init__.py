from flask import g, request, redirect
from functools import wraps
import jwt

import logging



def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get(g.jwt_cookie_name)
        if token:
            decoded = jwt.decode(token, key=g.jwt_secret, algorithms=["HS256"])
        else:
            decoded = None
        if decoded:
            if decoded['email'] in g.users:
                kwargs['userobj'] = decoded
                return f(*args, **kwargs)
            else:
                return redirect('/not-allowed')
        else: 
            return redirect('/login')
    return decorated


def check_user(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        kwargs['userobj'] = None
        token = request.cookies.get(g.jwt_cookie_name)
        if token:
            decoded = jwt.decode(token, key=g.jwt_secret, algorithms=["HS256"])
        else:
            decoded = None
        if decoded:
            if decoded['email'] in g.users:
                kwargs['userobj'] = decoded
        return f(*args, **kwargs)
    return decorated
