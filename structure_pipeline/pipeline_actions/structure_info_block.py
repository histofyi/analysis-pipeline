from .s3 import s3Provider
from .common import build_s3_structure_key, build_s3_block_key, pdb_loader, update_block
import logging
from .constants import SPECIES_OVERRIDES

def parse_pdb_header(pdb_code, aws_config):
    filepath = build_s3_structure_key(pdb_code, 'raw')
    s3 = s3Provider(aws_config)
    pdb_data, success, errors = s3.get(filepath, data_format='pdb')
    step_errors = []
    if success:
        structure = pdb_loader(pdb_data)
        if structure:
            key = build_s3_block_key(pdb_code, 'pdb', 'info')
            s3 = s3Provider(aws_config)
            payload = structure.header
            s3.put(key, payload)
            update = {}
            try:
                if pdb_code in SPECIES_OVERRIDES:
                    update['organism_common'] = SPECIES_OVERRIDES[pdb_code]['organism_common']
                else:
                    update['organism_common'] = payload['source']['1']['organism_common']
            except:
                step_errors.append('unable_to_parse_organism_common')
            try:
                if pdb_code in SPECIES_OVERRIDES:
                    update['organism_scientific'] = SPECIES_OVERRIDES[pdb_code]['organism_scientific']
                else:
                    update['organism_scientific'] = payload['source']['1']['organism_scientific']
            except:
                step_errors.append('unable_to_parse_organism_common')
            try:
                update['missing_residues'] = payload['missing_residues']
            except:
                step_errors.append('unable_to_assign_missing_residues')
            try:
                update['components'] = payload['compound']
            except:
                step_errors.append('unable_to_assign_compound')
            data, success, errors = update_block(pdb_code, 'core', 'info', update, aws_config)
            return payload, True, step_errors
        else:
            return None, False, ['unable_to_parse_structure']
    else:
        return None, False, ['unable_to_load_structure']
