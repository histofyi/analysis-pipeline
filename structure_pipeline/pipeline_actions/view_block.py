from re import A
from typing import Dict, Tuple, List, Optional, Union

from common.providers import s3Provider, awsKeyProvider

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
    blocks = ['core', 'pdb', 'rcsb', 'chains', 'allele_match']
    output = {
        'pdb_code':pdb_code,
        'core':None,
        'facets':{}
    }
    s3 = s3Provider(aws_config)
    for block in blocks:
        block_key = awsKeyProvider().block_key(pdb_code, block, 'info')
        if block == 'core':
            output[block] = s3.get(block_key)[0]
        else:
            output['facets'][block] = s3.get(block_key)[0]
    return output, True, None