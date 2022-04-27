from typing import Dict, List, Tuple

import Bio.PDB
from Bio.PDB.mmcifio import MMCIFIO
from io import StringIO, TextIOWrapper
import datetime


from common.providers import s3Provider, awsKeyProvider, PDBeProvider
from common.helpers import update_block, fetch_core, load_cif, save_cif
import logging

# Don't start at 1 as many structures start at 2 or 3 due to disorder of the first few residues
start_id = 3
end_id   = 180

def align_structure(target, canonical, target_chain_id, assembly_identifier, mhc_class, aws_config):
    logging.warn('-----')
    logging.warn(assembly_identifier)
    logging.warn(target_chain_id)
    s3 = s3Provider(aws_config)
    residues_to_be_aligned = range(start_id, end_id + 1)
    
    i = 0
    for model in canonical:
        if i == 0:
            canonical_model = model
        i+=1

    canonical_atoms = []
    canonical_res_ids = []
    canonical_res_aa = []

    target_model = target[0]
    target_atoms = []
    target_res_ids = []
    target_res_aa = []

    # Iterate of all chains in the canonical model in order to find chain to match on
    for canonical_chain in canonical_model:
        if canonical_chain.id == 'A':
            # Iterate through the residues in the chosen chain
            for canonical_residues in canonical_chain:
                # Check if residue number ( .get_id() ) is in the list
                if canonical_residues.get_id()[1] in residues_to_be_aligned:
                    canonical_res_ids.append(canonical_residues.get_id()[1])
                    canonical_res_aa.append(canonical_residues.resname)
                    # Append CA atom to list
                    canonical_atoms.append(canonical_residues['CA'])


    # Do the same for the target structure
    for target_chain in target_model:
        if target_chain.id == target_chain_id:
            for target_residues in target_chain:
                if target_residues.get_id()[1] in residues_to_be_aligned:
                    target_res_ids.append(target_residues.get_id()[1])
                    target_res_aa.append(target_residues.resname)
                    target_atoms.append(target_residues['CA'])
    
    
    
    rmsd = None
    errors = None
    if len(canonical_atoms) == len(target_atoms):
        try:
            super_imposer = Bio.PDB.Superimposer()
            super_imposer.set_atoms(canonical_atoms, target_atoms)
            super_imposer.apply(target_model.get_atoms())
            rmsd = super_imposer.rms
            errors = None
        except Bio.PDB.PDBExceptions.PDBException as e:
            rmsd = False
            errors = str(e).replace(' ','_').lower()
    else:
        logging.warn('ATOMS')
        logging.warn(len(canonical_atoms))
        logging.warn(len(target_atoms))

    if rmsd:
        target_cif_file = StringIO()
        io = MMCIFIO()
        io.set_structure(target) 
        io.save(target_cif_file)
        target_cif_key = awsKeyProvider().cif_file_key(assembly_identifier, 'aligned')
        cif_data, success, errors = s3.put(target_cif_key, target_cif_file.getvalue().encode('utf-8'), data_format='txt')
        aligned = {
            'aligned_on': mhc_class,
            'aligned_chain': target_chain_id,
            'rmsd': rmsd,
            'start': start_id,
            'end': end_id,
            'files': {
                'file_key':target_cif_key,
                'last_updated': datetime.datetime.now().isoformat()
            }
        }
        errors = None
    else:
        aligned = None
    
    if rmsd:
        logging.warn(f'RMSD is {rmsd}')
    else:
        logging.warn(errors)
    logging.warn('-----')
    return aligned, errors


    




def align_structures(pdb_code:str, aws_config:Dict, force:bool=False) -> Dict:
    step_errors = []
    core, success, errors = fetch_core(pdb_code, aws_config)
    s3 = s3Provider(aws_config)
    chains_key = awsKeyProvider().block_key(pdb_code, 'chains', 'info')
    chains, success, errors = s3.get(chains_key)
    mhc_class = core['class']
    chain_ids = None
    if mhc_class in ['class_i','class_ii']:
        for chain in chains:
            if mhc_class in chains[chain]['best_match']:
                chain_ids = chains[chain]['chains']
    action = {'aligned':{'files':{}}}
    update = {}
    if chain_ids:
        for assembly_id in core['assemblies']['files']:
            canonical_key = 'structures/canonical/class_i.cif'
            cif_key = core['assemblies']['files'][assembly_id]['files']['file_key']
            assembly_identifier = f'{pdb_code}_{assembly_id}'
            structure = load_cif(cif_key, assembly_identifier, aws_config)
            canonical = load_cif(canonical_key, 'class_i', aws_config)
            if structure and canonical:
                chain_id = chain_ids[int(assembly_id) - 1]
                alignment, errors = align_structure(structure, canonical, chain_id, assembly_identifier, mhc_class, aws_config)
                if not errors:
                    action['aligned']['files'][assembly_id] = alignment
                else:
                    step_errors.append(errors)
        if len(step_errors) == 0:
            update['aligned'] = action['aligned']
            data, success, errors = update_block(pdb_code, 'core', 'info', update, aws_config)
            core = data
            aligned_key = awsKeyProvider().block_key(pdb_code, 'aligned', 'info')
            data, success, errors = s3.put(aligned_key, action, data_format='json')
    output = {
        'action':action,
        'core':core
    }
    return output, success, step_errors
