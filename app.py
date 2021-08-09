from flask import Flask, request, redirect
from flask_caching import Cache

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
import functions.textanalysis as textanalysis
import functions.histo as histo


from api import api


config = {
    "DEBUG": True,          # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300
}

app = Flask(__name__)
app.config.from_file('config.toml', toml.load)
app.config.from_mapping(config)
cache = Cache(app)


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

    # TODO get this working properly
    if '-1' in str(diff):
        return "just now"

    for period, singular, plural in periods:        
        if period:
            return "%d %s ago" % (period, singular if period == 1 else plural)

    return default




filesystem = providers.filesystemProvider(app.config['BASEDIR'])



def return_to(pdb_code):
    return '/structures/information/{pdb_code}'.format(pdb_code=pdb_code)


@app.before_request
def before_request():
    logging.warn(request.full_path)


@app.get('/')
def home_handler():
    scratch_json, success, errors = filesystem.get('scratch/hello')
    return template.render('index', scratch_json)


@app.get('/structures')
def structures_handler():
    return template.render('structures', {})



@app.get('/structures/<string:pdb_code>/approve/best_match')
def structure_approve_attribute_handler(pdb_code):
    variables = common.request_variables(['return_to'])
    histo_info, success, errors = histo.structureInfo(pdb_code).get()
    complex_type = {'complex_type':histo_info['best_match']['best_match']}
    histo_info, success, errors = histo.structureInfo(pdb_code).put('complex_type', complex_type)
    return redirect(variables['return_to'])




@app.get('/structures/search/<string:mhc_class>')
def structures_search_handler(mhc_class):
    molecules, success, errors = filesystem.get('constants/shared/molecules')
    chain_assignment_complete, success, errors = lists.structureSet('chain_assignment_complete').get()
    exclude, success, errors = lists.structureSet('exclude').get()
    incorrect_chain_labels, success, errors = lists.structureSet('incorrect_chain_labels').get()
    edgecases, success, errors = lists.structureSet('edgecases').get()
    
    query_name = mhc_class + '_sequence_query'
    query, success, errors = filesystem.get('constants/rcsb/'+ query_name)
    
    search_data = pdb.RCSB().search(query)
    filtered_set = []

    for structure in search_data:
        seen_structure = False
        logging.warn(structure)
        if structure in chain_assignment_complete['set']:
            seen_structure = True
        if structure in exclude['set']:
            seen_structure = True
        if structure in incorrect_chain_labels['set']:
            seen_structure = True
        if structure in edgecases['set']:
            seen_structure = True
        if not seen_structure:
            filtered_set.append(structure)        
    slug = mhc_class + '_search'

    structureset = {
        'set':search_data,
        'length':len(search_data),
        'last_updated':datetime.now(),
        'slug':slug,
        'ui_text':slug.replace('_',' ').title()
    }
    return template.render('structure_sets', {'nav':'sets','set':structureset, 'view_type':'condensed'})


@app.get('/structures/assign_automatically/<string:mhc_class>')
def structures_automatic_assignment_handler(mhc_class):
    query_name = mhc_class + '_sequence_query'
    query, success, errors = filesystem.get('constants/rcsb/'+ query_name)
    exclude, success, errors = lists.structureSet('exclude').get()
    automatically_matched, success, errors = lists.structureSet('automatically_matched').get()
    error, success, errors = lists.structureSet('error').get()


    exclude_length = len(exclude['set'])
    automatically_matched_length = len(automatically_matched['set'])
    error_length = len(error['set'])


    number_of_records = 25


    rcsb = pdb.RCSB()

    rcsb_info = {}

    search_data = rcsb.search(query)
    
    stats = {
        'exclude_length':exclude_length,
        'automatically_matched_length':automatically_matched_length,
        'error_length':error_length,
        'found_length': len(search_data)
    }

    filtered_set = []

    for structure in search_data:
        seen_structure = False
        if structure in exclude['set']:
            seen_structure = True
        if structure in automatically_matched['set']:
            seen_structure = True
        if structure in error['set']:
            seen_structure = True
        if not seen_structure:
            filtered_set.append(structure)

    filtered_set_length = len(filtered_set)

    remaining = filtered_set_length - number_of_records
    if remaining < 0:
        remaining = 0


    short_search = filtered_set[0:number_of_records]




    search_set = {}

    for pdb_code in short_search:
        histo_info, success, errors = histo.structureInfo(pdb_code).get()
        search_set[pdb_code] = {}
        if 'complex_type' in histo_info:
            search_set[pdb_code]['manual_assignment'] = histo_info['complex_type']['complex_type']
        
        pdb_info = rcsb.get_info(pdb_code)
        rcsb_info = {}
        rcsb_info['primary_citation'] = pdb_info['rcsb_primary_citation']
        rcsb_info['struct'] = pdb_info['struct']
        rcsb_info['entry_info'] = pdb_info['rcsb_entry_info']
        rcsb_info['title'] = pdb_info['struct']['title']
        histo_info, success, errors = histo.structureInfo(pdb_code).put('rcsb_info', rcsb_info)


        pdb_file = rcsb.fetch(pdb_code)

        assembly_count = pdb_info['rcsb_entry_info']['assembly_count']

        structure = rcsb.load_structure(pdb_code)


        try:
            structure_stats = rcsb.predict_assigned_chains(structure, assembly_count)

            best_match = structure_stats['best_match']
            histo_info, success, errors = histo.structureInfo(pdb_code).put('best_match', best_match)
            del structure_stats['best_match']
            histo_info, success, errors = histo.structureInfo(pdb_code).put('structure_stats', structure_stats)

            logging.warn(best_match)

            if best_match['confidence'] > 0.8:
                del structure_stats['complex_hits']
                search_set[pdb_code]['best_matching'] = True
                data, success, errors = lists.structureSet(best_match['best_match']).add(pdb_code)
            elif best_match['confidence'] > 0.5:
                search_set[pdb_code]['matching'] = True
                data, success, errors = lists.structureSet('probable_' + best_match['best_match']).add(pdb_code)
            else:
                data, success, errors = lists.structureSet('unmatched').add(pdb_code)

            search_set[pdb_code]['best_match'] = best_match
            data, success, errors = lists.structureSet('automatically_matched').add(pdb_code)

        except:
            search_set[pdb_code]['error'] = True
            data, success, errors = lists.structureSet('error').add(pdb_code)

    
    return template.render('structure_matching', {'search': short_search, 'search_set':search_set, 'rcsb_info':rcsb_info, 'filtered_set_length': remaining, 'stats':stats})



@app.get('/structures/analyse_chains/<string:pdb_code>')
def analysechains_handler(pdb_code):
    rcsb = pdb.RCSB()
    complexes, success, errors = filesystem.get('constants/shared/complexes')

    # get the rcscb held data, the rscb json data and the pdb data
    pdb_info = rcsb.get_info(pdb_code)

    pdb_file = rcsb.fetch(pdb_code)

    assembly_count = pdb_info['rcsb_entry_info']['assembly_count']

    structure = rcsb.load_structure(pdb_code)

    structure_stats = rcsb.predict_assigned_chains(structure, assembly_count)
    

    variables = {
            'pdb_code': pdb_code,
            'structure_stats': structure_stats
    }
    
    return variables





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
    data, success, errors = lists.structureSet(current_set).add(pdb_code)
    return redirect(return_to(pdb_code))



@app.post('/structures/information/<string:pdb_code>/<string:information_section>/update')
def update_structure_information_handler(pdb_code,information_section):
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
    unmatched, success, errors = lists.structureSet('unmatched').get()
    unmatched_structure = False
    logging.warn(unmatched['set'])
    if pdb_code in unmatched['set']:
        unmatched_structure = True
        logging.warn("MATCH")

    # get the constants about complexes
    complexes, success, errors = filesystem.get('constants/shared/complexes')


    # get or create the histo dataset for this structure
    histo_info, success, errors = histo.structureInfo(pdb_code).get()

    rcsb = pdb.RCSB()

    # get the rcscb held data, the rscb json data and the pdb data
    pdb_info = rcsb.get_info(pdb_code)

    pdb_file = rcsb.fetch(pdb_code)

    # the rcsb pdb images are held in directories based on the middle two letters of the PDB code
    pdb_image_folder = pdb_code[1:3]


    assembly_count = pdb_info['rcsb_entry_info']['assembly_count']

    # load the structure into BioPython
    structure = rcsb.load_structure(pdb_code)

    # try to resolve the DOI in the rcsb data
    try:
        doi_url = rcsb.resolve_doi(pdb_info["rcsb_primary_citation"]["pdbx_database_id_doi"])
    except:
        # TODO handle this better
        doi_url = None
    

    # generate some basic information about the structure 
    # TODO refactor this
    
    basic_information = rcsb.generate_basic_information(structure, assembly_count)


    # build variables for the UI
    variables = {
        'nav':'structures',
        'pdb_file':pdb_file, 
        'pdb_code':pdb_code, 
        'pdb_info':pdb_info, 
        'pdb_info_text':json.dumps(pdb_info, sort_keys=True, indent=4), 
        'pdb_image_folder':pdb_image_folder, 
        'doi_url':doi_url,
        'basic_information':basic_information,
        'complexes':complexes,
        'histo_info':histo_info,
        'unmatched':unmatched_structure
    }
    return template.render('structure_info', variables)



@app.get('/sets/create')
def sets_create_form_handler():
    return template.render('sets_create', {})


@app.get('/sets/create')
def sets_create_action_handler():
    #TODO ensure set doesn't already exist
    already_exists = lists.structureSet(slug).check_exists()
    if not already_exists:
        logging.warn('create the set')
    else:
        logging.warn('already exists. do nothing')
    return template.render('sets_create', {})


@cache.memoize(timeout=300)
def get_hydrated_structure_set(slug):
    structureset, success, errors = lists.structureSet(slug).get()
    structureset['histo_info'] = {}
    for pdb_code in structureset['set']:
        histo_info, success, errors = histo.structureInfo(pdb_code).get()
        structureset['histo_info'][pdb_code] = histo_info
    return structureset




@app.get('/sets/<string:slug>')
def sets_display_handler(slug):
    structureset = get_hydrated_structure_set(slug)
    unnatural = []
    short = []
    for pdb_code in structureset['set']:
        histo_info = structureset['histo_info'][pdb_code]
        for chain in histo_info['structure_stats']['chain_assignments']:
            if chain == 'class_i_peptide':
                peptide_sequence = histo_info['structure_stats']['chain_assignments'][chain]['sequences'][0]
                if 'Z' in peptide_sequence:
                    unnatural.append(pdb_code)
                if len(peptide_sequence) < 8:
                    short.append(pdb_code)
    logging.warn('unnatural')
    logging.warn(unnatural)
    logging.warn('short')
    logging.warn(short)
    return template.render('set', {'nav':'sets','set':structureset})


@app.get('/sets')
def sets_list_handler():
    set_list = {
        'publications':['open_access','paywalled','missing_publication'],
        'structures':['class_i_with_peptide','probable_class_i_with_peptide'],
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










