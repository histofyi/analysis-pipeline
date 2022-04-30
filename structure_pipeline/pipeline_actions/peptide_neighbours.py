from typing import Dict, List, Tuple

import Bio.PDB

from common.providers import s3Provider, awsKeyProvider
from common.helpers import update_block, fetch_core, load_cif
import logging



def peptide_neighbours(pdb_code:str, aws_config:Dict, force:bool=False) -> Tuple[Dict,bool,List]:
    logging.warn(pdb_code)
    step_errors = []
    core, success, errors = fetch_core(pdb_code, aws_config)
    s3 = s3Provider(aws_config)
    chains_key = awsKeyProvider().block_key(pdb_code, 'chains', 'info')
    chains, success, errors = s3.get(chains_key)
    mhc_class = core['class']
    peptide_neighbours = {}
    contacts = {}
    peptide_chains = []
    mhc_chains = []
    sorted_peptides = {}
    if mhc_class == 'class_i':
        for chain in chains:
            if chains[chain]['best_match'] == 'peptide':
                peptide_chains = chains[chain]['chains']
            elif chains[chain]['best_match'] == 'class_i_alpha':
                mhc_chains = chains[chain]['chains']
        if len(peptide_chains) > 0:
            chains_to_test = peptide_chains + mhc_chains
            for assembly_id in core['assemblies']['files']:
                peptide_neighbours[assembly_id] = {}
                cif_key = core['assemblies']['files'][assembly_id]['files']['file_key']
                assembly_identifier = f'{pdb_code}_{assembly_id}'
                structure = load_cif(cif_key, assembly_identifier, aws_config)
                if structure:
                    all_atoms = []
                    for chain in structure.get_chains():
                        if chain.get_id() in chains_to_test:
                            if chain.get_id() in peptide_chains:
                                class_i_peptide = chain.get_id()
                            else:
                                class_i_alpha = chain.get_id()
                            contacts[chain.get_id()] = {}
                            for residue in chain:
                                if residue.id[0] == ' ':
                                    for atom in residue:
                                        all_atoms.append(atom)
                    neighbor = Bio.PDB.NeighborSearch(all_atoms)
                    neighbours = neighbor.search_all(5, level='R')
                    for residue_pair in neighbours:
                        residue_1 = residue_pair[0]
                        residue_2 = residue_pair[1]
                        if residue_1.get_parent().id != residue_2.get_parent().id:
                            chain_pair = [residue_1.get_parent().id, residue_2.get_parent().id]
                            if class_i_peptide in chain_pair and class_i_alpha in chain_pair:
                                if residue_1.get_parent().id == class_i_alpha:
                                    class_i_details = {'residue':residue_1.resname, 'position':residue_1.get_id()[1]}
                                    peptide_details = {'residue':residue_2.resname, 'position':residue_2.get_id()[1]}
                                else:
                                    peptide_details = {'residue':residue_1.resname, 'position':residue_1.get_id()[1]}
                                    class_i_details = {'residue':residue_2.resname, 'position':residue_2.get_id()[1]}

                            #TODO offset the peptide and MHC residue ids if needed

                            class_i_residue_id = class_i_details['position']
                            peptide_residue_id = peptide_details['position']


                            if class_i_residue_id not in contacts[class_i_alpha]:
                                contacts[class_i_alpha][class_i_residue_id] = {'position':class_i_residue_id, 'residue':class_i_details['residue'], 'neighbours':[] }
                            contacts[class_i_alpha][class_i_residue_id]['neighbours'].append(peptide_details)

                            if peptide_residue_id not in contacts[class_i_peptide]:
                                contacts[class_i_peptide][peptide_residue_id] = {'position':peptide_residue_id, 'residue':peptide_details['residue'], 'neighbours':[] }
                            contacts[class_i_peptide][peptide_residue_id]['neighbours'].append(class_i_details)

                    sorted_peptide = dict(sorted(contacts[class_i_peptide].items()))
                sorted_peptides[assembly_id] = sorted_peptide
            peptide_key = awsKeyProvider().block_key(pdb_code, 'peptide_neighbours', 'info')
            s3.put(peptide_key, sorted_peptides)
        else:
            logging.warn('NO PEPTIDE')
            step_errors.append('no_peptide')
    else:
        logging.warn('NOT CLASS I')
        step_errors.append('not_class_i')
    # TODO Class II 
    action = {'peptide_neighbours':sorted_peptides}
    output = {
        'action':action,
        'core':core
    }
    return output, True, step_errors