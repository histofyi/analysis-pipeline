from common.providers import s3Provider, awsKeyProvider, PDBeProvider
from common.helpers import pdb_loader, update_block, three_letter_to_one, fetch_constants

from common.helpers import fetch_constants, fetch_core, update_block, slugify

import logging



def assign_chain(chain_length, molecule, molecule_search_terms=None):
    if not molecule_search_terms:
        molecule_search_terms = molecule.replace('-',' ').split(' ')
    
    max_match_count = 0
    best_match = 'unmatched'
    chains = fetch_constants('chains')
    for chain in chains:
        if chain_length < 20:
            best_match = 'peptide'
        else:
            matches = [item for item in molecule_search_terms if item in chains[chain]['features']]
            if chain_length > chains[chain]['length'] + chains[chain]['range'][0] and chain_length < chains[chain]['length'] + chains[chain]['range'][1]:
                in_range = True
            else:
                in_range = False
            match_count = len(matches)
            if in_range:
                match_count += 1
            if match_count > max_match_count and in_range:
                max_match_count = match_count
                best_match = chains[chain]['label']
    return best_match


def organism_update(organism_scientific):
    species = fetch_constants('species')
    organism_slug = slugify(organism_scientific)
    if organism_slug in species:
        organism_update = {
            'scientific_name':species[organism_slug]['scientific_name'],
            'common_name':species[organism_slug]['common_name']
        }
    else:
        organism_update = {'scientific_name':organism_scientific}
    return organism_update


def assign_chains(pdb_code, aws_config, force=False):
    set_errors = []
    core, success, errors = fetch_core(pdb_code, aws_config)
    action = {}
    update = {'peptide':core['peptide']}
    molecules_info, success, errors = PDBeProvider(pdb_code).fetch_molecules()
    for chain in molecules_info:
        if 'molecule' not in chain:
            if 'length' in chain:
                chain_id = chain['entity_id']
                action[chain_id] = {
                    'molecule':chain['molecule_name'][0].lower(),
                    'chains':chain['in_chains'],
                    'length':chain['length'],
                    'gene_name':chain['gene_name'],
                    'start':[source['mappings'][0]['start']['residue_number'] for source in chain['source']],
                    'end':[source['mappings'][0]['end']['residue_number'] for source in chain['source']]
                }

                chain_length = chain['length']
                molecule_search_terms = chain['molecule_name'][0].lower().split(' ')
                if 'gene_name' in chain:
                    if chain['gene_name'] is not None:
                        for item in chain['gene_name']:
                            molecule_search_terms.append(item)
                best_match = assign_chain(chain_length, None, molecule_search_terms=molecule_search_terms)
                action[chain_id]['best_match'] = best_match
                action[chain_id]['sequences'] = [chain['sequence']]
                if best_match in ['class_i_alpha', 'class_ii_alpha']:
                    organism_update(chain['source'][0]['organism_scientific_name'])
                    update['organism'] = organism_update(chain['source'][0]['organism_scientific_name'])
                if best_match == 'peptide':
                    update['peptide']['sequence'] = chain['sequence']
    s3 = s3Provider(aws_config)
    chains_key = awsKeyProvider().block_key(pdb_code, 'chains', 'info')
    s3.put(chains_key, action)
    data, success, errors = update_block(pdb_code, 'core', 'info', update, aws_config)
    output = {
        'action':action,
        'core':data
    }
    return output, True, set_errors
