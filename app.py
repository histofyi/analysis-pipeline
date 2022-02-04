from flask import Flask, request, redirect, make_response, Response, render_template, g
from cache import cache
from os import environ
from authlib.integrations.flask_client import OAuth


import json

from common.decorators import requires_privilege, check_user, templated
from common.blueprints.auth import auth_handlers
import common.providers as providers
#import common.functions as functions


import toml
import logging

import common.providers as providers
#import common.functions as functions



#from structure_pipeline import structure_pipeline_views
#from sequence_pipeline import sequence_pipeline_views
#from constants_pipeline import constants_views



config = {
    "DEBUG": True,          # some Flask specific configs
    #TODO check what the "DEBUG" config does
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300, # Flask-Caching related configs
    "TEMPLATE_DIRS": "templates" # Default template directory
}



def create_app():
    app = Flask(__name__)
    app.config.from_file('config.toml', toml.load)
    app.secret_key = app.config['SECRET_KEY']

    app.config['USE_LOCAL_S3'] = False


    if environ.get('FLASK_ENV'):
        if environ.get('FLASK_ENV') == 'development' and app.config['LOCAL_S3']:
            app.config['USE_LOCAL_S3'] = True

    app.config.from_mapping(config)
    cache.init_app(app)


    app.register_blueprint(auth_handlers, url_prefix='/auth')



    # most of the work is done by Blueprints so that the system is modular
    # TODO revise and refactor the Blueprints. Some of them should be in the frontend application

    #app.register_blueprint(structure_pipeline_views, url_prefix='/pipeline/structures')
    #app.register_blueprint(sequence_pipeline_views, url_prefix='/pipeline/sequences')
    #app.register_blueprint(constants_views, url_prefix='/pipeline/constants')



#    app.register_blueprint(set_views, url_prefix='/sets')
#    app.register_blueprint(structure_views, url_prefix='/structures')
#    app.register_blueprint(allele_views, url_prefix='/alleles')
#    app.register_blueprint(represention_views, url_prefix='/representations')
#    app.register_blueprint(statistics_views, url_prefix='/statistics')




    oauth = OAuth(app)
    app.auth0 = oauth.register(
        'auth0',
        client_id = app.config['AUTH0_CLIENT_ID'],
        client_secret = app.config['AUTH0_CLIENT_SECRET'],
        api_base_url = app.config['AUTH0_API_BASE_URL'],
        access_token_url = app.config['AUTH0_ACCESS_TOKEN_URL'],
        authorize_url = app.config['AUTH0_AUTHORIZE_URL'],
        client_kwargs={
            'scope': 'openid profile email',
        },
    )
    return app


app = create_app()


@app.before_request
def before_request_func():
    g.jwt_secret = app.config['JWT_SECRET']
    g.jwt_cookie_name = app.config['JWT_COOKIE_NAME']
    g.users = app.config['USERS']


def get_aws_config():
    if app.config['USE_LOCAL_S3'] == True:
        return {
            'aws_access_key_id':app.config['LOCAL_ACCESS_KEY_ID'],
            'aws_access_secret':app.config['LOCAL_ACCESS_SECRET'],
            'aws_region':app.config['AWS_REGION'],
            's3_url':app.config['LOCAL_S3_URL'],
            'local':True,
            's3_bucket':app.config['S3_BUCKET'] 
        }
    else:
        return {
            'aws_access_key_id':app.config['AWS_ACCESS_KEY_ID'],
            'aws_access_secret':app.config['AWS_ACCESS_SECRET'],
            'aws_region':app.config['AWS_REGION'],
            'local':False,
            's3_bucket':app.config['S3_BUCKET'] 
        }






# TODO refactor this to check the AWS S3/Minio connection not the filesystem
@cache.memoize(timeout=5)
def check_datastore():
    scratch_json, success, errors = providers.s3Provider(get_aws_config()).get('scratch/hello.json')
    if success:
        return scratch_json
    else:
        return {'error':'unable to connect'}



### static (mostly) basic views


# mostly static view
# TODO pull in statistics on the datastore (how many structures etc)
@app.get('/')
@check_user
@templated('index')
def home_handler(userobj):
    logging.warn(userobj)
    scratch_json = check_datastore()
    return {'message':scratch_json, 'userobj': userobj}




# design system display, cribbed from Catalyst styles developed by @futurefabric (Guy Moorhouse)
@app.get('/design-system')
@templated('design-system')
def design_system_hander():
    return {}











