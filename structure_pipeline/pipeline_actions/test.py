from typing import Dict, Tuple, List, Optional, Union

from common.providers import s3Provider, awsKeyProvider

import logging

def test(pdb_code:str, aws_config: Dict, force: bool=False) -> Tuple[Dict, bool, Union[List, None]]:
    """
    This function does nothing really, it echoes back the pdb_code in a dictionary. It's role is to act as a small test function for the pipeline
    
    Args:
        pdb_code (str): the pdb code of a structure
        aws_config (Dict): the configuration details for AWS for the current app
        force (bool): whether the data in this step should be overwritten. 

    Returns:
        Dict: A dictionary of generated data (data)
        bool: A boolean of True or False (success)
        List: A list of error strings (errors)
    """
    return {'pdb_code':pdb_code, 'force': force}, True, None