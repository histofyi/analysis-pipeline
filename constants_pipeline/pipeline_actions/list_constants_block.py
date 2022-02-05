from .constants import CONSTANTS_FILES, constants_array

def list_constants(aws_config):
    return {'constants':constants_array()}, True, []