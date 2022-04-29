from typing import Dict, Tuple, List, Optional, Union

from common.providers import s3Provider, awsKeyProvider, httpProvider
from common.helpers import update_block, fetch_constants, slugify
from common.models import itemSet

import csv


import logging


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
    core, success, errors = s3.get(core_key)
    peptide_matches = []
    exact_match = False
    possible_matches = []
    update = {'peptide':core['peptide']}
    if 'peptide' in core:
        if core['peptide'] is not None:
            peptide_sequence = core['peptide']['sequence'].upper()
            query = f'https://query-api.iedb.org/epitope_search?limit=10&linear_sequence=eq.{peptide_sequence}&select=curated_source_antigens'
            results = httpProvider().get(query, 'json')
            for item in results:
                if item is not None:
                    if 'curated_source_antigens' in item:
                        if item['curated_source_antigens'] is not None:
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
            peptide_lengths = fetch_constants("peptide_lengths")
            try:
                peptide_length_name = [length for length in peptide_lengths if peptide_lengths[length]['length'] == len(core['peptide']['sequence'])][0]
            except:
                peptide_length_name = None 
                step_errors.append('no_matching_peptide_length_name') 
            update['peptide']['length'] = {
                'numeric':len(core['peptide']['sequence']),
                'text': peptide_length_name
            }
            if exact_match:
                update['peptide']['info'] = peptide_matches
                s3.put(peptide_key, peptide_matches)
                #TODO peptide organism set creation when we have a clean set of organism names
            elif len(peptide_matches) > 1:
                step_errors = ['unambiguous_peptide_matches']
                s3.put(peptide_key, peptide_matches)
            else:
                step_errors = ['no_peptide_matches']
            
            members = [pdb_code]
            set_title = f'Structures including {peptide_sequence}'
            set_slug = slugify(peptide_sequence)
            set_description = f'{peptide_sequence} containing structures'
            context = 'peptide_sequence'
            itemset, success, errors = itemSet(set_slug, context).create_or_update(set_title, set_description, members, context)


            if peptide_length_name:
                members = [pdb_code]
                set_title = f'{peptide_length_name.capitalize()} structures'
                set_slug = slugify(peptide_length_name)
                set_description = f'{peptide_length_name} containing structures'
                context = 'peptide_length'
                itemset, success, errors = itemSet(set_slug, context).create_or_update(set_title, set_description, members, context)


            data, success, errors = update_block(pdb_code, 'core', 'info', update, aws_config)
            core = data   
    output = {
        'action':{'exact_match':exact_match,'possible_matches':possible_matches},
        'core':core
    }
    return output, True, []