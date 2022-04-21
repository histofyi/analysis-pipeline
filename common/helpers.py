from flask import current_app, g

from Bio.PDB import PDBParser
from Bio.PDB.MMCIFParser import MMCIFParser
from io import StringIO, TextIOWrapper


from common.providers import s3Provider, awsKeyProvider

import logging






def fetch_constants(slug):
    if not 'constants' in g:
        g.constants = {}
    if slug not in g.constants:
        key = awsKeyProvider().constants_key(slug)
        data, success, errors = s3Provider(current_app.config['AWS_CONFIG']).get(key)
        if success:
            g.constants[slug] = data
            return data
        else:
            return None       
    else:
        return g.constants[slug]



def pdb_loader(pdb_data):
    pdb_file = StringIO(pdb_data.decode('utf-8'))
    parser = PDBParser(PERMISSIVE=1)
    try:
        structure = parser.get_structure('mhc', pdb_file)
        return structure
    except:
        return None


def cif_loader(cif_data, assembly_name):
    cif_file = StringIO(cif_data)
    parser = MMCIFParser(QUIET=True)
    try:
        structure = parser.get_structure(assembly_name, cif_file)
    except:
        structure = None
    return structure


def fetch_core(pdb_code, aws_config):
    key = awsKeyProvider().block_key(pdb_code, 'core', 'info')
    s3 = s3Provider(aws_config)
    data, success, errors = s3.get(key)
    return data, success, errors


def update_block(pdb_code, facet, domain, update, aws_config, privacy='public'):
    key = awsKeyProvider().block_key(pdb_code, facet, domain)
    s3 = s3Provider(aws_config)
    data, success, errors = s3.get(key)
    if success:
        for item in update:
            data[item] = update[item]
        s3.put(key, data)
        return data, True, []
    else:
        return None, False, ['no_matching_item']


def get_hetatoms():
    return sorted(set(fetch_constants('hetatoms')))


def three_letter_to_one(residue):
    if residue.upper() not in get_hetatoms():
        try:
            one_letter = fetch_constants('amino_acids')["natural"]["translations"]["three_letter"][residue.lower()]
        except:
            logging.warn('NEW HET ATOM ' + residue)
            one_letter = 'z'
    else:
        one_letter = 'x'
    return one_letter


def one_letter_to_three(residue):
    if residue.upper() not in ['Z']:
        try:
            three_letter = fetch_constants('amino_acids')["natural"]["translations"]["one_letter"][residue.lower()]
        except:
            logging.warn('UNNATURAL ' + residue)
            three_letter = 'ZZZ'
    else:
        three_letter = 'ZZZ'
    return three_letter



def chunk_one_letter_sequence(self, sequence, residues_per_line):
    # splits sequence into blocks
    chunked_sequence = []
    length = len(sequence)

    while length > residues_per_line:
        chunked_sequence.append(sequence[0:residues_per_line])
        sequence = sequence[residues_per_line:]
        length = len(sequence)
    chunked_sequence.append(sequence)
    return chunked_sequence


def slugify(string):
    return string.replace(' ','_').lower()



def levenshtein_ratio_and_distance(s, t):
    """ levenshtein_ratio_and_distance:
        Calculates levenshtein distance between two strings.
        If ratio_calc = True, the function computes the
        levenshtein distance ratio of similarity between two strings
        For all i and j, distance[i,j] will contain the Levenshtein
        distance between the first i characters of s and the
        first j characters of t
        
        Adapted from
        
        https://www.datacamp.com/community/tutorials/fuzzy-string-python
    """
    # Initialize matrix of zeros
    rows = len(s)+1
    cols = len(t)+1

    distance = np.zeros((rows,cols),dtype = int)

    # Populate matrix of zeros with the indeces of each character of both strings
    for i in range(1, rows):
        for k in range(1,cols):
            distance[i][0] = i
            distance[0][k] = k

    # Iterate over the matrix to compute the cost of deletions,insertions and/or substitutions    
    for col in range(1, cols):
        for row in range(1, rows):
            if s[row-1] == t[col-1]:
                cost = 0 # If the characters are the same in the two strings in a given position [i,j] then the cost is 0
            else:
                cost = 1
            distance[row][col] = min(distance[row-1][col] + 1,      # Cost of deletions
                                 distance[row][col-1] + 1,          # Cost of insertions
                                 distance[row-1][col-1] + cost)     # Cost of substitutions
    
    # Computation of the Levenshtein Distance Ratio
    try:
        ratio = ((len(s)+len(t)) - distance[row][col]) / (len(s)+len(t))
        return ratio, distance[row][col]
    except:
        return None, None
