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
        'assemblies':{'files':{}},
        'organism':{},
        'class':None,
        'classical': None,
        'complex':{'assemblies':{}},
        'locus':None,
        'allele':None,
        'peptide':{
            'sequence':None,
            'info':{},
            'length':{
                'numeric':None,
                'text':None
            },
            'extended':{
                'c_terminal':False,
                'n_terminal':False
            },
            'disordered':False,
            'modified':None
        },
        'resolution':None,
        'assembly_count':None,
        'chain_count':None,
        'unique_chain_count': None,
        'assembly_count':None,
        'structure':{
            'deposition_date':None,
            'release_date':None
        },
        'missing_residues':[],
        'pdb_title':None,
        'authors':[],
        'publication':{},
        'doi':None,
        'open_access':False,
        'manually_edited': {},
        'facets':{}
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
        Dict: A dictionary of generated data (output)
        bool: A boolean of True or False (success)
        List: A list of error strings (errors)
    """
    step_errors = []
    s3 = s3Provider(aws_config)
    key = awsKeyProvider().block_key(pdb_code, 'core', 'info')
    data, success, errors = s3.get(key)
    if errors:
        step_errors.append(errors)
    if not data or force is True:
        data, success, errors = s3.put(key, build_core(pdb_code))
        data = json.loads(data)
    if errors:
        step_errors.append(errors)
    output = {
        'action':data,
        'core':data
    }
    return output, success, list(set(step_errors))