from typing import Dict, List, Tuple

from datetime import datetime

from common.providers import s3Provider, httpProvider, awsKeyProvider
from common.helpers import fetch_core, update_block

import logging

def download_cif_file(pdb_code, assembly_id):
    url = f'https://www.ebi.ac.uk/pdbe/coordinates/{pdb_code}/assembly?id={assembly_id}'
    cif_data = httpProvider().get(url, 'txt')
    return cif_data


def get_pdbe_structures(pdb_code:str, aws_config: Dict, force:bool=False):
    core, success, errors = fetch_core(pdb_code, aws_config)
    s3 = s3Provider(aws_config)
    action = {'assemblies':{'files':{}}}

    has_updates = False
    if core['assembly_count'] is not None:
        assembly_id = 1
        while assembly_id <= core['assembly_count']:
            assembly_identifier = f'{pdb_code}_{assembly_id}'
            key = awsKeyProvider().cif_file_key(pdb_code, assembly_identifier, 'split')
            cif_data, success, errors = s3.get(key, data_format='cif')
            if not success:
                has_updates = True
                cif_data = download_cif_file(pdb_code, assembly_id)
                data, success, errors = s3.put(key, cif_data, data_format='cif')
                action['assemblies']['files'][str(assembly_id)] = {
                    'files':{
                        'file_key': key,
                        'last_updated': datetime.now().isoformat()
                    }
                }
            else:
                action['assemblies']['files'][str(assembly_id)] = core['assemblies']['files'][str(assembly_id)]
                cif_data = cif_data.decode('utf-8')
            assembly_id += 1
        if has_updates:
            update = action
            data, success, errors = update_block(pdb_code, 'core', 'info', update, aws_config)
            core = data
    output = {
        'action': action,
        'core': core
    }
    return output, success, errors




# OLD PDB METHODS

def download_pdb_file(pdb_code:str) -> str:
    """
    This function downloads the PDB file specified

    Args:
        pdb_code (str): the code of the PDB file to be downloaded

    Returns:
        str : the PDB file

    """
    url = f'https://files.rcsb.org/download/{pdb_code}.pdb'
    pdb_data = httpProvider().get(url, 'txt')
    return pdb_data


def get_pdb_structure(pdb_code:str, aws_config: Dict, force:bool=False) -> Tuple[str, bool, List]:
    """
    This function retrieves a PDB file from S3. If the file is not already in S3 it will retrieve it from the RCSB and persist it to S3

    Args:
        pdb_code (str): the code of the PDB file
        aws_config (Dict): the AWS configuration for the environment
        force (bool): not currently used, may be implemented to force a re-download in the case of a revised structure
    """
    key = awsKeyProvider().structure_key(pdb_code, 'raw')
    s3 = s3Provider(aws_config)
    pdb_data, success, errors = s3.get(key, data_format='pdb')
    if not success:
        pdb_data = download_pdb_file(pdb_code)
        if pdb_data:
            s3.put(key, pdb_data, data_format='pdb')
        return pdb_data, True, None
    else:
        return pdb_data.decode('utf-8'), True, None


