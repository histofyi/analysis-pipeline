from flask import Blueprint, current_app, request, redirect, make_response, Response


import functions.lists as lists
import functions.actions as actions

import logging

pipeline_views = Blueprint('pipeline_views', __name__)


def get_aws_config():
    return {
        'aws_access_key_id':current_app.config['AWS_ACCESS_KEY_ID'],
        'aws_access_secret':current_app.config['AWS_ACCESS_SECRET'],
        'aws_region':current_app.config['AWS_REGION'],
        's3_bucket':current_app.config['S3_BUCKET'] 
    }


pipeline_actions = {
    'class_i': {
        'initialise': {'action':actions.initialise},
        'fetch': {'action':actions.fetch_pdb_data, 'blocks':['rcsb_info','basic_info']}, # retrieves structure from RCSB
        'assign': {'action':actions.automatic_assignment, 'blocks':['alike_chains','chain_assignments', 'best_match']}, # automatic assignment of structure
        'split': {'action':actions.split_structure, 'blocks':['split_info']}, # splits structure into single assemblies
        'align': {'action':actions.align_structures, 'blocks':['align_info']}, # aligns structure against canonical one
        'match': {'action':actions.match_structure, 'blocks':['match_info']}, # matches against sequences
        'peptide_neighbours': {'action':actions.peptide_neighbours, 'blocks':['neighbour_info']},
        'peptide_positions': {'action':actions.peptide_positions, 'blocks':['peptide_positions']},
        'peptide_angles': {'action':actions.measure_peptide_angles, 'blocks':['peptide_angle_info']},
        'extract_peptides': {'action':actions.extract_peptides, 'blocks':[]},
        'cleft_angles': {'action': actions.measure_neighbour_angles, 'blocks':['cleft_angle_info']}   
    },
    'class_ii': {}
}



# Set pipeline step handler
@pipeline_views.get('/<string:mhc_class>/<string:route>/set/<path:slug>')
def pipeline_set_handler(mhc_class, route, slug):
    structureset, success, errors = lists.structureSet(slug).get()
    success_array = []
    errors_array = []
    for pdb_code in structureset['set']:
        data, success, errors = pipeline_actions[mhc_class][route]['action'](pdb_code)
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


# Pipeline step handler
@pipeline_views.get('/<string:mhc_class>/<string:route>/<string:pdb_code>')
def pipeline_item_handler(mhc_class, route, pdb_code):
    data, success, errors = pipeline_actions[mhc_class][route]['action'](pdb_code, aws_config=get_aws_config())
    if data:
        if 'histo_info' in data:
            return data['histo_info']
    return {'erors':errors}




### Sequence pipeline ###

@pipeline_views.get('/<string:mhc_class>/clean_sequences/<string:locus>')
def simplify_sequence_set_handler(mhc_class, locus):
    data, success, errors = actions.get_simplified_sequence_set(mhc_class, locus)
    return data


### Epitope pipeline ###




### Positions pipeline ###
@pipeline_views.get('/<string:mhc_class>/cluster_positions')
def cluster_positions_handler(mhc_class):
    data, success, errors = actions.cluster_positions()
    return {'message':'WIP'}







# Step 0
#@app.get('/structures/pipeline/clean/<string:pdb_code>')
#def clean_record_handler(pdb_code):
#    data, success, errors = actions.clean_record(pdb_code)
#    return data['histo_info']