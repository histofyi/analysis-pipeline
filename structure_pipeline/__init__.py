from flask import Blueprint, current_app, request, redirect
from typing import Dict

from common.decorators import check_user, requires_privilege, templated
from common.models import itemSet

from common.forms import request_variables

from .pipeline_actions import test, view, initialise, get_pdb_structure, parse_pdb_header, fetch_rcsb_info, alike_chains, match_chains


import logging
import json


structure_pipeline_views = Blueprint('structure_pipeline_views', __name__)


pipeline_actions = {
    'class_i': {
        'test':{'action':test, 'next':None, 'name':'Test', 'show_in_list':False, 'link':False},
        'view':{'action':view, 'next':None, 'name':'View', 'show_in_list':False, 'link':False},
        'initialise':{'action':initialise, 'name':'Initialise', 'show_in_list':False, 'link':False, 'next':'fetch_structure'},
        'fetch_structure':{'action':get_pdb_structure, 'name':'Fetch structure', 'show_in_list':False, 'link':False, 'next':'parse_structure'},
        'parse_structure':{'action':parse_pdb_header, 'name': 'Parse structure', 'show_in_list':False, 'link':False, 'next':'fetch_information'},
        'fetch_information':{'action':fetch_rcsb_info, 'name': 'Fetch information', 'show_in_list':False, 'link':False, 'next':'alike_chains'},
        'alike_chains':{'action':alike_chains, 'name': 'Detect alike chains', 'show_in_list':False, 'link':False, 'next':'match_chains'},
        'match_chains':{'action':match_chains, 'name': 'Match to sequences', 'link':False, 'next':None}
        # TODO re-implement/refactor these actions
#        'split': {'action':split_structure}, # splits structure into single assemblies
#        'align': {'action':align_structures, 'blocks':['align_info']}, # aligns structure against canonical one
#        'peptide_neighbours': {'action':peptide_neighbours, 'blocks':['neighbour_info']},
#        'peptide_positions': {'action':peptide_positions, 'blocks':['peptide_positions']},
#        'peptide_angles': {'action':measure_peptide_angles, 'blocks':['peptide_angle_info']},
#        'extract_peptides': {'action':extract_peptides, 'blocks':[]},
#        'cleft_angles': {'action': measure_neighbour_angles, 'blocks':['cleft_angle_info']}           
    },
    'class_ii': {}
}


@structure_pipeline_views.get('/')
@check_user
@requires_privilege('users')
@templated('structures/index')
def structure_home_handler(userobj:Dict) -> Dict:
    """
    This handler provides the homepage for the structure pipeline section

    Args: 
        userobj (Dict): a dictionary describing the currently logged in user with the correct privileges

    Returns:
        Dict: a dictionary containing the user object and a list of possible next actions

    """
    return {'userobj': userobj, 'actions':[]}


@structure_pipeline_views.post('/redirect')
@check_user
@requires_privilege('users')
def structure_redirect_handler(userobj:Dict) -> Dict:
    """
    This handler redirects to the individual structure pipeline for the PDB code requested, or to the multiple structure pipeline with the set requested

    Args: 
        userobj (Dict): a dictionary describing the currently logged in user with the correct privileges

    Returns:
        A redirect to the relevant starting point

    """
    variables = request_variables(None, params=['pdb_code','set_slug','mhc_class'])
    logging.warn(variables)
    mhc_class = variables['mhc_class']
    if 'pdb_code' in variables:
        pdb_code = variables['pdb_code']
        url = f'/pipeline/structures/{mhc_class.lower()}/initialise/{pdb_code.lower()}'
        return redirect(url)
    elif 'set_slug' in variables:
        url = f'/pipeline/structures/{mhc_class.lower()}/initialise/set/{set_slug.lower()}'
        return redirect(url)
    else:
        return redirect('/pipeline/structures/')


@structure_pipeline_views.get('/<string:mhc_class>/<string:route>/set/<path:slug>')
def pipeline_set_handler(userobj, mhc_class, route, slug):
    """
    This handler is used to perform structure pipeline actions on a set of structures en masse

    Args: 
        userobj (Dict): a dictionary describing the currently logged in user with the correct privileges
        mhc_class (str): a string describing the mhc_class that this set relates to, e.g. class_i
        route (str): the route to the action e.g. fetch_structure. This is the key in the pipeline_actions dictionary for that action
        slug (str): the slug for the set 

    Returns:
        Dict: a dictionary containing the user object, data aboutt the action performed and the next action in the pipeline

    """
    itemset, success, errors = itemSet(slug).get()
    success_array = []
    errors_array = []
    error_count = 0
    for pdb_code in itemset['members']:
        data, success, errors = pipeline_actions[mhc_class][route]['action'](pdb_code, current_app.config['AWS_CONFIG'])
        if data:
            success_array.append(pdb_code)
            if errors:
                errors_array.append({'pdb_code':pdb_code,'errors':errors})
                error_count += 1
        else:
            errors_array.append({'pdb_code':pdb_code,'errors':errors})
            error_count += 1
    return {
        'success':success_array,
        'success_count': len(success_array),
        'item_count': len(itemset['members']),
        'error_count': error_count,
        'errors':errors_array,
        'next':pipeline_actions[mhc_class][route]['next'], 
        'mhc_class':mhc_class, 
        'userobj': userobj
    }


@structure_pipeline_views.get('/<string:mhc_class>/<string:route>/<string:pdb_code>')
@requires_privilege('users')
@templated('structures/item')
def pipeline_item_handler(userobj, mhc_class, route, pdb_code):
    """
    This handler is used to perform structure pipeline actions on a single named structure

    Args: 
        userobj (Dict): a dictionary describing the currently logged in user with the correct privileges
        mhc_class (str): a string describing the mhc_class that this set relates to, e.g. class_i
        route (str): the route to the action e.g. fetch_structure. This is the key in the pipeline_actions dictionary for that action
        pdb_code (str): the pdb_code for the structure
    Returns:
        Dict: a dictionary containing the user object, data aboutt the action performed and the next action in the pipeline

    """
    force = False
    if 'force' in request.args.to_dict():
        if request.args.get('force') == 'True':
            force = True
    data, success, errors = pipeline_actions[mhc_class][route]['action'](pdb_code.lower(), current_app.config['AWS_CONFIG'], force)
    if pipeline_actions[mhc_class][route]['next']:
        next = pipeline_actions[mhc_class][route]['next']
        next_action = {
            'name': pipeline_actions[mhc_class][next]['name'],
            'slug': next
        }
    else:
        next_action = None
    return {
            'data':data, 
            'name':pipeline_actions[mhc_class][route]['name'], 
            'next':pipeline_actions[mhc_class][route]['next'], 
            'mhc_class':mhc_class, 
            'pdb_code':pdb_code, 
            'userobj':userobj, 
            'next_action':next_action,
            'errors':errors
    }


