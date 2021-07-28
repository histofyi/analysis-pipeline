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


molecules, success, errors = filesystem.get('constants/shared/molecules')


@app.get('/')
def home_handler():
    pdb_file = pdb.RCSB().fetch('2hla')
    return template.render('index', {'pdb_file':pdb_file})



@app.get('/structures/information/<path:pdb_code>')
def structure_info_handler(pdb_code):
    pdb_file = pdb.RCSB().fetch(pdb_code)
    return template.render('structure_info', {'pdb_file':pdb_file,'pdb_code':pdb_code})




@app.get('/structures/search/<path:mhc_class>')
def structures_search_handler(mhc_class):
    query_name = mhc_class + '_sequence_query'
    logging.warn(query_name)
    query, success, errors = filesystem.get('constants/rcsb/'+ query_name)
    logging.warn(query)
    search_data = pdb_data = pdb.RCSB().search(query)
    return template.render('structure_search', {'search_data':search_data,'molecule_metadata':molecules[mhc_class],'count':len(search_data)})





