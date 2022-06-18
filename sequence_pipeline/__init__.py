from flask import Blueprint, current_app, request

from .pipeline_actions import split_ipd_bulk_fasta, process_ipd_bulk_fasta, fetch_ipd_species, check_ipd_version

from common.decorators import check_user, requires_privilege, templated


import logging
import json


sequence_pipeline_views = Blueprint('sequence_pipeline_views', __name__)


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
        'check_ipd':{'action':check_ipd_version,'next':'split_ipd'},
        'split_ipd':{'action':split_ipd_bulk_fasta,'next':'process_ipd'},
        'fetch_ipd_species':{'action':fetch_ipd_species,'next':'process_ipd'},
        'process_ipd':{'action':process_ipd_bulk_fasta,'next':'process_hla'}
}



# Home
@sequence_pipeline_views.get('/')
@templated('sequences/index')
def home_handler():
    return {'erors':None}




# Named bulk step handler
@sequence_pipeline_views.get('/<string:route>')
def pipeline_handler(route):
    data, success, errors = pipeline_actions[route]['action'](aws_config=get_aws_config())
    if success:
        return {'data':data, 'next':pipeline_actions[route]['next']}
    else:
        return {'erors':errors}



# Individual step handler
@sequence_pipeline_views.get('/<string:route>/<string:file_name>')
def pipeline_item_handler(route, file_name):
    data, success, errors = pipeline_actions[route]['action'](file_name, aws_config=get_aws_config())
    if success:
        return {'data':data, 'next':pipeline_actions[route]['next'], 'file_name':file_name}
    else:
        return {'erors':errors}



