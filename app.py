from flask import Flask, request, redirect, make_response, Response, render_template, g
from cache import cache
from os import environ
from authlib.integrations.flask_client import OAuth

import json


from common.decorators import requires_privilege, check_user, templated
from common.blueprints.auth import auth_handlers
import common.providers as providers
import common.functions as functions


import toml
import logging
import datetime


from structure_pipeline import structure_pipeline_views
#from sequence_pipeline import sequence_pipeline_views
from constants_pipeline import constants_views


config = {
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300, # Flask-Caching related configs
    "TEMPLATE_DIRS": "templates" # Default template directory
}



def create_app():
    """
    Creates an instance of the Flask app, and associated configuration and blueprints registration for specific routes. 

    Configuration includes

    - Relevant secrets stored in the config.toml file
    - Storing in configuration a set of credentials for AWS (decided upon by the environment of the application e.g. development, live)
    
    Returns:
            A configured instance of the Flask app

    """
    app = Flask(__name__)
    app.config.from_file('config.toml', toml.load)
    app.secret_key = app.config['SECRET_KEY']

    if environ.get('FLASK_ENV'):
        if environ.get('FLASK_ENV') == 'development' and app.config['LOCAL_S3']:
            app.config['USE_LOCAL_S3'] = True


    # configuration of the cache from config
    app.config.from_mapping(config)
    cache.init_app(app)

    # removing whitespace from templated returns    
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True


    # most of the work is done by Blueprints so that the system is modular
    # TODO revise and refactor the Blueprints. Some of them should be in the frontend application

    app.register_blueprint(auth_handlers, url_prefix='/auth')
    app.register_blueprint(structure_pipeline_views, url_prefix='/pipeline/structures')
    #app.register_blueprint(sequence_pipeline_views, url_prefix='/pipeline/sequences')
    app.register_blueprint(constants_views, url_prefix='/pipeline/constants')


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


    if app.config['USE_LOCAL_S3'] == True:
        app.config['AWS_CONFIG'] = {
            'aws_access_key_id':app.config['LOCAL_ACCESS_KEY_ID'],
            'aws_access_secret':app.config['LOCAL_ACCESS_SECRET'],
            'aws_region':app.config['AWS_REGION'],
            's3_url':app.config['LOCAL_S3_URL'],
            'local':True,
            's3_bucket':app.config['S3_BUCKET'] 
        }
    else:
        app.config['AWS_CONFIG'] = {
            'aws_access_key_id':app.config['AWS_ACCESS_KEY_ID'],
            'aws_access_secret':app.config['AWS_ACCESS_SECRET'],
            'aws_region':app.config['AWS_REGION'],
            'local':False,
            's3_bucket':app.config['S3_BUCKET'] 
    }


    return app


app = create_app()


# TODO refactor this to check the AWS S3/Minio connection not the filesystem
@cache.memoize(timeout=5)
def check_datastore():
    """
    A function to return a small piece of JSON to indicate whether or not the connection to AWS is working
    """
    scratch_json, success, errors = providers.s3Provider(app.config['AWS_CONFIG']).get('scratch/hello.json')
    if not success:
        scratch_json = {'error':'unable to connect'}
    scratch_json['cached'] = datetime.datetime.now()
    return scratch_json


# mostly static view
# TODO pull in statistics on the datastore (how many structures etc)
@app.get('/')
@check_user
@templated('index')
def home_handler(userobj):
    """
    Handler to return the homepage of the Pipeline application
    """
    scratch_json = check_datastore()
    return {'message':scratch_json, 'userobj': userobj, }


# design system display, cribbed from Catalyst styles developed by @futurefabric (Guy Moorhouse)
@app.get('/design-system')
@templated('design-system')
def design_system_hander():
    return {}


### Template filters ###


@app.template_filter()
def timesince(start_time):
    return functions.timesince(start_time)


@app.template_filter()
def deslugify(slug):
    return functions.de_slugify(slug)


@app.template_filter()
def prettify_json(this_json):
    return functions.prettify_json(this_json)

@app.template_filter()
def prettify_dict(this_dict):
    return functions.prettify_json(json.dumps(this_dict))


# for displaying images from RCSB
# TODO decide if this is needed - think probably not for "legal-ish" reasons
@app.template_filter()
def pdb_image_folder(pdb_code):
    return pdb_code[1:3]


@app.template_filter()
def structure_title(description):
    title = ''
    return title


