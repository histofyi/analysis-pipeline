from typing import Dict, List, Tuple

import Bio.PDB
from Bio.PDB.mmcifio import MMCIFIO
from io import StringIO, TextIOWrapper
import datetime


from common.providers import s3Provider, awsKeyProvider, PDBeProvider
from common.helpers import update_block, fetch_core, load_cif, save_cif, SelectChains, NonHetSelect
import logging


def extract_peptides(pdb_code:str, aws_config:Dict, force:bool=False) -> Dict:
    step_errors = []
    core, success, errors = fetch_core(pdb_code, aws_config)
    s3 = s3Provider(aws_config)
    aligned_key = awsKeyProvider().block_key(pdb_code, 'aligned', 'info')
    aligned, success, errors = s3.get(aligned_key)
    chains_key = awsKeyProvider().block_key(pdb_code, 'chains', 'info')
    chains, success, errors = s3.get(chains_key)
    chain_ids = None
    for chain in chains:
        if chains[chain]['best_match'] == 'peptide':
            chain_ids = chains[chain]['chains']
    action = {'peptide_structures':{'files':{}}}
    i = 0
    if aligned is not None:
        for assembly_id in aligned['aligned']['files']:
            assembly_identifier = f'{pdb_code}_{assembly_id}'
            action['peptide_structures']['files'][assembly_id] = {}
            cif_key = aligned['aligned']['files'][assembly_id]['files']['file_key']
            structure = load_cif(cif_key, assembly_identifier, aws_config)
            chain_id = chain_ids[i]
            for model in structure:
                for chain in model:
                    if chain.get_id() == chain_id:
                        peptide_and_hetatoms_cif_file = StringIO()
                        io = MMCIFIO()
                        io.set_structure(structure)
                        io.save(peptide_and_hetatoms_cif_file, SelectChains(chain_id))
                        cif_key = awsKeyProvider().cif_file_key(assembly_identifier, 'peptide_and_hetatoms')
                        cif_data = save_cif(cif_key, peptide_and_hetatoms_cif_file, aws_config)
                        action['peptide_structures']['files'][assembly_id]['peptide_and_hetatoms'] = {'file_key':cif_key, 'last_updated':datetime.datetime.now().isoformat()}
                        peptide_structure = load_cif(cif_key, assembly_identifier, aws_config)
                        io.set_structure(peptide_structure)
                        peptide_cif_file = StringIO()
                        io.save(peptide_cif_file, NonHetSelect())
                        cif_key = awsKeyProvider().cif_file_key(assembly_identifier, 'peptide')
                        cif_data = save_cif(cif_key, peptide_cif_file, aws_config)
                        action['peptide_structures']['files'][assembly_id]['peptide_only'] = {'file_key':cif_key, 'last_updated':datetime.datetime.now().isoformat()}
            i += 1
        peptide_structures_key = awsKeyProvider().block_key(pdb_code, 'peptide_structures', 'info')
        data, success, errors = s3.put(peptide_structures_key, action, data_format='json')
    else:
        logging.warn(pdb_code)
        logging.warn('NO ALIGNED STRUCTURES')
        step_errors.append('no_aligned_structures')
    output = {
        'action':action,
        'core':core
    }
    return output, success, step_errors
