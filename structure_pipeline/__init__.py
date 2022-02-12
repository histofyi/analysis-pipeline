from flask import Blueprint, current_app, request, redirect, make_response, Response


from common.decorators import check_user, requires_privilege, templated

#from .pipeline_actions import initialise
#from .pipeline_actions import get_pdb_structure
#from .pipeline_actions import initialise, get_pdb_structure, parse_pdb_header, fetch_rcsb_info, alike_chains, match_chains
#from .pipeline_actions import initialise, get_pdb_structure, parse_pdb_header, fetch_rcsb_info, alike_chains, match_chains
#rom .pipeline_actions import initialise, get_pdb_structure, parse_pdb_header, fetch_rcsb_info, alike_chains, match_chains
#from .pipeline_actions import initialise, get_pdb_structure, parse_pdb_header, fetch_rcsb_info, alike_chains, match_chains




import logging
import json


structure_pipeline_views = Blueprint('structure_pipeline_views', __name__)



@structure_pipeline_views.get('/')
@check_user
@requires_privilege('users')
@templated('structures/index')
def structure_home_handler(userobj):
    return {'userobj': userobj, 'actions':[]}



