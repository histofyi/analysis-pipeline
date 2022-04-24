from typing import Dict, List, Tuple

from common.providers import PDBeProvider
from common.helpers import update_block, fetch_core, process_step_errors

import datetime


def parse_date_to_isoformat(datestring:str) -> str:
    """
        This function takes an 8 digit datestring from the PDBe return and delivers an ISO formated date string
    """
    try:
        date = datetime.date(int(datestring[0:4]), int(datestring[4:6]), int(datestring[6:8]))
        return date.isoformat()
    except:
        return datestring


def fetch_summary_info(pdb_code:str, aws_config, force=False):
    """
    This function retrieves a fetches the summary information from the PDBe REST API

    Args:
        pdb_code (str): the code of the PDB file
        aws_config (Dict): the AWS configuration for the environment
        force (bool): not currently used, may be implemented to force a re-download in the case of a revised structure
    
    Returns:
        Dict: a dictionary of the summary information from the PDBe and an attribution
    """
    step_errors = []
    summary_info, success, errors = PDBeProvider(pdb_code).fetch_summary()
    if summary_info:
        update = {'complex':{},'structure':{}}
        update['structure']['release_date'] =  parse_date_to_isoformat(summary_info['release_date'])
        update['structure']['deposition_date'] =  parse_date_to_isoformat(summary_info['deposition_date'])
        if 'revision_date' in summary_info:
            update['structure']['revision_date'] =  parse_date_to_isoformat(summary_info['revision_date'])
        update['pdb_title'] = summary_info['title'].title()
        update['assembly_count'] = len(summary_info['assemblies'])
        update['unique_chain_count'] = summary_info['number_of_entities']['polypeptide']
        update['chain_count'] =  update['assembly_count'] * update['unique_chain_count']
        update['authors'] = summary_info['entry_authors']
        data, success, errors = update_block(pdb_code, 'core', 'info', update, aws_config)
        if errors:
            step_errors.append(errors)
    if not data:
        data, success, errors = fetch_core(pdb_code, aws_config)
        if errors:
            step_errors.append(errors)
    output = {
        'action':{'summary':summary_info, 'source':'PDBe REST API summary method'},
        'core': data
    }
    return output, success, process_step_errors(step_errors)