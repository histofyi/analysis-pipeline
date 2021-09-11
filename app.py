from flask import Flask, request, redirect, make_response, Response
from flask_caching import Cache


import toml

import functions.providers as providers
import functions.template as template
import functions.common as common


from pipeline import pipeline_views
from sets import set_views
from structures import structure_views

#from representations import represention_views


config = {
    "DEBUG": True,          # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300
}



app = Flask(__name__)
app.config.from_file('config.toml', toml.load)
app.config.from_mapping(config)
app.register_blueprint(pipeline_views, url_prefix='/pipeline')
app.register_blueprint(set_views, url_prefix='/sets')
app.register_blueprint(structure_views, url_prefix='/structures')
#app.register_blueprint(represention_views, url_prefix='/representations')
#app.register_blueprint(statistics_views, url_prefix='/statistics')

cache = Cache(app)

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


@app.template_filter()
def pdb_image_folder(pdb_code):
    return pdb_code[1:3]


@app.template_filter()
def structure_title(description):
    title = ''
    return title





# mostly static view
@app.get('/')
def home_handler():
    scratch_json, success, errors = filesystem.get('scratch/hello')
    return template.render('index', scratch_json)


# static view
@app.get('/structures')
def structures_handler():
    return template.render('structures', {})



@app.get('/design-system')
def design_system_hander():
    return template.render('design_system', {})










