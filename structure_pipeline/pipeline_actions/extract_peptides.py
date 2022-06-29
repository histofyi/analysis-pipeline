from typing import Dict, List, Tuple

import Bio.PDB
from Bio.PDB.mmcifio import MMCIFIO
from io import StringIO, TextIOWrapper
import datetime


from common.providers import s3Provider, awsKeyProvider, PDBeProvider
from common.helpers import load_pdb, update_block, fetch_core, fetch_facet, load_cif, save_cif, SelectChains, NonHetSelect
import logging


def extract_peptides(pdb_code:str, aws_config:Dict, force:bool=False) -> Dict:
    step_errors = []
    core, success, errors = fetch_core(pdb_code, aws_config)
    s3 = s3Provider(aws_config)
    aligned, success, errors = fetch_facet(pdb_code, 'aligned', aws_config)
    chains, success, errors = fetch_facet(pdb_code, 'chains', aws_config)
    chain_ids = None
    for chain in chains:
        if chains[chain]['best_match']['match'] == 'peptide':
            chain_ids = chains[chain]['chains']
    action = {'peptide_structures':{'files':{}}}
    i = 0
    if chain_ids is None:
        step_errors.append("no_peptide_chain_ids")
    else:
        if aligned:
            print (aligned)
            for assembly_id in aligned:
                assembly_identifier = f'{pdb_code}_{assembly_id}'
                action['peptide_structures'][assembly_id] = {'peptide_only':{'files':{}}, 'peptide_and_hetatoms':{'files':{}}}
                if aligned[assembly_id] ['files'] is not None:
                    pdb_file_key = aligned[assembly_id]['files']['pdb_file_key']
                    print (pdb_file_key)
                    structure = load_pdb(pdb_file_key, assembly_identifier, aws_config)
                    try:
                        chain_id = chain_ids[i]
                    except:
                        chain_id = None
                        print (i)
                    if chain_id:
                        for model in structure:
                            for chain in model:
                                if chain.get_id() == chain_id:
                                    peptide_and_hetatoms_cif_file = StringIO()
                                    io = MMCIFIO()
                                    io.set_structure(structure)
                                    io.save(peptide_and_hetatoms_cif_file, SelectChains(chain_id))
                                    cif_key = awsKeyProvider().cif_file_key(assembly_identifier, 'peptide_and_hetatoms')
                                    cif_data = save_cif(cif_key, peptide_and_hetatoms_cif_file, aws_config)
                                    action['peptide_structures'][assembly_id]['peptide_and_hetatoms']['files'] = {'file_key':cif_key, 'last_updated':datetime.datetime.now().isoformat()}
                                    peptide_structure = load_cif(cif_key, assembly_identifier, aws_config)
                                    io.set_structure(peptide_structure)
                                    peptide_cif_file = StringIO()
                                    io.save(peptide_cif_file, NonHetSelect())
                                    cif_key = awsKeyProvider().cif_file_key(assembly_identifier, 'peptide')
                                    cif_data = save_cif(cif_key, peptide_cif_file, aws_config)
                                    action['peptide_structures'][assembly_id]['peptide_only']['files'] = {'file_key':cif_key, 'last_updated':datetime.datetime.now().isoformat()}
                    else:
                        step_errors.append('missing_chain_id_' + str(i))
                else:
                    step_errors.append('missing_aligned_structure')
                i += 1
            peptide_structures_key = awsKeyProvider().block_key(pdb_code, 'peptide_structures', 'info')
            data, success, errors = s3.put(peptide_structures_key, action['peptide_structures'], data_format='json')
        else:
            logging.warn(pdb_code)
            logging.warn('NO ALIGNED STRUCTURES')
            step_errors.append('no_aligned_structures')
    output = {
        'action':action,
        'core':core
    }
    return output, success, step_errors
