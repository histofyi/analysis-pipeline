from .filesystem import filesystemProvider
from .s3 import s3Provider
from .constants import CONSTANTS_FILES

from .common import build_s3_constants_key

import logging

fs = filesystemProvider('constants_pipeline/files')



def view_constants(aws_config):
    s3 = s3Provider(aws_config)
    constants = []
    for filename in CONSTANTS_FILES:
        key = build_s3_constants_key(filename)
        data, success, errors = s3.get(key)       
        if data:
            constants.append({'slug':filename, 'data':data})
    return {'constants':constants}, True, []