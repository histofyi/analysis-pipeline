from .s3 import s3Provider
from .common import build_s3_block_key

def build_core(pdb_code):
    return {
        'pdb_code':pdb_code,
        'organism_common':None,
        'organism_scientific':None,
        'class':None,
        'classical': None,
        'locus':None,
        'allele':None,
        'peptide':None,
        'peptide_name':None,
        'resolution':None,
        'deposition_date':None,
        'release_date':None,
        'components':{},
        'missing_residues':[],
        'complex_count':0,
        'chain_count':0,
        'title':0,
        'authors':[],
        'publication':{}
    }


def initialise(pdb_code, aws_config):
    s3 = s3Provider(aws_config)
    key = build_s3_block_key(pdb_code, 'core', 'info')
    payload = build_core(pdb_code)
    s3.put(key, payload)
    return payload, True, None