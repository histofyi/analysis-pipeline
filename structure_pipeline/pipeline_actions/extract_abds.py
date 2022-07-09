from typing import Dict, List, Tuple

import Bio.PDB
from Bio.PDB.mmcifio import MMCIFIO
from io import StringIO, TextIOWrapper
import datetime


from common.providers import s3Provider, awsKeyProvider, PDBeProvider
from common.helpers import load_pdb, update_block, fetch_core, fetch_facet, load_cif, save_cif, SelectChains, NonHetSelect, SelectResidues
import logging


def extract_abds(pdb_code:str, aws_config:Dict, force:bool=False) -> Dict:
    step_errors = []
    core, success, errors = fetch_core(pdb_code, aws_config)
    s3 = s3Provider(aws_config)
    aligned, success, errors = fetch_facet(pdb_code, 'aligned', aws_config)
    chains, success, errors = fetch_facet(pdb_code, 'chains', aws_config)
    chain_ids = None
    for chain in chains:
        if chains[chain]['best_match']['match'] == 'class_i_alpha':
            chain_ids = chains[chain]['chains']
    action = {'abd_structures':{'files':{}}}
    i = 0
    if chain_ids is None:
        step_errors.append("no_chain_ids")
    else:
        if aligned is not None:
            for assembly_id in aligned:
                assembly_identifier = f'{pdb_code}_{assembly_id}'
                action['abd_structures'][assembly_id] = {'alpha_and_hetatoms':{'files':{}},'alpha':{'files':{}},'abd':{'files':{}}}
                if aligned[assembly_id]['files'] is not None:
                    pdb_file_key = aligned[assembly_id]['files']['pdb_file_key']
                    print (pdb_file_key)
                    structure = load_pdb(pdb_file_key, assembly_identifier, aws_config)
                    chain_id = chain_ids[i]
                    for model in structure:
                        for chain in model:
                            if chain.get_id() == chain_id:
                                alpha_cif_file = StringIO()
                                io = MMCIFIO()
                                io.set_structure(structure)
                                io.save(alpha_cif_file, SelectChains(chain_id))
                                alpha_cif_key = awsKeyProvider().cif_file_key(assembly_identifier, 'alpha_and_hetatoms')
                                cif_data = save_cif(alpha_cif_key, alpha_cif_file, aws_config)
                                action['abd_structures'][assembly_id]['alpha_and_hetatoms']['files'] = {'file_key':alpha_cif_key, 'last_updated':datetime.datetime.now().isoformat()}
                                alpha_strucuture = load_cif(alpha_cif_key, assembly_identifier, aws_config)
                                io.set_structure(alpha_strucuture)
                                alpha_only_cif_file = StringIO()
                                io.save(alpha_only_cif_file, NonHetSelect())
                                alpha_only_cif_key = awsKeyProvider().cif_file_key(assembly_identifier, 'alpha')
                                cif_data = save_cif(alpha_only_cif_key, alpha_only_cif_file, aws_config)
                                action['abd_structures'][assembly_id]['alpha']['files'] = {'file_key':alpha_only_cif_key, 'last_updated':datetime.datetime.now().isoformat()}
                                alpha_only_strucuture = load_cif(alpha_only_cif_key, assembly_identifier, aws_config)
                                io.set_structure(alpha_only_strucuture)
                                abd_cif_file = StringIO()
                                io.save(abd_cif_file, SelectResidues(1,181))
                                abd_cif_key = awsKeyProvider().cif_file_key(assembly_identifier, 'abd')
                                cif_data = save_cif(abd_cif_key, abd_cif_file, aws_config)
                                action['abd_structures'][assembly_id]['abd']['files'] = {'file_key':abd_cif_key, 'last_updated':datetime.datetime.now().isoformat()}
                else:
                    step_errors.append('missing_aligned_structure')
            i += 1
            abd_structures_key = awsKeyProvider().block_key(pdb_code, 'abd_structures', 'info')
            data, success, errors = s3.put(abd_structures_key, action['abd_structures'], data_format='json')
        else:
            logging.warn(pdb_code)
            logging.warn('NO ALIGNED STRUCTURES')
            step_errors.append('no_aligned_structures')
    output = {
        'action':action,
        'core':core
    }
    return output, success, step_errors
