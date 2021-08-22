from functions.actions.structure_pipeline import measure_peptide_angles
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
import functions.structure as structure

import functions.actions as actions


from api import api


config = {
    "DEBUG": True,          # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300
}

pipeline_actions = {
    'peptide_angles': actions.measure_peptide_angles
}

app = Flask(__name__)
app.config.from_file('config.toml', toml.load)
app.config.from_mapping(config)
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


def return_to(pdb_code):
    return '/structures/information/{pdb_code}'.format(pdb_code=pdb_code)


@cache.memoize(timeout=300)
def get_hydrated_structure_set(slug):
    structureset, success, errors = lists.structureSet(slug).get()
    structureset['histo_info'] = {}
    for pdb_code in structureset['set']:
        try:
            histo_info, success, errors = histo.structureInfo(pdb_code).get()
            structureset['histo_info'][pdb_code] = histo_info
        except:
            logging.warn("ERROR for " + pdb_code)
    return structureset



# mostly static view
@app.get('/')
def home_handler():
    scratch_json, success, errors = filesystem.get('scratch/hello')
    return template.render('index', scratch_json)


# static view
@app.get('/structures')
def structures_handler():
    return template.render('structures', {})


### Structure pipeline ###

# Step 0
@app.get('/structures/pipeline/clean/set/<string:slug>')
def set_clean_record_handler(slug):
    structureset, success, errors = lists.structureSet(slug).get()
    success_array = []
    errors_array = []
    for pdb_code in structureset['set']:
        try:
            data, success, errors = actions.clean_record(pdb_code)
            if success:
                success_array.append(pdb_code)
            else:
                errors_array.append(pdb_code)
        except:
            errors_array.append(pdb_code)
    data = {
        'success':success_array,
        'errors':errors_array
    }
    return data


# Step 1
@app.get('/structures/pipeline/fetch/set/<string:slug>')
def set_fetch_pdb_data_handler(slug):
    structureset, success, errors = lists.structureSet(slug).get()
    success_array = []
    errors_array = []
    for pdb_code in structureset['set']:
        try:
            data, success, errors = actions.fetch_pdb_data(pdb_code)
            if success:
                success_array.append(pdb_code)
            else:
                errors_array.append(pdb_code)
        except:
            errors_array.append(pdb_code)
    data = {
        'success':success_array,
        'errors':errors_array
    }
    return data


# Step 2
@app.get('/structures/pipeline/assign/set/<string:slug>')
def set_automatic_assignment_handler(slug):
    structureset, success, errors = lists.structureSet(slug).get()
    success_array = []
    errors_array = []
    for pdb_code in structureset['set']:
        try:
            data, success, errors = actions.automatic_assignment(pdb_code)
            if success:
                success_array.append(pdb_code)
            else:
                errors_array.append(pdb_code)
        except:
            errors_array.append(pdb_code)
    data = {
        'success':success_array,
        'errors':errors_array
    }
    return data


# Step 3
@app.get('/structures/pipeline/split/set/<string:slug>')
def set_split_structure_handler(slug):
    structureset, success, errors = lists.structureSet(slug).get()
    success_array = []
    errors_array = []
    for pdb_code in structureset['set']:
        try:
            data, success, errors = actions.split_structure(pdb_code)
            if data:
                success_array.append(pdb_code)
            else:
                errors_array.append(pdb_code)
        except:
            errors_array.append(pdb_code)
    data = {
        'success':success_array,
        'errors':errors_array
    }
    return data


# Step 4
@app.get('/structures/pipeline/align/set/<string:slug>')
def set_align_structures_handler(slug):
    structureset, success, errors = lists.structureSet(slug).get()
    success_array = []
    errors_array = []
    for pdb_code in structureset['set']:
        try:
            data, success, errors = actions.align_structures(pdb_code)
            if data:
                success_array.append(pdb_code)
            else:
                errors_array.append(pdb_code)
        except:
            errors_array.append(pdb_code)
    data = {
        'success':success_array,
        'errors':errors_array
    }
    return data



# Step 5
@app.get('/structures/pipeline/match/set/<string:slug>')
def set_match_structures_handler(slug):
    structureset, success, errors = lists.structureSet(slug).get()
    success_array = []
    errors_array = []
    for pdb_code in structureset['set']:
        try:
            data, success, errors = actions.match_structure(pdb_code)
            if data:
                success_array.append(pdb_code)
            else:
                errors_array.append(pdb_code)
        except:
            errors_array.append(pdb_code)
    data = {
        'success':success_array,
        'errors':errors_array
    }
    return data


# Step 6
@app.get('/structures/pipeline/peptide_positions/set/<string:slug>')
def set_peptide_positions_handler(slug):
    structureset, success, errors = lists.structureSet(slug).get()
    success_array = []
    errors_array = []
    for pdb_code in structureset['set']:
        try:
            data, success, errors = actions.peptide_positions(pdb_code)
            if data:
                success_array.append(pdb_code)
            else:
                errors_array.append(pdb_code)
        except:
            errors_array.append(pdb_code)
    data = {
        'success':success_array,
        'errors':errors_array
    }
    return data


# Step 7
@app.get('/structures/pipeline/peptide_neighbours/set/<string:slug>')
def set_peptide_neighbours_handler(slug):
    structureset, success, errors = lists.structureSet(slug).get()
    success_array = []
    errors_array = []
    for pdb_code in structureset['set']:
        try:
            data, success, errors = actions.peptide_neighbours(pdb_code)
            if data:
                success_array.append(pdb_code)
            else:
                errors_array.append(pdb_code)
        except:
            errors_array.append(pdb_code)
    data = {
        'success':success_array,
        'errors':errors_array
    }
    return data


# Step 8
@app.get('/structures/pipeline/extract_peptides/set/<string:slug>')
def set_extract_peptides_handler(slug):
    structureset, success, errors = lists.structureSet(slug).get()
    success_array = []
    errors_array = []
    for pdb_code in structureset['set']:
        try:
            data, success, errors = actions.extract_peptides(pdb_code)
            if data:
                success_array.append(pdb_code)
            else:
                errors_array.append(pdb_code)
        except:
            errors_array.append(pdb_code)
    data = {
        'success':success_array,
        'errors':errors_array
    }
    return data


route_actions = {
    'peptide_angles': actions.measure_peptide_angles
}



# Step X
@app.get('/structures/pipeline/<string:route_action>/set/<path:slug>')
def pipeline_set_handler(route_action, slug):
    structureset, success, errors = lists.structureSet(slug).get()
    success_array = []
    errors_array = []
    for pdb_code in structureset['set']:
        data, success, errors = pipeline_actions[route_action](pdb_code)
        if data:
            success_array.append(pdb_code)
        else:
            errors_array.append({'pdb_code':pdb_code,'errors':errors})
    error_types = {}
    for errors in errors_array:
        for error in errors['errors']:
            if not error['error'] in error_types:
                error_type = error['error']
                error_types[error_type] = {'count':0, 'set':[]}
            error_types[error_type]['set'].append(error['pdb_code'])
            error_types[error_type]['count'] += 1
    data = {
        'success':success_array,
        'success_count': len(success_array),
        'errors':errors_array,
        'errors_count': len(errors_array),
        'error_types': error_types
    }
    return data


# Step X
@app.get('/structures/pipeline/<string:route_action>/<string:pdb_code>')
def pipeline_item_handler(route_action, pdb_code):
    data, success, errors = pipeline_actions[route_action](pdb_code)
    return data['histo_info']









# Step 0
@app.get('/structures/pipeline/clean/<string:pdb_code>')
def clean_record_handler(pdb_code):
    data, success, errors = actions.clean_record(pdb_code)
    return data['histo_info']


# Step 1
@app.get('/structures/pipeline/fetch/<string:pdb_code>')
def fetch_pdb_data_handler(pdb_code):
    data, success, errors = actions.fetch_pdb_data(pdb_code)
    return data['histo_info']


# Step 2
@app.get('/structures/pipeline/assign/<string:pdb_code>')
def automatic_assignment_handler(pdb_code):
    logging.warn("ASSIGNING")
    data, success, errors = actions.automatic_assignment(pdb_code)
    return data['histo_info']


# Step 3
@app.get('/structures/pipeline/split/<string:pdb_code>')
def split_structure_handler(pdb_code):

    data, success, errors = actions.split_structure(pdb_code)
    return data['histo_info']


# Step 4
@app.get('/structures/pipeline/align/<string:pdb_code>')
def align_structures_handler(pdb_code):
    data, success, errors = actions.align_structures(pdb_code)
    return data['histo_info']


# Step 5
@app.get('/structures/pipeline/match/<string:pdb_code>')
def match_structures_handler(pdb_code):
    data, success, errors = actions.match_structure(pdb_code)
    return data['histo_info']


# Step 6
@app.get('/structures/pipeline/peptide_positions/<string:pdb_code>')
def peptide_positions_handler(pdb_code):
    data, success, errors = actions.peptide_positions(pdb_code)
    return data['histo_info']


# Step 7
@app.get('/structures/pipeline/peptide_neighbours/<string:pdb_code>')
def peptide_neighbours_handler(pdb_code):
    data, success, errors = actions.peptide_neighbours(pdb_code)
    return data['histo_info']


# Step 8
@app.get('/structures/pipeline/extract_peptides/<string:pdb_code>')
def extract_peptides_handler(pdb_code):
    data, success, errors = actions.extract_peptides(pdb_code)
    return data['histo_info']





# Step 10
@app.get('/structures/pipeline/flare/<string:pdb_code>')
def generate_flare_file_handler(pdb_code):
    data, success, errors = actions.generate_flare_file(pdb_code)
    return data['flare_info']







### Sequence pipeline ###

@app.get('/sequence/pipeline/clean/<string:mhc_class>/<string:locus>')
def simplify_sequence_set_handler(mhc_class, locus):
    data, success, errors = actions.get_simplified_sequence_set(mhc_class, locus)
    return data















### REFACTOR ALL BELOW THE FOLD TO THIN CONTROLLERS AND REMOVING UNUSED CODE/HANDLERS ###


# need to see how this is used now, possibly refactor
@app.get('/structures/<string:pdb_code>/approve/best_match')
def structure_approve_best_match_handler(pdb_code):
    variables = common.request_variables(['return_to'])
    histo_info, success, errors = histo.structureInfo(pdb_code).get()
    complex_type = {'complex_type':histo_info['best_match']['best_match']}
    histo_info, success, errors = histo.structureInfo(pdb_code).put('complex_type', complex_type)
    return redirect(variables['return_to'])


# search for new structures. Need options to hide already matched structures
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


# make this a linked first point of call for new structures
@app.get('/structures/assign_automatically/<string:pdb_code>')
def structures_automatic_assignment_handler(pdb_code):
    variables = actions.automatic_assignment(pdb_code)
    return variables


#TODO not sure how this is used anymore check
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


@app.get('/structures/split_assemblies/<string:pdb_code>')
def split_assemblies(pdb_code):
    complexes, success, errors = filesystem.get('constants/shared/complexes')
    histo_info, success, errors = histo.structureInfo(pdb_code).get()
    if 'split_info' not in histo_info:
        current_assembly = pdb.RCSB().load_structure(pdb_code)
        split_information = structure.split_assemblies(histo_info, current_assembly, pdb_code)
        histo_info, success, errors = histo.structureInfo(pdb_code).put('split_info', split_information)
    variables = {
        'pdb_code': pdb_code,
        'histo_info': histo_info,
        'complexes':complexes
    }
    return template.render('structure_assembly_splitting', variables)


@app.get('/structures/align_complexes/<string:pdb_code>')
def align_complexes(pdb_code):
    complexes, success, errors = filesystem.get('constants/shared/complexes')
    histo_info, success, errors = histo.structureInfo(pdb_code).get()
    align_info = {}
    mhc_alpha_chains = []
    #mhc_beta_chains = []
    aligned_assignment = ''
    for chain in histo_info['chains']:
        if 'class_i_alpha' in histo_info['chains'][chain]['chain_type']:
            mhc_alpha_chains = histo_info['chains'][chain]['assignments']
            aligned_assignment = 'class_i_alpha'
    errors
    if 'split_info' in histo_info:
        i = 1
        for complex in histo_info['split_info']['complexes']:
            for chain in mhc_alpha_chains:
                if chain in complex['chains']:
                    complex_number = 'complex_' + str(i)
                    current_alignment = {
                        'aligned_chain': chain,
                        'chain_assignment': aligned_assignment,
                        'filename': complex['filename']
                    }
                    try:
                        align_information = structure.align_structures('class_i', pdb_code, str(i), chain)
                        if align_information:
                            current_alignment['rms'] = align_information
                        else:
                            current_alignment['errors'] = ['unable_to_load']
                    except:
                        current_alignment['errors'] = ['unable_to_align']
                    align_info[complex_number] = current_alignment
            i += 1
        histo_info, success, errors = histo.structureInfo(pdb_code).put('align_info', align_info)  
    else:
        align_info = {'error':'structure_not_split'}  
    variables = {
        'pdb_code': pdb_code,
        'histo_info': histo_info,
        'complexes':complexes
    }
    return template.render('structure_alignment', variables)


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


@app.get('/api/v1/structures/information/<string:pdb_code>')
@app.get('/structures/information/<string:pdb_code>')
def structure_info_handler(pdb_code):
    unmatched, success, errors = lists.structureSet('unmatched').get()
    unmatched_structure = False
    if pdb_code in unmatched['set']:
        unmatched_structure = True


    # get the constants about complexes
    complexes, success, errors = filesystem.get('constants/shared/complexes')


    # get or create the histo dataset for this structure
    histo_info, success, errors = histo.structureInfo(pdb_code).get()

    rcsb = pdb.RCSB()

    # get the rcscb held data, the rscb json data and the pdb data
    pdb_info = rcsb.get_info(pdb_code)

    pdb_file = rcsb.fetch(pdb_code)

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
        'pdb_code':pdb_code, 
        'doi_url':doi_url,
        'histo_info':histo_info,
        'unmatched':unmatched_structure
    }
    if 'api' in str(request.url_rule):
        return variables
    else:
        variables['pdb_info'] = pdb_info
        variables['pdb_file'] = pdb_file
        variables['complexes'] = complexes
        variables['possible_complexes_labels'] = basic_information['possible_complexes_labels']
        return template.render('structure_info', variables)


@app.get('/sets/intersection')
def sets_intersection_handler():
    return template.render('sets_intersection', {'setlist':{}})



@app.get('/sets/create')
def sets_create_form_handler():
    return template.render('sets_create', {'variables':{},'structureset':None,'errors':['no_data']})


@app.post('/sets/create')
def sets_create_action_handler():
    params = ['set_ui_text','set_members']
    variables = {}
    errors = None
    slug = None
    members = None
    structureset = None
    variables = common.request_variables(params)
    if 'set_ui_text' in variables:
        if variables['set_ui_text'] is not None:
            slug = common.slugify(variables['set_ui_text'])
            logging.warn(slug)
        else:
            errors.append('no_ui_text')
    else:
        errors.append('no_ui_text')
    if 'set_members' in variables:
        if variables['set_members'] is not None:
            try:
                if '\'' in variables['set_members']:
                    variables['set_members'] = variables['set_members'].replace('\'','"')
                members = json.loads(variables['set_members'])
                members = [member.lower() for member in members]
                logging.warn(members)
            except:
                errors.append('not_json')
        else:
            errors.append('no_members')
    else:
        errors.append('no_members')
    if errors is None:
        already_exists = lists.structureSet(slug).check_exists()
        if not already_exists:
            structureset, success, errors = lists.structureSet(slug).put(members)
        else:
            structureset, success, errors = lists.structureSet(slug).get()
            errors.append('already_exists')
    logging.warn(errors)
    return template.render('sets_create', {'variables':variables,'errors':errors,'structureset':structureset,'errors':errors})







@app.get('/sets/<path:slug>')
def sets_display_handler(slug):
    structureset = get_hydrated_structure_set(slug)
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










