from typing import Dict, List, Tuple

import Bio.PDB

from common.providers import s3Provider, awsKeyProvider
from common.helpers import update_block, fetch_core, load_cif
import logging



def peptide_angles(structure):
    structure.atom_to_internal_coordinates()
    angle_info = {}
    i = 1
    for residue in structure.get_residues():
        angle_info[i] = {}
        if residue.internal_coord:
            angle_info[i]['position'] = i
            angle_info[i]['residue'] = residue.resname
            angle_info[i]['phi'] = residue.internal_coord.get_angle('phi')
            angle_info[i]['psi'] = residue.internal_coord.get_angle('psi')
            angle_info[i]['omg'] = residue.internal_coord.get_angle('omg')
            angle_info[i]['chi1'] = residue.internal_coord.get_angle('chi1')
            angle_info[i]['chi2'] = residue.internal_coord.get_angle('chi2')
            angle_info[i]['chi3'] = residue.internal_coord.get_angle('chi3')
            angle_info[i]['chi4'] = residue.internal_coord.get_angle('chi4')
            angle_info[i]['cb:ca:c'] = residue.internal_coord.get_angle('CB:CA:C')
            i += 1
    return angle_info



def measure_peptide_angles(pdb_code:str, aws_config:Dict, force:bool=False) -> Dict:
    step_errors = []
    core, success, errors = fetch_core(pdb_code, aws_config)
    s3 = s3Provider(aws_config)
    peptide_structures_key = awsKeyProvider().block_key(pdb_code, 'peptide_structures', 'info')
    peptide_structures, success, errors = s3.get(peptide_structures_key)
    action = {'peptide_angles':{}}
    if peptide_structures is not None:
        for assembly_id in peptide_structures['peptide_structures']['files']:
            assembly_identifier = f'{pdb_code}_{assembly_id}'
            peptide_cif_key = peptide_structures['peptide_structures']['files'][assembly_id]['peptide_only']['file_key']
            structure = load_cif(peptide_cif_key, assembly_identifier, aws_config)
            action['peptide_angles'][assembly_id] = peptide_angles(structure)
        peptide_angles_key = awsKeyProvider().block_key(pdb_code, 'peptide_angles', 'info')
        data, success, errors = s3.put(peptide_angles_key, action, data_format='json')
    else:
        logging.warn(pdb_code)
        logging.warn('NO PEPTIDE STRUCTURES')
        step_errors.append('no_peptide_structures')

    output = {
        'action':action,
        'core':core
    }
    return output, success, step_errors