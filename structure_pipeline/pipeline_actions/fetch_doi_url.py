from common.helpers import update_block, fetch_core

import logging

import doi


def fetch_doi_url(pdb_code, aws_config, force=False):
    core, success, errors = fetch_core(pdb_code, aws_config)
    step_errors = []
    core, success, errors = fetch_core(pdb_code, aws_config)
    action = {}
    update = {}
    try:
        url = doi.get_real_url_from_doi(core['doi'])
        update['resolved_doi_url'] = url
    except:
        url = None
        update = None
        step_errors.append('unable_to_fetch_doi_url')
    action['resolved_doi_url'] = url
    if update:
        data, success, errors = update_block(pdb_code, 'core', 'info', update, aws_config)
    else:
        data = core
    output = {
        'action':action,
        'core':data
    }
    return output, True, step_errors