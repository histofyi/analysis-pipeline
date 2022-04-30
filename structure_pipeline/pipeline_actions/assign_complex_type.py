from typing import Dict, Tuple, Union, List

from common.providers import s3Provider, awsKeyProvider, PDBeProvider
from common.models import itemSet

from common.helpers import fetch_constants, fetch_core, update_block, slugify

import logging

complexes = {
    'chain_counts':{
        '2':[{
                'components':['hfe2','beta2m'],
                'unique_chains':2,
                'label': 'HFE2',
                'slug':'hfe2'

        },
        {
                'components':['h2-t22','beta2m'],
                'unique_chains':2,
                'label': 'H2-T22',
                'slug':'h2-t22'

        },
        {
                'components':['class_i_alpha','beta2m'],
                'unique_chains':2,
                'label': 'Class I without distinct peptide',
                'slug':'class_i_possibly_without_peptide'

        },
        {
                'components':['cd1b','beta2m'],
                'unique_chains':2,
                'label': 'CD1b',
                'slug':'cd1b'

        },
        {
                'components':['fcrn','beta2m'],
                'unique_chains':2,
                'label': 'Fc receptor (FcRn)',
                'slug':'fcrn'

        }],
        '3':[{
                'components':['class_i_alpha','beta2m', 'peptide'],
                'unique_chains':3,
                'label': 'MHC Class I with peptide',
                'slug':'class_i_with_peptide'

        }],
        '4':[{
               'components':['class_i_alpha', 'beta2m', 'peptide', 'cd8'],
                'unique_chains':4,
                'label': 'MHC Class I with peptide and CD8',
                'slug':'class_i_with_peptide_and_cd8'                
            },
            {
               'components':['class_i_alpha', 'beta2m', 'peptide', 'kir'],
                'unique_chains':4,
                'label': 'MHC Class I with peptide and KIR NK receptor',
                'slug':'class_i_with_peptide_and_kir'                
            }],
        '5':[{
               'components':['class_i_alpha','beta2m', 'peptide','tcr_alpha','tcr_beta'],
                'unique_chains':5,
                'label': 'MHC Class I with peptide and Alpha/Beta T cell receptor',
                'slug':'class_i_with_peptide_and_tcr'                
            }]
    }
}




def test_complex_types(found_chains, unique_chain_count):
    exact_matches = []
    possible_matches = []
    all_matches = []
    if str(unique_chain_count) in complexes['chain_counts']:
        for item in complexes['chain_counts'][str(unique_chain_count)]:
            matches = [chain for chain in found_chains if chain in item['components']]
            if len(matches) == unique_chain_count:
                exact_matches.append(item)
            confidence = len(matches)/unique_chain_count 
            if confidence > 0.6:
                possible_matches.append({
                    'matching_chains':matches,
                    'confidence':confidence,
                    'matching_chain_count':len(matches),
                    'unique_chain_count': unique_chain_count
                })
        if len(exact_matches) == 1:
            return exact_matches[0], None
        else:
            return None, possible_matches
    else:
        return None, None


def assign_complex_type(pdb_code:str, aws_config:Dict, force:bool=False) -> Tuple[Dict, bool, List]:
    print('--------------------')
    print(' ')
    print(pdb_code)
    set_errors = []
    core, success, errors = fetch_core(pdb_code, aws_config)
    action = {}
    s3 = s3Provider(aws_config)
    chains_key = awsKeyProvider().block_key(pdb_code, 'chains', 'info')
    chains, success, errors = s3.get(chains_key)
    found_chains = []
    for chain in chains:
        chain_assignment = chains[chain]['best_match']
        found_chains.append(chain_assignment)
    exact_match, possible_matches = test_complex_types(found_chains, core['unique_chain_count'])
    if exact_match:
        print('EXACT MATCH')
        update = {}
        action['complex_type'] = exact_match
        set_title = exact_match['label']
        set_slug = exact_match['slug']
        set_description = f'{set_title} structures'
        members = [pdb_code]
        itemset, success, errors = itemSet(set_slug, 'complex_type').create_or_update(set_title, set_description, members, 'complex_type')
        update['complex'] = exact_match
        data, success, errors = update_block(pdb_code, 'core', 'info', update, aws_config)
        core = data
    elif possible_matches:
        logging.warn('POSSIBLE MATCH')
        action['possible_matches'] = possible_matches
        logging.warn(possible_matches)
        set_errors.append(['unable_to_match_complex_type_exactly'])
    else:
        logging.warn('NO MATCH')
        set_errors.append(['no_matching_complex_types'])
        logging.warn(found_chains)
    output = {
        'action':action,
        'core':core
    }
    return output, True, set_errors
