from flask import Flask, request
import toml
import json
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
    scratch_json, success, errors = filesystem.get('scratch/hello')
    return template.render('index', {'pdb_file':scratch_json})



@app.get('/structures/information/<path:pdb_code>')
def structure_info_handler(pdb_code):
    rcsb = pdb.RCSB()
    pdb_info = rcsb.get_info(pdb_code)
    pdb_info_text = json.dumps(pdb_info, sort_keys=True, indent=4)
    pdb_file = rcsb.fetch(pdb_code)
    pdb_image_folder = pdb_code[1:3]
    return template.render('structure_info', {'pdb_file':pdb_file, 'pdb_code':pdb_code, 'pdb_info':pdb_info, 'pdb_info_text':pdb_info_text, 'pdb_image_folder':pdb_image_folder})




@app.get('/structures/search/<path:mhc_class>')
def structures_search_handler(mhc_class):
    query_name = mhc_class + '_sequence_query'
    query, success, errors = filesystem.get('constants/rcsb/'+ query_name)
    search_data = pdb_data = pdb.RCSB().search(query)
    return template.render('structure_search', {'search_data':search_data,'molecule_metadata':molecules[mhc_class],'count':len(search_data)})





