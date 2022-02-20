from common.providers import s3Provider, awsKeyProvider

import logging

def test(pdb_code, aws_config):
    logging.warn(pdb_code)
    return {'pdb_code':pdb_code}, True, None