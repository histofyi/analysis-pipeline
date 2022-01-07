from Bio import SeqIO
from io import StringIO

from .s3 import s3Provider
from .common import build_s3_sequence_key

import logging

class_ii_alpha_loci = ['dra','dpa','dqa','doa','dma']
class_ii_beta_loci = ['drb','dpb','dqb','dob','dmb']

def split_ipd_bulk_fasta(aws_config):
    loci = {}
    step_errors = []
    all_alleles = []
    locus_list = []
    s3 = s3Provider(aws_config)
    key = build_s3_sequence_key('mhc_prot_ipd', format='fasta')
    data, success, errors = s3.get(key, data_format='fasta')
    if data:
        fasta_file = StringIO(data.decode('utf-8'))
        all_sequences = SeqIO.parse(fasta_file, "fasta")
        for record in all_sequences:
            description_parts = record.description.split(' ')
            full_allele_identifier = description_parts[1].lower()
            allele_group = full_allele_identifier.split(':')[0]
            locus = allele_group.split('*')[0]
            organism = locus.split('-')[0]
            locus_type = locus.split('-')[1]
            if locus_type not in locus_list:
                locus_list.append(locus_type)
            allele_identifier = (':').join(full_allele_identifier.split(':')[:2])

            if organism not in loci:
                loci[organism] = {}
            if locus not in loci[organism]:
                loci[organism][locus] = {}
            if allele_group not in loci[organism][locus]:
                loci[organism][locus][allele_group] = {'alleles':[]}
            if allele_identifier not in all_alleles:
                all_alleles.append(allele_identifier)
                allele_info = {
                    'id': record.id,
                    'allele': allele_identifier,
                    'allele_group': allele_group,
                    'description': record.description,
                    'sequence':str(record.seq)
                }
                loci[organism][locus][allele_group]['alleles'].append(allele_info)
            else:
                pass
            
    species_map = {}
    for species in loci:
        species_map[species] = {'class_i':{'alpha':[]},'class_ii':{'alpha':[],'beta':[]},'tap':[],'stem':species}
        for locus in loci[species]:
            is_class_ii_alpha = False
            is_class_ii_beta = False
            is_tap = False
            if 'tap' in locus:
                is_tap = True
            if not is_tap:
                for potential_locus in class_ii_alpha_loci:
                    if potential_locus in locus:
                        is_class_ii_alpha = True
            if not is_class_ii_alpha:
                for potential_locus in class_ii_beta_loci:
                    if potential_locus in locus:
                        is_class_ii_beta = True
            if is_class_ii_alpha:
                if locus not in species_map[species]['class_ii']['alpha']:
                    species_map[species]['class_ii']['alpha'].append(locus)
            elif is_class_ii_beta:
                if locus not in species_map[species]['class_ii']['beta']:
                    species_map[species]['class_ii']['beta'].append(locus)
            elif is_tap:
                if locus not in species_map[species]['tap']:
                    species_map[species]['tap'].append(locus)
            else:
                if locus not in species_map[species]['class_i']['alpha']:
                    species_map[species]['class_i']['alpha'].append(locus)


    return {'loci':loci}, True, step_errors
