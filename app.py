from flask import Flask, request, redirect, make_response, Response, render_template
from cache import cache
from os import environ


import toml
import logging

import functions.providers as providers
import functions.template as template
import functions.common as common


from functions.template import templated


from structure_pipeline import structure_pipeline_views
from sequence_pipeline import sequence_pipeline_views
from constants_pipeline import constants_views

from sets import set_views
from structures import structure_views
from alleles import allele_views
#from representations import represention_views


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
    app.config['USE_LOCAL_S3'] = False


    if environ.get('FLASK_ENV'):
        if environ.get('FLASK_ENV') == 'development' and app.config['LOCAL_S3']:
            app.config['USE_LOCAL_S3'] = True

    app.config.from_mapping(config)
    cache.init_app(app)

    # most of the work is done by Blueprints so that the system is modular
    # TODO revise and refactor the Blueprints. Some of them should be in the frontend application

    app.register_blueprint(structure_pipeline_views, url_prefix='/pipeline/structures')
    app.register_blueprint(sequence_pipeline_views, url_prefix='/pipeline/sequences')
    app.register_blueprint(constants_views, url_prefix='/pipeline/constants')



    app.register_blueprint(set_views, url_prefix='/sets')
    app.register_blueprint(structure_views, url_prefix='/structures')
    app.register_blueprint(allele_views, url_prefix='/alleles')
    #app.register_blueprint(represention_views, url_prefix='/representations')
    #app.register_blueprint(statistics_views, url_prefix='/statistics')
    
    return app


app = create_app()



# TODO refactor this out to use the AWS S3/Minio BOTO procvider
filesystem = providers.filesystemProvider(app.config['BASEDIR'])



### Template filters ###


@app.template_filter()
def timesince(start_time):
    return common.timesince(start_time)


@app.template_filter()
def deslugify(slug):
    return common.de_slugify(slug)


@app.template_filter()
def prettify_json(this_json):
    return common.prettify_json(this_json)


# for displaying images from RCSB
# TODO decide if this is needed - think probably not for "legal-ish" reasons
@app.template_filter()
def pdb_image_folder(pdb_code):
    return pdb_code[1:3]


@app.template_filter()
def structure_title(description):
    title = ''
    return title


# TODO refactor this to check the AWS S3/Minio connection not the filesystem
@cache.memoize(timeout=5)
def check_filestore():
    scratch_json, success, errors = filesystem.get('scratch/hello')
    if success:
        return scratch_json
    else:
        return {'error':'unable to connect'}



### static (mostly) basic views


# mostly static view
# TODO pull in statistics on the datastore (how many structures etc)
@app.get('/')
@templated('index')
def home_handler():
    scratch_json = check_filestore()
    return scratch_json


# design system display, cribbed from Catalyst styles developed by @futurefabric (Guy Moorhouse)
@app.get('/design-system')
@templated('design-system')
def design_system_hander():
    return {}











