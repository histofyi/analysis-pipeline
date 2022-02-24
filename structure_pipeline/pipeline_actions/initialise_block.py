from typing import Dict, Tuple, List, Optional, Union

from common.providers import s3Provider, awsKeyProvider

import json

def build_core(pdb_code: str) -> Dict:
    """
    This function returns the core metadata dictionary which is filled out by the different methods on the structure pipeline

    Args:
        pdb_code (str): the pdb code of the structure

    Returns:
        Dict: the default prototype data dictionary for structure metadata
    """
    return {
        'pdb_code':pdb_code,
        'organism_common':None,
        'organism_scientific':None,
        'class':None,
        'classical': None,
        'locus':None,
        'allele':None,
        'peptide':None,
        'peptide_info':{},
        'resolution':None,
        'deposition_date':None,
        'release_date':None,
        'components':{},
        'missing_residues':[],
        'complex_count':0,
        'chain_count':0,
        'title':None,
        'authors':[],
        'publication':{}
    }


def initialise(pdb_code: str, aws_config: Dict, force:bool=False) -> Tuple[Dict, bool, Union[List, None]]:
    """
    This function initialises the records for a structure. 
    
    If the force parameter is set to True it resets the record to the empty default dictionary. 
    
    This SHOULD only be used to reset the record if there is a concern about the metadata integrity in the pipeline. 
    
    Args:
        pdb_code (str): the pdb code of the structure
        aws_config (Dict): the configuration details for AWS for the current app
        force (bool): determines whether the metadata on a particular structure should be reset

    Returns:
        Dict: A dictionary of generated data (data)
        bool: A boolean of True or False (success)
        List: A list of error strings (errors)
    """
    s3 = s3Provider(aws_config)
    key = awsKeyProvider().block_key(pdb_code, 'core', 'info')
    data, success, errors = s3.get(key)
    if not data or force is True:
        data, success, errors = s3.put(key, build_core(pdb_code))
        data = json.loads(data)
    return data, success, errors