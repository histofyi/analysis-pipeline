from flask import Blueprint, current_app, request, redirect, make_response, Response


import functions.lists as lists
from .pipeline_actions import initialise, get_pdb_structure, parse_pdb_header, fetch_rcsb_info, alike_chains, match_chains
import logging
import json


structure_pipeline_views = Blueprint('structure_pipeline_views', __name__)


def get_aws_config():
    if current_app.config['USE_LOCAL_S3'] == True:
        return {
            'aws_access_key_id':current_app.config['LOCAL_ACCESS_KEY_ID'],
            'aws_access_secret':current_app.config['LOCAL_ACCESS_SECRET'],
            'aws_region':current_app.config['AWS_REGION'],
            's3_url':current_app.config['LOCAL_S3_URL'],
            'local':True,
            's3_bucket':current_app.config['S3_BUCKET'] 
        }
    else:
        return {
            'aws_access_key_id':current_app.config['AWS_ACCESS_KEY_ID'],
            'aws_access_secret':current_app.config['AWS_ACCESS_SECRET'],
            'aws_region':current_app.config['AWS_REGION'],
            'local':False,
            's3_bucket':current_app.config['S3_BUCKET'] 
        }


pipeline_actions = {
    'class_i': {
        'initialise':{'action':initialise,'next':'fetch_structure'},
        'fetch_structure':{'action':get_pdb_structure,'next':'parse_structure'},
        'parse_structure':{'action':parse_pdb_header,'next':'fetch_information'},
        'fetch_information':{'action':fetch_rcsb_info,'next':'alike_chains'},
        'alike_chains':{'action':alike_chains,'next':'match_chains'},
        'match_chains':{'action':match_chains,'next':'split_structure'}
        # TODO re-implement/refactor these actions
#        'split': {'action':split_structure, 'blocks':['split_info']}, # splits structure into single assemblies
#        'align': {'action':align_structures, 'blocks':['align_info']}, # aligns structure against canonical one
#        'peptide_neighbours': {'action':peptide_neighbours, 'blocks':['neighbour_info']},
#        'peptide_positions': {'action':peptide_positions, 'blocks':['peptide_positions']},
#        'peptide_angles': {'action':measure_peptide_angles, 'blocks':['peptide_angle_info']},
#        'extract_peptides': {'action':extract_peptides, 'blocks':[]},
#        'cleft_angles': {'action': measure_neighbour_angles, 'blocks':['cleft_angle_info']}           
    },
    'class_ii': {}
}



# Set pipeline step handler
@structure_pipeline_views.get('/<string:mhc_class>/<string:route>/set/<path:slug>')
def pipeline_set_handler(mhc_class, route, slug):
    structureset, success, errors = lists.structureSet(slug).get()
    success_array = []
    errors_array = []
    error_count = 0
    for pdb_code in structureset['set']:
        data, success, errors = pipeline_actions[mhc_class][route]['action'](pdb_code, aws_config=get_aws_config())
        if data:
            success_array.append(pdb_code)
            if errors:
                errors_array.append({'pdb_code':pdb_code,'errors':errors})
                error_count += 1
        else:
            errors_array.append({'pdb_code':pdb_code,'errors':errors})
            error_count += 1
    data = {
        'success':success_array,
        'success_count': len(success_array),
        'item_count': len(structureset['set']),
        'error_count': error_count,
        'errors':errors_array,
        'next':pipeline_actions[mhc_class][route]['next'], 
        'mhc_class':mhc_class
    }
    return data



# Pipeline step handler
@structure_pipeline_views.get('/<string:mhc_class>/<string:route>/<string:pdb_code>')
def pipeline_item_handler(mhc_class, route, pdb_code):
    data, success, errors = pipeline_actions[mhc_class][route]['action'](pdb_code, aws_config=get_aws_config())
    if success:
        return {'data':data, 'next':pipeline_actions[mhc_class][route]['next'], 'mhc_class':mhc_class, 'pdb_code':pdb_code}
    else:
        return {'erors':errors}




