from typing import Dict, Tuple, List, Optional, Union

from common.providers import s3Provider, awsKeyProvider
from common.helpers import fetch_core

import logging

def view(pdb_code:str, aws_config: Dict, force: bool=False) -> Tuple[Dict, bool, Union[List, None]]:
    """
    This function returns all currently processed data for a pdb_code as a dictionary
    
    Args:
        pdb_code (str): the pdb code of a structure
        aws_config (Dict): the configuration details for AWS for the current app
        force (bool): currently unused

    Returns:
        Dict: A dictionary of generated data (data)
        bool: A boolean of True or False (success)
        List: A list of error strings (errors)
    """
    blocks = ['chains', 'allele_match', 'peptide_matches', 'peptide_neighbours', 'peptide_structures', 'peptide_angles', 'cleft_angles', 'c_alpha_distances']
    core, success, errors = fetch_core(pdb_code, aws_config)
    core['pdb_code'] = pdb_code
    core['facets'] = {}
    s3 = s3Provider(aws_config)
    for block in blocks:
        block_key = awsKeyProvider().block_key(pdb_code, block, 'info')
        block_data, success, errors = s3.get(block_key)
        core['facets'][block] = block_data
    output = {
        'action': core,
        'core': None
    } 
    return output, True, None