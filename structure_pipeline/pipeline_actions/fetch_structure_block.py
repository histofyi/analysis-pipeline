from typing import Dict, List, Tuple

from datetime import datetime

from common.providers import s3Provider, httpProvider, awsKeyProvider
from common.helpers import fetch_core, update_block, process_step_errors

import logging

def download_cif_file(pdb_code, assembly_id):
    url = f'https://www.ebi.ac.uk/pdbe/coordinates/{pdb_code}/assembly?id={assembly_id}'
    cif_data = httpProvider().get(url, 'txt')
    return cif_data


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
            key = awsKeyProvider().cif_file_key(assembly_id, 'split')
            cif_data, success, errors = s3.get(key, data_format='cif')
            if errors:
                step_errors.append(errors)
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
                if 'files' in core['assemblies']:
                    action['assemblies']['files'][str(assembly_id)] = core['assemblies']['files'][str(assembly_id)]
                else:
                    # TODO fix the edge case where we already have the files but have initialsed the records
                    logging.warn("EDGE CASE TO FIX!")
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
    return output, success, process_step_errors(step_errors)

