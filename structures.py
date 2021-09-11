from flask import Blueprint, current_app, request, redirect, make_response, Response

import logging
import json

import functions.template as template
import functions.common as common

import functions.lists as lists
import functions.histo as histo
import functions.providers as providers
import functions.pdb as pdb



filesystem = providers.filesystemProvider(None)


structure_views = Blueprint('structure_views', __name__)


### REFACTOR ALL BELOW THE FOLD TO THIN CONTROLLERS AND REMOVING UNUSED CODE/HANDLERS ###


@structure_views.post('/lookup')
def structure_lookup_handler():
    variables = common.request_variables(['pdb_code'])
    pdb_code = variables['pdb_code'].strip().lower()[0:4]
    exists = histo.structureInfo(pdb_code).check_exists()
    if exists:
        return redirect(common.return_to(pdb_code))
    else:
        return "nope"



#@structure_views.get('/api/v1/structures/information/<string:pdb_code>')
@structure_views.get('/information/<string:pdb_code>')
def structure_info_handler(pdb_code):
    unmatched, success, errors = lists.structureSet('unmatched').get()
    unmatched_structure = False
    if '_' in pdb_code:
        pdb_code = pdb_code.split('_')[0]
    if pdb_code in unmatched['set']:
        unmatched_structure = True

    pdb_file = pdb.RCSB().fetch(pdb_code)

    # get the constants about complexes
    complexes, success, errors = filesystem.get('constants/shared/complexes')


    # get or create the histo dataset for this structure
    histo_info, success, errors = histo.structureInfo(pdb_code).get()

    # try to resolve the DOI in the rcsb data
    try:
        doi_url = pdb.RCSB().resolve_doi(histo_info['rcsb_info']['primary_citation']['pdbx_database_id_doi'])
    except:
        # TODO handle this better
        doi_url = None
    

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
        variables['pdb_file'] = pdb_file
        variables['histo_info'] = histo_info
        variables['doi_url'] = doi_url
        variables['complexes'] = complexes
        variables['description_block'] = common.describe_complex(histo_info)
        return template.render('structure_info', variables)