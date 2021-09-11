from flask import Blueprint, current_app, request, redirect, make_response, Response
from flask_caching import Cache

import logging
import json

import functions.template as template
import functions.common as common

import functions.lists as lists
import functions.histo as histo


set_views = Blueprint('set_views', __name__)


### Sets views ###


#@cache.memoize(timeout=300) - TODO FIX THIS
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


@set_views.get('/<path:slug>')
def sets_display_handler(slug):
    structureset = get_hydrated_structure_set(slug)
    return template.render('set', {'nav':'sets','set':structureset})


@set_views.get('/')
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


@set_views.get('/intersection')
def sets_intersection_handler():
    return template.render('sets_intersection', {'setlist':{}})


@set_views.get('/create')
def sets_create_form_handler():
    return template.render('sets_create', {'variables':{},'structureset':None,'errors':['no_data']})


@set_views.post('/create')
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
    return template.render('sets_create', {'variables':variables,'errors':errors,'structureset':structureset,'errors':errors})

