from flask import Blueprint, current_app, request

from common.decorators import templated, check_user, requires_privilege

import logging
import json

notes_views = Blueprint('notes_views', __name__)

@notes_views.get('/')
@check_user
@requires_privilege('users')
@templated('notes/index')
def notes_home_handler(userobj):
    return {'userobj': userobj}
