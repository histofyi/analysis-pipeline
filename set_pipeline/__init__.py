from flask import Blueprint, current_app, request, redirect
from typing import Dict

from common.decorators import check_user, requires_privilege, templated
from common.models import itemSet

from common.forms import request_variables


import logging
import json


set_pipeline_views = Blueprint('set_pipeline_views', __name__)


@set_pipeline_views.get('/')
@check_user
@requires_privilege('users')
@templated('sets/index')
def structure_home_handler(userobj:Dict) -> Dict:
    """
    This handler provides the homepage for the sets pipeline section

    Args: 
        userobj (Dict): a dictionary describing the currently logged in user with the correct privileges

    Returns:
        Dict: a dictionary containing the user object and a list of possible next actions

    """
    return {'userobj': userobj, 'actions':[]}