from flask import Flask, request, redirect
import toml
import json
import logging



import functions.providers as providers
import functions.template as template
import functions.pdb as pdb
import functions.lists as lists
import functions.common as common
import functions.histo as histo


from api import api



app = Flask(__name__)
app.config.from_file('config.toml', toml.load)


filesystem = providers.filesystemProvider(app.config['BASEDIR'])

def return_to(pdb_code):
    return '/structures/information/{pdb_code}'.format(pdb_code=pdb_code)


@app.get('/')
def home_handler():
    scratch_json, success, errors = filesystem.get('scratch/hello')
    return template.render('index', scratch_json)


@app.get('/structures/search/<string:mhc_class>')
def structures_search_handler(mhc_class):
    molecules, success, errors = filesystem.get('constants/shared/molecules')
    query_name = mhc_class + '_sequence_query'
    query, success, errors = filesystem.get('constants/rcsb/'+ query_name)
    search_data = pdb.RCSB().search(query)
    return template.render('structure_search', {'search_data':search_data,'molecule_metadata':molecules[mhc_class],'count':len(search_data)})



@app.get('/structures/information/<string:pdb_code>/<string:current_set>/add')
def add_to_structureset_handler(pdb_code,current_set):
    data, success, errors = lists.structureSet(current_set).add(pdb_code)
    return redirect(return_to(pdb_code))


@app.post('/structures/information/<string:pdb_code>/<string:information_section>/update')
def update_structure_information_handler(pdb_code,information_section):
    variables = common.request_variables(None)
    if variables:
        if 'pdb_code' in variables:
            del variables['pdb_code']
        histo_info, success, errors = histo.structureInfo(pdb_code).put(information_section, json.dumps(variables))
    return redirect(return_to(pdb_code))




@app.get('/structures/information/<string:pdb_code>')
def structure_info_handler(pdb_code):
    histo_info, success, errors = histo.structureInfo(pdb_code).get()

    rcsb = pdb.RCSB()
    pdb_info = rcsb.get_info(pdb_code)

    pdb_file = rcsb.fetch(pdb_code)

    pdb_image_folder = pdb_code[1:3]


    assembly_count = pdb_info['rcsb_entry_info']['assembly_count']


    structure = rcsb.load_structure(pdb_code)

    try:
        doi_url = rcsb.resolve_doi(pdb_info["rcsb_primary_citation"]["pdbx_database_id_doi"])
    except:
        doi_url = None
    
    

    basic_information = rcsb.generate_basic_information(structure, assembly_count)

    complexes, success, errors = filesystem.get('constants/shared/complexes')

    
    variables = {
        'pdb_file':pdb_file, 
        'pdb_code':pdb_code, 
        'pdb_info':pdb_info, 
        'assembly_count': assembly_count,
        'pdb_info_text':json.dumps(pdb_info, sort_keys=True, indent=4), 
        'pdb_image_folder':pdb_image_folder, 
        'doi_url':doi_url,
        'basic_information':basic_information,
        'complexes':complexes,
        'histo_info':histo_info
    }
    return template.render('structure_info', variables)



@app.get('/design-system')
def design_system_hander():
    return template.render('design_system', {})










