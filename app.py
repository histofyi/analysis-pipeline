from flask import Flask, request, redirect
import toml
import json
import logging

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from datetime import datetime

import functions.providers as providers
import functions.template as template
import functions.pdb as pdb
import functions.lists as lists
import functions.common as common
import functions.histo as histo


from api import api


app = Flask(__name__)
app.config.from_file('config.toml', toml.load)


@app.template_filter()
def timesince(dt, default="just now"):
    """
    Returns string representing "time since" e.g.
    3 days ago, 5 hours ago etc.
    """

    now = datetime.utcnow()
    diff = now - dt
    
    periods = (
        (diff.days / 365, "year", "years"),
        (diff.days / 30, "month", "months"),
        (diff.days / 7, "week", "weeks"),
        (diff.days, "day", "days"),
        (diff.seconds / 3600, "hour", "hours"),
        (diff.seconds / 60, "minute", "minutes"),
        (diff.seconds, "second", "seconds"),
    )

    for period, singular, plural in periods:
        
        if period:
            return "%d %s ago" % (period, singular if period == 1 else plural)

    return default


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


@app.post("/structures/information/<string:pdb_code>/assignchains")
def assign_structure_chains(pdb_code):
    mhc_class = None
    length_name = None
    peptide_sequence = None

    variables = common.request_variables(['chain_count'])
    chain_count = int(variables['chain_count'])
    params = []
    i = 1
    while i <= chain_count:
        this_chain = str(i)
        params.append('chain_'+ this_chain + '_length')
        params.append('chain_'+ this_chain + '_assignments')
        params.append('chain_'+ this_chain + '_chain_type')
        params.append('chain_'+ this_chain + '_sequence')
        i += 1
    variables = common.request_variables(params)
    variables['chain_count'] = chain_count
    info = {}

    i = 1
    while i <= chain_count:
        i 
        this_chain_name = 'chain_' + str(i)
        info[this_chain_name] = {}
        info[this_chain_name]['length'] = variables[this_chain_name + '_length']
        info[this_chain_name]['assignments'] = variables[this_chain_name + '_assignments']
        info[this_chain_name]['chain_type'] = variables[this_chain_name + '_chain_type']
        info[this_chain_name]['sequence'] = variables[this_chain_name + '_sequence']
        data, success, errors = lists.structureSet('chains/' + variables[this_chain_name + '_chain_type']).add(pdb_code)

        if 'peptide' in variables[this_chain_name + '_chain_type']:
            mhc_class = variables[this_chain_name + '_chain_type'].replace('_peptide','')
            peptide_lengths, success, errors = filesystem.get('constants/shared/peptide_lengths')
            peptide_length = int(variables[this_chain_name + '_length'])
            logging.warn("PEPTIDE KLAXON for " + this_chain_name)
            if peptide_length < 20:
                for peptide_type in peptide_lengths:
                    if peptide_lengths[peptide_type]['length'] == peptide_length:
                        length_name = peptide_type
                        peptide_sequence = variables[this_chain_name + '_sequence'].lower()
            else:
                length_name = "overlength"
            data, success, errors = lists.structureSet('peptides/' + mhc_class + '/lengths/' + length_name).add(pdb_code)
            data, success, errors = lists.structureSet('peptides/' + mhc_class + '/sequences/' + peptide_sequence).add(pdb_code)
        i += 1
    
    data, success, errors = lists.structureSet('chain_assignment_complete').add(pdb_code)
    histo_info, success, errors = histo.structureInfo(pdb_code).put('chains', json.dumps(info))
    return redirect(return_to(pdb_code))



@app.get('/structures/information/<string:pdb_code>/<string:current_set>/add')
def add_to_structureset_handler(pdb_code,current_set):
    logging.warn("ADD TO SET " + current_set)
    data, success, errors = lists.structureSet(current_set).add(pdb_code)
    return redirect(return_to(pdb_code))



@app.post('/structures/information/<string:pdb_code>/<string:information_section>/update')
def update_structure_information_handler(pdb_code,information_section):
    logging.warn("UPDATING INFORMATION " + information_section)
    variables = common.request_variables(None)
    if variables:
        if 'pdb_code' in variables:
            del variables['pdb_code']
        histo_info, success, errors = histo.structureInfo(pdb_code).put(information_section, json.dumps(variables))
        if 'complex_type' in variables:
            data, success, errors = lists.structureSet(variables['complex_type']).add(pdb_code)
        if 'open_access' in variables:
            data, success, errors = lists.structureSet('open_access').add(pdb_code)
        if 'paywalled' in variables:
            data, success, errors = lists.structureSet('paywalled').add(pdb_code)
        if 'missing_publication' in variables:
            data, success, errors = lists.structureSet('missing_publication').add(pdb_code)
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
        'nav':'structures',
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


@app.get('/sets/<string:slug>')
def sets_display_handler(slug):
    rcsb = pdb.RCSB()
    structureset, success, errors = lists.structureSet(slug).get()
    structureset['pdb_info'] = {}
    structureset['histo_info'] = {}
    for pdb_code in structureset['set']:
        histo_info, success, errors = histo.structureInfo(pdb_code).get()
        structureset['histo_info'][pdb_code] = histo_info
        structureset['pdb_info'][pdb_code] = rcsb.get_info(pdb_code)['struct']
    return template.render('set', {'nav':'sets','set':structureset})


@app.get('/sets')
def sets_list_handler():
    set_list = {
        'publications':['open_access','paywalled','missing_publication'],
        'structures':[],
        'editorial':['interesting'],
        'curatorial':['edgecases','exclude','incorrect_chain_labels']
    }
    sets = {}
    for category in set_list:
        sets[category] = {}
        for set in set_list[category]:
            sets[category][set], success, errors = lists.structureSet(set).get()
    return template.render('sets', {'nav':'sets','sets':sets})





@app.get('/design-system')
def design_system_hander():
    return template.render('design_system', {})










