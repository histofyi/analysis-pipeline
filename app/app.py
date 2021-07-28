from flask import Flask, request

from api import api

app = Flask(__name__)

app.register_blueprint(api, url_prefix='/api/v1')
