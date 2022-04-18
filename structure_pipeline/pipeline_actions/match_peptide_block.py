from typing import Dict, Tuple, List, Optional, Union

from common.providers import s3Provider, awsKeyProvider, filesystemProvider, httpProvider
from common.helpers import update_block, fetch_constants, slugify


import csv

fs = filesystemProvider('structure_pipeline/files')

import logging

def match_peptide(pdb_code:str, aws_config: Dict, force: bool=False) -> Tuple[Dict, bool, Union[List, None]]:
    """
    This function matches the peptide sequence to a csv file from the IEDB - https://www.iedb.org/ - the csv file needs to be regenerated regularly
    
    Args:
        pdb_code (str): the pdb code of a structure
        aws_config (Dict): the configuration details for AWS for the current app
        force (bool): whether the data in this step should be overwritten. 

    Returns:
        Dict: A dictionary of generated data (data)
        bool: A boolean of True or False (success)
        List: A list of error strings (errors)
    """
    step_errors = [] 
    success = False
    s3 = s3Provider(aws_config)
    csv_data, success, errors = fs.get('iedb_latest', format='csv')
    result = [row for row in csv.reader(csv_data.splitlines(), delimiter=',')]

    core_key = awsKeyProvider().block_key(pdb_code, 'core', 'info')
    data, success, errors = s3.get(core_key)
    
    print(data['peptide'])

    peptide_matches = []

    if 'peptide' in data:
        if data['peptide'] is not None:
            # TODO exclude first row
            # TODO include information on peptide if it has been modified
            # TODO create named columns in the rows
            for row in result:
                if data['peptide'].lower() == row[2].lower():
                    peptide_match = {
                        'sequence':row[2],
                        'organism':row[13],
                        'protein':row[11]
                    }
                    peptide_matches.append(peptide_match)
    peptide_key = awsKeyProvider().block_key(pdb_code, 'peptide_matches', 'info')
    update = {}
    peptide_lengths = fetch_constants("peptide_lengths")
    try:
        peptide_length_name = [length for length in peptide_lengths if peptide_lengths[length]['length'] == len(data['peptide'])][0]
    except:
        peptide_length_name = None 
        step_errors.append('no_matching_peptide_length_name') 
    update['peptide_length'] = {
        'value':len(data['peptide']),
        'display': peptide_length_name
    }
    if len(peptide_matches) == 1:
        update['peptide_info'] = peptide_matches[0]
        s3.put(peptide_key, peptide_matches)
    elif len(peptide_matches) > 1:
        step_errors = ['unambiguous_peptide_matches']
        s3.put(peptide_key, peptide_matches)
    else:
        step_errors = ['no_peptide_matches']
    data, success, errors = update_block(pdb_code, 'core', 'info', update, aws_config)
    # TODO add to speficic peptide sets
    return {'pdb_code':pdb_code, 'peptide_matches': peptide_matches}, success, step_errors



def api_match_peptide(pdb_code:str, aws_config: Dict, force: bool=False) -> Tuple[Dict, bool, Union[List, None]]:
    """
    This function matches the peptide sequence to a the IEDB API

    Sample query - https://query-api.iedb.org/epitope_search?limit=10&linear_sequence=eq.SIINFEKL
    
    Args:
        pdb_code (str): the pdb code of a structure
        aws_config (Dict): the configuration details for AWS for the current app
        force (bool): whether the data in this step should be overwritten. 

    Returns:
        Dict: A dictionary of generated data (data)
        bool: A boolean of True or False (success)
        List: A list of error strings (errors)
    """

    results = []
    step_errors = [] 
    success = False
    s3 = s3Provider(aws_config)
    core_key = awsKeyProvider().block_key(pdb_code, 'core', 'info')
    data, success, errors = s3.get(core_key)

    peptide_matches = []
    exact_match = False
    possible_matches = []

    if 'peptide' in data:
        if data['peptide'] is not None:
            peptide_sequence = data['peptide'].upper()
            query = f'https://query-api.iedb.org/epitope_search?limit=10&linear_sequence=eq.{peptide_sequence}&select=curated_source_antigens'
            results = httpProvider().get(query, 'json')
            for item in results:
                peptide_match = {
                        'organism':item['curated_source_antigens'][0]['source_organism_name'],
                        'protein':item['curated_source_antigens'][0]['name']
                }
                possible_matches.append(peptide_match)
            if len(possible_matches) > 0:
                unique_matches = []
                for match in peptide_matches:
                    peptide_details = match['organism'] + ' ' + match['protein']
                    if not slugify(peptide_details) in unique_matches:
                        unique_matches.append(slugify(peptide_details))
                        peptide_matches.append(match)
                else:
                    peptide_matches = possible_matches[0]
                    exact_match = True
            peptide_key = awsKeyProvider().block_key(pdb_code, 'peptide_matches', 'info')
            update = {}
            peptide_lengths = fetch_constants("peptide_lengths")
            try:
                peptide_length_name = [length for length in peptide_lengths if peptide_lengths[length]['length'] == len(data['peptide'])][0]
            except:
                peptide_length_name = None 
                step_errors.append('no_matching_peptide_length_name') 
            update['peptide_length'] = {
                'value':len(data['peptide']),
                'display': peptide_length_name
            }
            if exact_match:
                update['peptide_info'] = peptide_matches
                s3.put(peptide_key, peptide_matches)
            elif len(peptide_matches) > 1:
                step_errors = ['unambiguous_peptide_matches']
                s3.put(peptide_key, peptide_matches)
            else:
                step_errors = ['no_peptide_matches']
            data, success, errors = update_block(pdb_code, 'core', 'info', update, aws_config)    
    return {'exact_match':exact_match,'possible_matches':possible_matches}, True, []