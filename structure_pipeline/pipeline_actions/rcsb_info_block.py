from .s3 import s3Provider
from .http import httpProvider
from .common import build_s3_block_key, update_block

import logging


def download_rcsb_info(pdb_code):
    url = 'https://data.rcsb.org/rest/v1/core/entry/{pdb_code}'.format(pdb_code = pdb_code)
    pdb_info = httpProvider().get(url, 'json')
    return pdb_info



def fetch_rcsb_info(pdb_code, aws_config):
    key = build_s3_block_key(pdb_code, 'rcsb', 'info')
    s3 = s3Provider(aws_config)
    payload = download_rcsb_info(pdb_code)
    step_errors = []
    s3.put(key, payload)
    update = {}
    try:
        update['publication'] = payload['rcsb_primary_citation']
    except:
        step_errors.append('unable_to_assign_publication')
    try: 
        update['title'] = payload['struct']['pdbx_descriptor']
    except:
        step_errors.append('unable_to_assign_title')
    data, success, step_errors = update_block(pdb_code, 'core', 'info', update, aws_config)
    return payload, True, None