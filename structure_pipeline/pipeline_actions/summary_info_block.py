from common.providers import s3Provider, awsKeyProvider, PDBeProvider
from common.helpers import update_block, fetch_constants

import datetime

import logging

def parse_date_to_isoformat(datestring):
    try:
        date = datetime.date(int(datestring[0:4]), int(datestring[4:6]), int(datestring[6:8]))
        return date.isoformat()
    except:
        return datestring


def fetch_summary_info(pdb_code, aws_config, force=False):
    summary_info, success, errors = PDBeProvider(pdb_code).fetch_summary()
    if summary_info:
        for item in summary_info:
            if '_date' in item:
                summary_info[item] = parse_date_to_isoformat(summary_info[item])
        species_overrides = fetch_constants('species_overrides')
        update = {}
        update['release_date'] = summary_info['release_date']
        update['deposition_date'] = summary_info['deposition_date']
        if 'revision_date' in summary_info:
            update['revision_date'] = summary_info['revision_date']
        update['title'] = summary_info['title'].title()
        update['assembly_count'] = len(summary_info['assemblies'])
        update['unique_chain_count'] = summary_info['number_of_entities']['polypeptide']
        update['chain_count'] =  update['assembly_count'] * update['unique_chain_count']
        update['authors'] = summary_info['entry_authors']
        data, success, errors = update_block(pdb_code, 'core', 'info', update, aws_config)

    return {'summary':summary_info, 'source':'PDBe REST API summary method'}, True, []