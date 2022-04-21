from typing import Dict, List, Tuple

from common.providers import s3Provider, awsKeyProvider, PDBeProvider
from common.helpers import update_block, fetch_core
from common.functions import slugify

from common.models import itemSet

import logging


def fetch_publication_info(pdb_code:str, aws_config:Dict, force:bool=False) -> Dict:
    """
    This function retrieves a fetches the publication information from the PDBe REST API

    Args:
        pdb_code (str): the code of the PDB file
        aws_config (Dict): the AWS configuration for the environment
        force (bool): not currently used, may be implemented to force a re-download in the case of a revised structure
    """
    publication_info, success, errors = PDBeProvider(pdb_code).fetch_publications()
    if publication_info:
        update = {'publication':{'citation':{}}}
        update['publication']['citation']['authors'] = publication_info['author_list']
        update['doi'] = publication_info['doi']
        update['publication']['citation']['title'] = publication_info['title']
        update['publication']['pubmed_id'] = publication_info['pubmed_id']
        update['publication']['citation']['iso_abbreviation'] = publication_info['journal_info']['ISO_abbreviation']
        update['publication']['citation']['volume'] = publication_info['journal_info']['volume']
        update['publication']['citation']['issue'] = publication_info['journal_info']['issue']
        update['publication']['citation']['pages'] = publication_info['journal_info']['pages']
        update['publication']['citation']['year'] = publication_info['journal_info']['year']
        update['associated_structures'] = [member.strip() for member in publication_info['associated_entries'].split(',')]
        if update['doi'] is not None:
            if update['associated_structures'] is not None:
                members = update['associated_structures']
                members.append(pdb_code)
                members = sorted(members)
            else:
                members = [pdb_code]
            itemset, success, errors = itemSet(slugify(update['doi'])).create_or_update('doi:'+ update['doi'], 'Structures in '+ update['publication']['citation']['title'], members, 'publication')
        data, success, errors = update_block(pdb_code, 'core', 'info', update, aws_config)
    output = {
        'action': {'publication':publication_info, 'source':'PDBe REST API publication method'} ,
        'core': data
    }
    return output, True, []
