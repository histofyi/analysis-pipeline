from common.providers import s3Provider, awsKeyProvider


from .constants import CONSTANTS_FILES, constants_details

import logging



def view_item(aws_config, slug):
    s3 = s3Provider(aws_config)
    constants = []
    key = awsKeyProvider().constants_key(slug)
    data, success, errors = s3.get(key)       
    if data:
        metadata = constants_details(slug)
        metadata['data'] = data
    else:
        data = None
    return metadata, True, []