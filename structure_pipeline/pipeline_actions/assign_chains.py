from typing import List, Dict, Tuple, Union
from common.providers import s3Provider, awsKeyProvider, PDBeProvider
from common.models import itemSet

from common.helpers import fetch_constants, fetch_core, update_block, slugify

from common.models import itemSet


from rich import print
from rich.panel import Panel

import logging

from structure_pipeline.pipeline_actions.match_chains import match_chains



def process_molecule_search_terms(molecule:str) -> List:
    return [term.lower() for term in molecule.replace('-',' ').split(' ')]


def assign_chain(chain_length, molecule, molecule_search_terms=None):
    logging.warn(molecule_search_terms)
    if not molecule_search_terms:
        molecule_search_terms = process_molecule_search_terms(molecule)
    max_match_count = 0
    best_match = 'unmatched'
    possible_matches = []
    chains = fetch_constants('chains')
    for chain in chains:
        if chain_length < 20:
            best_match = 'peptide'
        else:
            matches = [item for item in molecule_search_terms if item in chains[chain]['features']]
            lower = chains[chain]['length'] + chains[chain]['range'][0]
            upper = chains[chain]['length'] + chains[chain]['range'][1]
            if chain_length > lower and chain_length < upper:
                in_range = True
            else:
                in_range = False
            match_count = len(matches)
            if in_range:
                match_count += 1
            #TODO test why in_range was required, function works better without it on test set
            #if match_count > max_match_count and in_range:
            #TODO remove comment if not needed
            if match_count > max_match_count:
                max_match_count = match_count
                best_match = chains[chain]['label']
            else:
                if matches and match_count > 1:
                    possible_matches.append({'match_count':match_count, 'in_range':in_range, 'matches':matches ,'chain_type': chains[chain]['label'], 'search_terms':molecule_search_terms, 'chain_length':chain_length, 'lower':lower, 'upper':upper })
    if best_match == 'unmatched':
        logging.warn(molecule_search_terms)
        logging.warn(possible_matches)
    if best_match == 'unmatched' and len(possible_matches) > 1:
        logging.warn(possible_matches)
    else:
        logging.warn(best_match)
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
        organism_update = None
    return organism_update


def create_or_update_organism_set(organism, mhc_alpha_chain, pdb_code):
    species = organism['common_name']
    class_name = None
    #TODO these sorts of labels should be centrally done somehow
    if mhc_alpha_chain == 'class_i_alpha':
        class_name = 'Class I'
    else:
        class_name = 'Class II'
    set_title = f'{species.capitalize()} {class_name}'
    set_slug = slugify(set_title)
    set_description = f'{set_title} structures. Automatically assigned'
    context = 'species'
    logging.warn(pdb_code)
    itemset, success, errors = itemSet(set_slug, context).create_or_update(set_title, set_description, [pdb_code], context)
    return itemset, success, errors




def assign_chains(pdb_code, aws_config, force=False):
    print('--------------------')
    print(' ')
    logging.warn(pdb_code)
    step_errors = []
    core, success, errors = fetch_core(pdb_code, aws_config)
    action = {}
    update = {'peptide':core['peptide']}
    molecules_info, success, errors = PDBeProvider(pdb_code).fetch_molecules()
    found_chains = []
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
                molecule_search_terms = process_molecule_search_terms(chain['molecule_name'][0])
                if 'gene_name' in chain:
                    if chain['gene_name'] is not None:
                        for item in chain['gene_name']:
                            molecule_search_terms.append(item.lower())
                best_match = assign_chain(chain_length, None, molecule_search_terms=molecule_search_terms)
                action[chain_id]['best_match'] = best_match
                action[chain_id]['sequences'] = [chain['sequence']]
                found_chains.append(best_match)
                if best_match in ['class_i_alpha', 'class_ii_alpha']:
                    organism = organism_update(chain['source'][0]['organism_scientific_name'])
                    if organism:
                        update['organism'] = organism
                        print(organism)
                        itemset, success, errors = create_or_update_organism_set(organism, best_match, pdb_code)
                    else:
                        missing_organism = chain['source'][0]['organism_scientific_name']
                        print(Panel(f'Unable to match organism : {missing_organism}', style="red"))
                    
                if best_match == 'peptide':
                    update['peptide']['sequence'] = chain['sequence']
    if 'unmatched' in found_chains:
        step_errors.append('unmatched_chain')
    s3 = s3Provider(aws_config)
    chains_key = awsKeyProvider().block_key(pdb_code, 'chains', 'info')
    s3.put(chains_key, action)
    data, success, errors = update_block(pdb_code, 'core', 'info', update, aws_config)
    print(' ')
    output = {
        'action':action,
        'core':data
    }
    return output, True, step_errors
