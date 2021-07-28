from flask import Flask, request
import toml
import logging

import functions.providers as providers
import functions.template as template

from api import api

app = Flask(__name__)
app.config.from_file('config.toml', toml.load)


app.register_blueprint(api, url_prefix='/api/v1')

filesystem = providers.filesystemProvider(app.config['BASEDIR'])

@app.get('/')
def home_handler():
    filesystem.get('hello')
    return str(providers.filesystem())