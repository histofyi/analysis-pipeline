from typing import List, Dict, Tuple, Union
from common.providers import s3Provider, awsKeyProvider, PDBeProvider
from common.models import itemSet

from common.helpers import fetch_constants, fetch_core, update_block, slugify, levenshtein_ratio_and_distance

from common.models import itemSet


from rich import print
from rich.panel import Panel
from rich.console import Console

console = Console()



import logging

from structure_pipeline.pipeline_actions.match_chains import match_chains


alpha_chains = ['class_i_alpha', 'mr1', 'cd1a', 'cd1b', 'cd1d', 'fcrn', 'mica', 'micb', 'hfe2', 'h2-t22','zag']


def process_molecule_search_terms(molecule:str) -> List:
    return [term.lower() for term in molecule.replace('-',' ').split(' ')]


def assign_chain(chain_length, chain_sequence, molecule_search_terms=None):
    max_match_count = 0
    best_match = 'unmatched'
    best_match_score = 0
    possible_matches = []
    chains = fetch_constants('chains')
    if len(chain_sequence) < 20:
        return {'score':1, 'match':'peptide'}
    else:
        with console.status(f"Matching for...{molecule_search_terms}"):
            for chain in chains:
                if 'sequences' in chains[chain]:
                    if chains[chain]['sequences']:
                        for test in chains[chain]['sequences']:
                            length_difference = abs(len(test) - len(chain_sequence))
                            if length_difference < 50:
                                ratio, distance = levenshtein_ratio_and_distance(test.lower(), chain_sequence.lower())
                                if ratio > best_match_score:
                                    best_match_score = ratio
                                    best_match = chain
        return {'score':best_match_score, 'match':best_match}


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
        print(organism_scientific)
    return organism_update


def create_or_update_organism_set(organism, mhc_alpha_chain, pdb_code):
    species = organism['common_name']
    class_name = None
    #TODO these sorts of labels should be centrally done somehow
    if mhc_alpha_chain['match'] == 'class_i_alpha':
        class_name = 'Class I'
    elif mhc_alpha_chain['match'] == 'class_ii_alpha':
        class_name = 'Class II'
    else:
        for chain in alpha_chains:
            if mhc_alpha_chain['match'] == chain:
                class_name = chain.upper()
    if class_name:
        set_title = f'{species.capitalize()} {class_name}'
        set_slug = slugify(set_title)
        set_description = f'{set_title} structures. Automatically assigned'
        context = 'species'
        itemset, success, errors = itemSet(set_slug, context).create_or_update(set_title, set_description, [pdb_code], context)
        return itemset, success, errors
    else:
        return {}, False, ['no_class_name']




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
                best_match = assign_chain(chain_length, chain['sequence'], molecule_search_terms=molecule_search_terms)
                action[chain_id]['best_match'] = best_match
                action[chain_id]['sequences'] = [chain['sequence']]
                found_chains.append(best_match)
                if best_match['match'] in alpha_chains:
                    species_overrides = fetch_constants('species_overrides')
                    if pdb_code in species_overrides:
                        organism_scientific = species_overrides[pdb_code]['organism_scientific_name']
                    else:
                        organism_scientific = chain['source'][0]['organism_scientific_name']
                    organism = organism_update(organism_scientific)
                    if organism:
                        update['organism'] = organism
                        itemset, success, errors = create_or_update_organism_set(organism, best_match, pdb_code)
                    else:
                        missing_organism = chain['source'][0]['organism_scientific_name']
                        step_errors.append(f'missing_organism__{slugify(missing_organism)}')
                        print(Panel(f'Unable to match organism : {missing_organism}', style="red"))
                    
                if best_match['match'] == 'peptide':
                    update['peptide']['sequence'] = chain['sequence']
    if 'unmatched' in found_chains:
        step_errors.append('unmatched_chain')
    print (action)
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
