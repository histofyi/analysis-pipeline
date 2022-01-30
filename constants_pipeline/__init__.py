from flask import Blueprint, current_app, request

from functions.decorators import requires_auth

from .pipeline_actions import upload_constants

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
        'upload':{'action':upload_constants,'next':None}
}


@constants_views.get('/')
@requires_auth
def constants_home_handler():
    return 'hello'



# Named bulk step handler
@constants_views.get('/<string:route>')
def pipeline_handler(route):
    data, success, errors = pipeline_actions[route]['action'](aws_config=get_aws_config())
    if success:
        return {'data':data, 'next':pipeline_actions[route]['next']}
    else:
        return {'erors':errors}


