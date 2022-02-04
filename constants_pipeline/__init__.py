from flask import Blueprint, current_app, request

from functions.decorators import requires_permission, templated
from functions.decorators.authentication import check_user

from .pipeline_actions import list_constants, view_constants, upload_constants

import logging
import json


constants_views = Blueprint('constants_views', __name__)


def get_aws_config():
    if current_app.config['USE_LOCAL_S3'] == True:
        return {
            'aws_access_key_id':current_app.config['LOCAL_ACCESS_KEY_ID'],
            'aws_access_secret':current_app.config['LOCAL_ACCESS_SECRET'],
            'aws_region':current_app.config['AWS_REGION'],
            's3_url':current_app.config['LOCAL_S3_URL'],
            'local':True,
            's3_bucket':current_app.config['S3_BUCKET'] 
        }
    else:
        return {
            'aws_access_key_id':current_app.config['AWS_ACCESS_KEY_ID'],
            'aws_access_secret':current_app.config['AWS_ACCESS_SECRET'],
            'aws_region':current_app.config['AWS_REGION'],
            'local':False,
            's3_bucket':current_app.config['S3_BUCKET'] 
        }


pipeline_actions = {
        'list':{'action':list_constants,'next':None, 'name':'List constants'},
        'view':{'action':view_constants,'next':None, 'name':'View constants'},
        'upload':{'action':upload_constants,'next':None, 'name':'Upload constants'}
}


@constants_views.get('/')
@check_user
@requires_permission
@templated('constants_index')
def constants_home_handler(userobj):
    return {'userobj': userobj}



# Named bulk step handler
@constants_views.get('/<string:route>')
@check_user
@requires_permission
@templated('pipeline_view')
def pipeline_handler(userobj, route):
    data, success, errors = pipeline_actions[route]['action'](aws_config=get_aws_config())
    return {'data':data, 'next':pipeline_actions[route]['next'], 'success': success, 'errors':errors, 'userobj':userobj, 'action':route, 'section':'Constants', 'action':pipeline_actions[route]['name'], 'items':'constants'}


