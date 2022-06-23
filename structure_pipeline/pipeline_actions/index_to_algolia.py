from typing import Dict, List, Tuple
from flask import current_app

import json
import time
    

from common.providers import s3Provider, awsKeyProvider, algoliaProvider
from common.helpers import update_block, fetch_core

from common.models import itemSet


def index_to_algolia(pdb_code:str, aws_config:Dict, force:bool=False) -> Dict:
    """
    This function pushes the core record to Algolia
    # TODO push more records to different indices

    Args:
        pdb_code (str): the code of the PDB file
        aws_config (Dict): the AWS configuration for the environment
        force (bool): not currently used, may be implemented to force a re-download in the case of a revised structure
    """
    step_errors = []
    core, success, errors = fetch_core(pdb_code, aws_config)

    algolia = algoliaProvider(current_app.config['ALGOLIA_APPLICATION_ID'], current_app.config['ALGOLIA_KEY'])
    data, success, errors = algolia.index_item(pdb_code, 'core', core)
    time.sleep(5)
    data, success, errors = algolia.search('core', [pdb_code])

    if success:
        action = data
    else:
        action = {'indexing_status':'unsuccessful'}
    output = {
            'action':action,
            'core':core
     }
    return output, success, step_errors
