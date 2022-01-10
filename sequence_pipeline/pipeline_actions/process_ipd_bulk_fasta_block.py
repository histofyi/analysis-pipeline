from .s3 import s3Provider

from .common import build_s3_sequence_key

class_i_starts = ['GSHT','GSHS','GTHS','GYHS','SSYS','VSHS', 'EPHV','GPHS', 'GSPR', 'GHPK','GSHW','ATHS', 'ASHP','VTHS', 'SHTL', 'SHTI', 'SHSL','SHSM','SHTV','SHTY','THAL','THSL','TNTL','EHTI','AHVT','HQTV','EHKV']


def process_ipd_bulk_fasta(aws_config):
    s3 = s3Provider(aws_config)
    key = build_s3_sequence_key('species_map', format='json')
    data, success, errors = s3.get(key)
    class_i_loci = []
    class_ii_alpha_loci = []
    class_ii_beta_loci = []
    for species in data:
        species_data = data[species]
        for locus in species_data['class_i']['alpha']:
            key = build_s3_sequence_key('raw/' +locus, format='json')
            locus_data, success, errors = s3.get(key)
            for allele_group in locus_data:
                this_sequence = locus_data[allele_group]['alleles'][0]['sequence']
                present = False
                for class_i_start in class_i_starts:
                    if class_i_start in this_sequence:
                        present = True
                if not present:
                    class_i_loci.append(allele_group)
        for locus in species_data['class_ii']['alpha']:
            class_ii_alpha_loci.append(locus)
        for locus in species_data['class_ii']['beta']:
            class_ii_beta_loci.append(locus)
    return {'unknown_start':class_i_loci}, success, errors