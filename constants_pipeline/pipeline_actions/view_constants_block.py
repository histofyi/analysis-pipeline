from .filesystem import filesystemProvider
from .s3 import s3Provider

from .common import build_s3_constants_key

import logging

fs = filesystemProvider('constants_pipeline/files')

constants_files = ['amino_acids','chains','class_i_starts','hetatoms','loci','peptide_lengths','species_overrides','species']


def view_constants(aws_config):
    s3 = s3Provider(aws_config)
    constants = []
    for filename in constants_files:
        key = build_s3_constants_key(filename)
        data, success, errors = s3.get(key)       
        if data:
            constants.append({'name':filename, 'data':data})
    return {'constants':constants}, True, []