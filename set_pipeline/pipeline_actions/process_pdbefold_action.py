from typing import Dict, Tuple, List, Optional, Union

from common.providers import filesystemProvider
from common.models import itemSet
from common.functions import de_slugify, slugify

import logging


fs = filesystemProvider('set_pipeline/files')

def process_pdbefold(mhc_class:str) -> Dict:
    """
    This function takes a 'reslist.dat' file from the PDBeFold server of the EMBL-EBI (https://www.ebi.ac.uk/msd-srv/ssm/cgi-bin/ssmserver)
    and turns it into a set of possible molecules to run through the pipeline.

    The PDBeFold service matches a template structure to give a set of results which align structurally to it with homology.

    Args:
        mhc_class (str): the class of MHC molecule e.g. 'class_i'

    Returns:
        Dict : a set of items
    """
    molecules = {'class_i':'1HHK','class_ii':'1DLH'}
    slug = f'{mhc_class}_pdbefold_query'
    title = f'{de_slugify(mhc_class)} PDBeFold Query'
    description = f'PDBeFold Query for {de_slugify(mhc_class)}. Template molecule is {molecules[mhc_class]}'
    data, success, errors = fs.get(mhc_class, format='txt')

    rows = [row.replace('PDB ','').split() for row in data.split('\n') if len(row) > 0]

    complexes = []

    i = 0
    for row in rows:
        if i == 2:
            labels = [slugify(label) for label in row]
            logging.warn(labels)
        if i > 2:
            this_row = dict(zip(labels, row))
            if 'target' in this_row:
                complexes.append(this_row['target'].split(':')[0])
        i += 1
    complexes = list(set(complexes))
    complexes = sorted(complexes)
    itemset, success, errors = itemSet(slug).create_or_update(title, description, complexes, 'search_query')
    return itemset
