from common.providers import s3Provider, awsKeyProvider, PDBeProvider
from common.helpers import update_block
from common.functions import slugify

from common.models import itemSet

import logging


def fetch_publication_info(pdb_code, aws_config, force=False):
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
        update['associated_structures'] = publication_info['associated_entries']
        if update['doi'] is not None:
            if update['associated_structures'] is not None:
                members = [member.strip() for member in update['associated_structures'].split(',')]
                members.append(pdb_code)
                members = sorted(members)
            else:
                members = [pdb_code]
            logging.warn(slugify(update['doi']))
            itemset, success, errors = itemSet(slugify(update['doi'])).create_or_update('doi:'+ update['doi'], 'Structures in '+ update['publication']['citation']['title'], members, 'publication')
        data, success, errors = update_block(pdb_code, 'core', 'info', update, aws_config)
    return {'publication':publication_info, 'source':'PDBe REST API publication method'}, True, []
