from flask import Flask, request
import toml
import logging

import functions.providers as providers
import functions.template as template
import functions


from api import api


app = Flask(__name__)
app.config.from_file('config.toml', toml.load)

#app.register_blueprint(api, url_prefix='/api/v1')


provider = providers.filesystemProvider(app.config['BASEDIR'])


@app.get('/')
def home_handler():
    data, success, errors = provider.get('scratch/hello')
    return template.render('index', data)


