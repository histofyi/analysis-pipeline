from typing import Dict, List, Tuple

import Bio.PDB

from common.providers import s3Provider, awsKeyProvider
from common.helpers import update_block, fetch_core, load_cif
import logging

peptide_contact_positions = [5,7,9,24,25,33,34,45,59,62,63,64,65,66,67,68,69,70,72,73,74,75,76,77,78,80,81,84,95,97,99,114,116,123,124,133,139,140,142,143,144,146,147,152,155,156,157,158,159,160,163,164,167,168,171]


def cleft_torsion_angles(structure, chain_id, peptide_contacts=True):
    structure.atom_to_internal_coordinates()
    peptide_contact_angles = {}
    all_cleft_angles = {}
    for model in structure:
        for chain in model:
            if chain.get_id() == chain_id:
                for residue in chain:
                    if residue.internal_coord is not None:
                        i = residue.get_id()[1]
                        if i < 180:
                            angle_info = {}
                            angle_info['residue'] = residue.resname
                            angle_info['phi'] = residue.internal_coord.get_angle('phi')
                            angle_info['psi'] = residue.internal_coord.get_angle('psi')
                            angle_info['omg'] = residue.internal_coord.get_angle('omg')
                            angle_info['cb:ca:c'] = residue.internal_coord.get_angle('CB:CA:C')
                            angle_info['chi1'] = residue.internal_coord.get_angle('chi1')
                            angle_info['chi2'] = residue.internal_coord.get_angle('chi2')
                            angle_info['chi3'] = residue.internal_coord.get_angle('chi3')
                            angle_info['chi4'] = residue.internal_coord.get_angle('chi4')
                            if residue.get_id()[1] in peptide_contact_positions:
                                peptide_contact_angles[i] = angle_info
                            all_cleft_angles[i] = angle_info
    return peptide_contact_angles, all_cleft_angles



def measure_cleft_angles(pdb_code:str, aws_config:Dict, force:bool=False) -> Dict:
    step_errors = []
    core, success, errors = fetch_core(pdb_code, aws_config)
    s3 = s3Provider(aws_config)
    aligned_key = awsKeyProvider().block_key(pdb_code, 'aligned', 'info')
    aligned, success, errors = s3.get(aligned_key)
    action = {'peptide_contact_position_angles':{},'cleft_torsion_angles':{}}
    chains_key = awsKeyProvider().block_key(pdb_code, 'chains', 'info')
    chains, success, errors = s3.get(chains_key)
    chain_ids = None
    for chain in chains:
        if chains[chain]['best_match']['match'] == 'class_i_alpha':
            chain_ids = chains[chain]['chains']
    i = 0
    if aligned is not None:
        for assembly_id in aligned['aligned']['files']:
            action['peptide_contact_position_angles'][assembly_id] = {}
            action['cleft_torsion_angles'][assembly_id] = {}
            assembly_identifier = f'{pdb_code}_{assembly_id}'
            if aligned['aligned']['files'][assembly_id] is not None:
                cif_key = aligned['aligned']['files'][assembly_id]['files']['file_key']
                structure = load_cif(cif_key, assembly_identifier, aws_config)
                peptide_contact_angles, all_cleft_angles = cleft_torsion_angles(structure, chain_ids[i])
                action['peptide_contact_position_angles'][assembly_id] = peptide_contact_angles
                action['cleft_torsion_angles'][assembly_id] = all_cleft_angles
            else:
                step_errors.append('missing_aligned_structure')
            i += 1
        
        peptide_contact_position_angles_key = awsKeyProvider().block_key(pdb_code, 'peptide_contact_position_angles', 'info')
        data, success, errors = s3.put(peptide_contact_position_angles_key, {'peptide_contact_position_angles': action['peptide_contact_position_angles']}, data_format='json')
        cleft_torsion_angles_key = awsKeyProvider().block_key(pdb_code, 'cleft_torsion_angles', 'info')
        data, success, errors = s3.put(cleft_torsion_angles_key, {'cleft_torsion_angles': action['cleft_torsion_angles']}, data_format='json')
    else:
        logging.warn(pdb_code)
        logging.warn('NO ALIGNED STRUCTURES')
        step_errors.append('no_aligned_structures')
    output = {
        'action':action,
        'core':core
    }
    return output, success, step_errors