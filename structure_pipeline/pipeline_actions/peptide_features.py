from typing import Dict, List, Tuple

from common.providers import s3Provider, awsKeyProvider
from common.helpers import fetch_core, slugify

from common.models import itemSet

import logging


def peptide_features(pdb_code:str, aws_config:Dict, force:bool=False) -> Tuple[Dict,bool,List]:
    core, success, errors = fetch_core(pdb_code, aws_config)
    s3 = s3Provider(aws_config)
    peptide_key = awsKeyProvider().block_key(pdb_code, 'peptide_neighbours', 'info')
    sorted_peptide, success, errors = s3.get(peptide_key)
    
    extended_peptide = False
    exposed_bulge = False
    peptide_features = {}
    extensions = None

    for assembly_id in sorted_peptide:
        peptide_features[assembly_id] = {
            'PN':None,
            'PC':None,
            'exposed':[],
            'buried':[]
        }
        members = [pdb_code]
        for position in sorted_peptide[assembly_id]:
            abd_contacts = [neighbour['position'] for neighbour in sorted_peptide[assembly_id][position]['neighbours']]
            if len(abd_contacts) <=3:
                peptide_features[assembly_id]['exposed'].append(position)
            else:
                peptide_features[assembly_id]['buried'].append(position)
            if 7 in abd_contacts and 171 in abd_contacts:
                peptide_features[assembly_id]['PN'] = position
                
            if 116 in abd_contacts and 143 in abd_contacts:
                peptide_features[assembly_id]['PC'] = position

        if int(peptide_features[assembly_id]['PN']) > 1:
            extended_peptide = True 
            extensions = {'n-terminal':{'positions':[]}}
            set_title = f'N-terminally extended structures'
            set_slug = slugify('c terminally extended')
            set_description = f'Structures containing a N-terminal extension'
            context = 'features'
            itemset, success, errors = itemSet(set_slug, context).create_or_update(set_title, set_description, members, context)

        if int(peptide_features[assembly_id]['PC']) < len(sorted_peptide[assembly_id]): 
            extended_peptide = True
            extensions = {'c-terminal':{'positions':[]}}
            set_title = f'C-terminally extended structures'
            set_slug = slugify('c terminally extended')
            set_description = f'Structures containing a C-terminal extension'
            context = 'features'
            itemset, success, errors = itemSet(set_slug, context).create_or_update(set_title, set_description, members, context)

        if extended_peptide:
            set_title = f'Extended peptide structures'
            set_slug = slugify('extended')
            set_description = f'Structures containing an extension at either end of the cleft'
            context = 'features'
            itemset, success, errors = itemSet(set_slug, context).create_or_update(set_title, set_description, members, context)

    peptide_features['extended_peptide'] = extended_peptide
    peptide_features['extensions'] = extensions
    step_errors = []
    action = {
        'peptide_features':peptide_features
    }
    output = {
        'action':action,
        'core':core
    }
    return output, True, step_errors