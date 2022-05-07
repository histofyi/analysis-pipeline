from flask import current_app
from common.providers import s3Provider, awsKeyProvider
from .data import FacetClass

import logging

class Core(FacetClass):
    def __init__(self):
        super().__init__(self.__class__.__name__, 'core', current_app.config['AWS_CONFIG'])


class PeptideNeighbours(FacetClass):
    def __init__(self):
        super().__init__(self.__class__.__name__, 'peptide_neighbours', current_app.config['AWS_CONFIG'])

    
class PeptideAngles(FacetClass):
    def __init__(self):
        super().__init__(self.__class__.__name__, 'peptide_angles', current_app.config['AWS_CONFIG'])


class AlleleMatch(FacetClass):
    def __init__(self):
        super().__init__(self.__class__.__name__, 'allele_match', current_app.config['AWS_CONFIG'])
