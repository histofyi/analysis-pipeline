from typing import Dict, List, Tuple

from common.providers import s3Provider, httpProvider, awsKeyProvider
from common.helpers import update_block


def download_rcsb_info(pdb_code:str) -> Dict:
    """
    This function downloads the RSCB data for the pdb code specified specified

    Args:
        pdb_code (str): the code of the PDB data from RCSB to be cached

    Returns:
        str : the RCSB json data

    """
    url = f'https://data.rcsb.org/rest/v1/core/entry/{pdb_code}'
    pdb_info = httpProvider().get(url, 'json')
    return pdb_info



def fetch_rcsb_info(pdb_code:str, aws_config: Dict, force=False) -> Tuple[Dict, bool, List]:
    """
    This function downloads the RSCB data for the pdb code specified specified

    Args:
        pdb_code (str): the code of the PDB data from RCSB to be cached

    Returns:
        str : the RCSB json data

    """
    key = awsKeyProvider().block_key(pdb_code, 'rcsb', 'info')
    s3 = s3Provider(aws_config)
    data, success, errors =  s3.get(key)
    if not success or force is True:
        payload = download_rcsb_info(pdb_code)
        step_errors = []
        s3.put(key, payload)
        update = {}
        try:
            update['publication'] = payload['rcsb_primary_citation']
        except:
            step_errors.append('unable_to_assign_publication')
        try: 
            update['title'] = payload['struct']['pdbx_descriptor']
        except:
            step_errors.append('unable_to_assign_title')
        data, success, errors = update_block(pdb_code, 'core', 'info', update, aws_config)
    return data, success, errors