from common.providers import s3Provider, awsKeyProvider
from common.helpers import pdb_loader, update_block, fetch_constants


def parse_pdb_header(pdb_code, aws_config, force=False):
    """
    This function loads the PDB file from S3 and parses any useful information from it such as chain assignments by the authors, species assignment and missing residues

    Args:
        pdb_code (str): the code of the PDB file
        aws_config (Dict): the AWS configuration for the environment
        force (bool): not currently used, may be implemented to force a new parse in the case of a revised structure
    """
    filepath = awsKeyProvider().structure_key(pdb_code, 'raw')
    s3 = s3Provider(aws_config)
    pdb_data, success, errors = s3.get(filepath, data_format='pdb')
    step_errors = []
    if success:
        structure = pdb_loader(pdb_data)
        if structure:
            key = awsKeyProvider().block_key(pdb_code, 'pdb', 'info')
            s3 = s3Provider(aws_config)
            payload = structure.header
            s3.put(key, payload)
            update = {}
            species_overrides = fetch_constants('species_overrides')
            try:
                if pdb_code in species_overrides:
                    update['organism_scientific'] = species_overrides[pdb_code]['organism_scientific']
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
