from typing import Dict, List, Tuple
from flask import current_app

import json
import time
    

from common.providers import s3Provider, awsKeyProvider, algoliaProvider
from common.helpers import update_block, fetch_core

from common.models import itemSet


def index_to_algolia(set_context:str, set_slug:str, aws_config:Dict, force:bool=False) -> Dict:
    """
    This function pushes the core record to Algolia
    # TODO push more records to different indices

    Args:
        pdb_code (str): the code of the PDB file
        aws_config (Dict): the AWS configuration for the environment
        force (bool): not currently used, may be implemented to force a re-download in the case of a revised structure
    """
    step_errors = []
    
    set_key = ''
    algolia = algoliaProvider(current_app.config['ALGOLIA_APPLICATION_ID'], current_app.config['ALGOLIA_KEY'])
    itemset = {}
    data, success, errors = algolia.index_item(set_key, 'sets', itemset)
    time.sleep(5)
    data, success, errors = algolia.search('sets', [set_key], 1)

    if success:
        action = data
    else:
        action = {'indexing_status':'unsuccessful'}
    output = {
            'action':action,
            'set':itemset
    }
    return output, success, step_errors
