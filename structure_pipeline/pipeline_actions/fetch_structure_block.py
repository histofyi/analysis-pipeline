from .s3 import s3Provider
from .http import httpProvider
from .common import build_s3_structure_key, pdb_loader

import logging


def download_pdb_file(pdb_code):
    url = 'https://files.rcsb.org/download/{pdb_code}.pdb'.format(pdb_code = pdb_code)
    pdb_data = httpProvider().get(url, 'txt')
    return pdb_data



def get_pdb_structure(pdb_code, aws_config):
    filepath = build_s3_structure_key(pdb_code, 'raw')
    s3 = s3Provider(aws_config)
    pdb_data, success, errors = s3.get(filepath, data_format='pdb')
    if not success:
        pdb_data = download_pdb_file(pdb_code)
        if pdb_data:
            s3.put(filepath, pdb_data, data_format='pdb')
        return pdb_data, True, None
    else:
        return pdb_data.decode('utf-8'), True, None
