from flask import Blueprint, current_app, request

from common.decorators import templated, requires_privilege, check_user
from common.providers import s3Provider, awsKeyProvider
from common.helpers import fetch_core


import logging
import json

features_views = Blueprint('features_views', __name__)


@features_views.get('/')
@check_user
@requires_privilege('users')
@templated('features/index')
def features_home_handler(userobj):
    return {'userobj': userobj}



@features_views.get('/view/<string:pdb_code>')
@check_user
@requires_privilege('users')
@templated('features/view')
def features_view_handler(userobj, pdb_code):
    s3 = s3Provider(current_app.config['AWS_CONFIG'])
    core, success, errors = fetch_core(pdb_code, current_app.config['AWS_CONFIG'])
    if success:
        block_key = awsKeyProvider().block_key(pdb_code, 'features', 'structures')
        features, success, errors = s3.get(block_key)
    else:
        features = None
        core = None
        errors = ['not_mhc']
    return {'userobj': userobj, 'pdb_code': pdb_code, 'features':features, 'success': success, 'errors':errors, 'structure':core}


@features_views.get('/add/<string:pdb_code>')
@check_user
@requires_privilege('users')
#@templated('features/add')
def features_add_handler(userobj, pdb_code):
    s3 = s3Provider(current_app.config['AWS_CONFIG'])
    core, success, errors = fetch_core(pdb_code, current_app.config['AWS_CONFIG'])
    if success:
        block_key = awsKeyProvider().block_key(pdb_code, 'features', 'structures')
        features, success, errors = s3.get(block_key)
    else:
        features = None
        core = None
        errors = ['not_mhc']
    return {'userobj': userobj, 'pdb_code': pdb_code, 'features':features, 'success': success, 'errors':errors, 'structure':core}
