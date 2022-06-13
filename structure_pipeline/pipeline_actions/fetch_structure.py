from typing import Dict, List, Tuple

from datetime import datetime

from common.providers import s3Provider, httpProvider, awsKeyProvider
from common.helpers import fetch_core, update_block, process_step_errors

import logging

def download_cif_file(pdb_code, assembly_id):
    url = f'https://www.ebi.ac.uk/pdbe/coordinates/{pdb_code}/assembly?id={assembly_id}'
    cif_data = httpProvider().get(url, 'txt')
    return cif_data


def build_assembly_block(key):
    return {
            'files':{
                    'file_key': key,
                    'last_updated': datetime.now().isoformat()
                }
            }


def get_pdbe_structures(pdb_code:str, aws_config: Dict, force:bool=False):
    step_errors = []
    core, success, errors = fetch_core(pdb_code, aws_config)
    if errors:
        step_errors.append(errors)
    s3 = s3Provider(aws_config)
    action = {'assemblies':{'files':{}}}
    has_updates = False
    if core['assembly_count'] is not None:
        assembly_id = 1
        while assembly_id <= core['assembly_count']:
            assembly_identifier = f'{pdb_code}_{assembly_id}'
            key = awsKeyProvider().cif_file_key(assembly_identifier, 'split')
            # get the local file
            cif_data, success, errors = s3.get(key, data_format='cif')
            # if the local file is not there
            if not success:
                has_updates = True
                cif_data = download_cif_file(pdb_code, assembly_id)
                data, success, errors = s3.put(key, cif_data, data_format='cif')
                if success:
                    action['assemblies']['files'][str(assembly_id)] = build_assembly_block(key)
                    print (f'FILE DOWNLOADED FOR {assembly_identifier}')
            else:
                if 'files' in core['assemblies']:
                    if str(assembly_id) in core['assemblies']['files']:
                        action['assemblies']['files'][str(assembly_id)] = core['assemblies']['files'][str(assembly_id)]
                        print (f'FILE ALREADY EXISTS FOR {assembly_identifier}')
                    else:
                        has_updates = True
                        action['assemblies']['files'][str(assembly_id)] = build_assembly_block(key)
                        print (f'FILE ALREADY EXISTS FOR {assembly_identifier}')
                else:
                    action['assemblies']['files'][str(assembly_id)] = build_assembly_block(key)
                    has_updates = True
                    print (f'FILE ALREADY EXISTS FOR {assembly_identifier}')
            assembly_id += 1
        if has_updates:
            update = action
            data, success, errors = update_block(pdb_code, 'core', 'info', update, aws_config)
            if errors:
                step_errors.append(errors)
            core = data
    output = {
        'action': action,
        'core': core
    }
    return output, success, step_errors

