from typing import List, Dict, Tuple, Union
from common.providers import s3Provider, awsKeyProvider, PDBeProvider, rcsbProvider
from common.models import itemSet

from common.helpers import fetch_constants, fetch_core, update_block, slugify, one_letter_to_three



direct_mapping = ['homo_sapiens','macaca_mulatta','equus_caballus','felis_catus','ailuropoda_melanoleuca','bos_taurus','oryctolagus_cuniculus','sus_scrofa','mus_musculus','rattus_norvegicus']



def map_pockets(pdb_code, aws_config, force=False):
    s3 = s3Provider(aws_config)
    mhc_pockets = fetch_constants('pockets')['class_i']
    print (mhc_pockets)
    step_errors = []
    sequence = None
    required_chain = 'class_i_alpha'
    core, success, errors = fetch_core(pdb_code, aws_config)
    if 'organism' in core:
        if 'scientific_name' in core['organism']:
            organism = slugify(core['organism']['scientific_name'])
        else:
            organism = None
    else:
        organism = None
    if organism:
        if organism in direct_mapping:
            chains_key = awsKeyProvider().block_key(pdb_code, 'chains', 'info')
            chains_data, success, errors = s3.get(chains_key)
            for chain in chains_data:
                if chains_data[chain]['best_match']['match'] == required_chain:
                    sequence = chains_data[chain]['sequences'][0]
            if sequence:
                action = {'pockets':{}}
                for pocket in mhc_pockets:
                    action['pockets'][pocket] = {}
                    for position in mhc_pockets[pocket]:
                        position_number = int(position[1:])
                        residue = sequence[position_number - 1]
                        action['pockets'][pocket][position] = {
                            'number': str(position_number),
                            'one_letter': residue,
                            'three_letter': one_letter_to_three(residue),
                            'chain':required_chain
                        }
            else:
                step_errors.append('no_sequence')
                action = {'pockets':None}
        else:
            step_errors.append('indirect_mapping')
            action = {'pockets':None}
    else:
        step_errors.append('no_organism_found')
        action = {'pockets':None}

    if len(step_errors) == 0:
        pockets_key = awsKeyProvider().block_key(pdb_code, 'pockets', 'info')
        s3.put(pockets_key, action)
    output = {
        'action':action,
        'core':core
    }
    return output, True, step_errors


