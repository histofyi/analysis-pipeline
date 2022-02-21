from typing import Dict, List, Tuple
from common.providers import s3Provider, httpProvider, awsKeyProvider


def download_pdb_file(pdb_code:str) -> str:
    """
    This function downloads the PDB file specified

    Args:
        pdb_code (str): the code of the PDB file to be downloaded

    Returns:
        str : the PDB file

    """
    url = f'https://files.rcsb.org/download/{pdb_code}.pdb'
    pdb_data = httpProvider().get(url, 'txt')
    return pdb_data



def get_pdb_structure(pdb_code:str, aws_config: Dict, force:bool=False) -> Tuple[str, bool, List]:
    """
    This function retrieves a PDB file from S3. If the file is not already in S3 it will retrieve it from the RCSB and persist it to S3

    Args:
        pdb_code (str): the code of the PDB file
        aws_config (Dict): the AWS configuration for the environment
        force (bool): not currently used, may be implemented to force a re-download in the case of a revised structure
    """
    key = awsKeyProvider().structure_key(pdb_code, 'raw')
    s3 = s3Provider(aws_config)
    pdb_data, success, errors = s3.get(key, data_format='pdb')
    if not success:
        pdb_data = download_pdb_file(pdb_code)
        if pdb_data:
            s3.put(key, pdb_data, data_format='pdb')
        return pdb_data, True, None
    else:
        return pdb_data.decode('utf-8'), True, None
