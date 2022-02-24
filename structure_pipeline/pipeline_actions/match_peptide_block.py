from typing import Dict, Tuple, List, Optional, Union

from common.providers import s3Provider, awsKeyProvider, filesystemProvider
from common.helpers import update_block


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
            for row in result:
                if data['peptide'].lower() == row[2].lower():
                    peptide_match = {
                        'sequence':row[2],
                        'organism':row[13],
                        'protein':row[11]
                    }
                    peptide_matches.append(peptide_match)
    peptide_key = awsKeyProvider().block_key(pdb_code, 'peptide_matches', 'info')
    if len(peptide_matches) == 1:
        update = {}
        update['peptide_info'] = peptide_matches[0]

        success = True  
        s3.put(peptide_key, peptide_matches)
        data, success, errors = update_block(pdb_code, 'core', 'info', update, aws_config)
    elif len(peptide_matches) > 1:
        step_errors = ['unambiguous_peptide_matches']
        s3.put(peptide_key, peptide_matches)
    else:
        step_errors = ['no_peptide_matches']
    return {'pdb_code':pdb_code, 'peptide_matches': peptide_matches}, success, step_errors