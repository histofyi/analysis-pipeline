from flask import Flask, request
import toml
import logging

import functions.providers as providers
import functions.template as template
import functions.pdb as pdb
import functions



from api import api


app = Flask(__name__)
app.config.from_file('config.toml', toml.load)


filesystem = providers.filesystemProvider(app.config['BASEDIR'])
http = providers.httpProvider()




@app.get('/')
def home_handler():
    data, success, errors = filesystem.get('scratch/hello')
    query, success, errors = filesystem.get('constants/class_ii_sequence_query')

    pdb_file = pdb.RCSB().fetch('2hla')

    pdb_data = pdb.RCSB().search(query)


    data['pdb_file'] = pdb_file
    data['pdb'] = pdb_data
    data['count'] = len(pdb_data)
    return template.render('index', data)


