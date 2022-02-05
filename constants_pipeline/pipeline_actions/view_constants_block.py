from .filesystem import filesystemProvider
from .s3 import s3Provider
from .constants import CONSTANTS_FILES, constants_details

from .common import build_s3_constants_key

import logging

fs = filesystemProvider('constants_pipeline/files')

def view_constants(aws_config):
    s3 = s3Provider(aws_config)
    constants = []
    for slug in CONSTANTS_FILES:
        key = build_s3_constants_key(slug)
        data, success, errors = s3.get(key)       
        if data:
            metadata = constants_details(slug)
            metadata['data'] = data
            constants.append(metadata)
    return {'constants':constants}, True, []