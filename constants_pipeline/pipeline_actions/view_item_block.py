from .filesystem import filesystemProvider
from .s3 import s3Provider
from .constants import CONSTANTS_FILES, constants_details

from .common import build_s3_constants_key

import logging

fs = filesystemProvider('constants_pipeline/files')



def view_item(aws_config, slug):
    s3 = s3Provider(aws_config)
    constants = []
    key = build_s3_constants_key(slug)
    data, success, errors = s3.get(key)       
    if data:
        metadata = constants_details(slug)
        metadata['data'] = data
    else:
        data = None
    return metadata, True, []