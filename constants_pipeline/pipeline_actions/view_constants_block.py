from common.providers import s3Provider, awsKeyProvider

from .constants import CONSTANTS_FILES, constants_details

import logging

def view_constants(aws_config):
    s3 = s3Provider(aws_config)
    constants = []
    for slug in CONSTANTS_FILES:
        key = awsKeyProvider().constants_key(slug)
        data, success, errors = s3.get(key)       
        if data:
            metadata = constants_details(slug)
            metadata['data'] = data
            constants.append(metadata)
    return {'constants':constants}, True, []