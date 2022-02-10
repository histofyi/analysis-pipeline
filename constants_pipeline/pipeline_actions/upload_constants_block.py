from .filesystem import filesystemProvider
from .s3 import s3Provider


from .constants import CONSTANTS_FILES
from .common import build_s3_constants_key

import json

import logging

fs = filesystemProvider('constants_pipeline/files')

constants_files = ['amino_acids','chains','class_i_starts','hetatoms','loci','peptide_lengths','species_overrides','species']


# TODO error handling and comparison
def upload_constants(aws_config):
    s3 = s3Provider(aws_config)
    constants = {}
    for slug in CONSTANTS_FILES:
        constants[slug] = CONSTANTS_FILES[slug]
        constants[slug]['unchanged'] = False
        constants[slug]['uploaded'] = False
        constants[slug]['formatted'] = False
        is_json = False
        key = build_s3_constants_key(slug)
        localdata, success, errors = fs.get(slug)
        if success:
            s3data, success, errors = s3.get(key)
            localjson = json.loads(json.dumps(localdata))
            if localjson:
                is_json = True
                constants[slug]['formatted'] = True
            else:
                is_json = False
                constants[slug]['formatted'] = False
        else:
            s3data = None
        if localdata != s3data and is_json:
            payload, success, errors = s3.put(key, localdata)
            constants[slug]['unchanged'] = False
            if success:
                constants[slug]['uploaded'] = True
        elif localdata == s3data:
            constants[slug]['unchanged'] = True     
                   
    return {'constants':[constants[constant] for constant in constants]}, True, []