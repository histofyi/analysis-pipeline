from .filesystem import filesystemProvider
from .s3 import s3Provider

from .common import build_s3_constants_key

import logging

fs = filesystemProvider('constants_pipeline/files')
constants_files = ['amino_acids','chains','hetatoms','loci','peptide_lengths','species_overrides']


def load_constants(aws_config):
    s3 = s3Provider(aws_config)
    for filename in constants_files:
        logging.warn(filename)
        data, success, errors = fs.get(filename)
        if success and data:
            logging.warn(data)
            key = build_s3_constants_key(filename)
            s3.put(key, data)
        
    return {'files':constants_files}, True, []