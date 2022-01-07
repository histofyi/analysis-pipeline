
from common import trim_class_i_alpha_sequence

import logging


def filter_sequence_set(all_sequences):
    sequence_set = {}
    unique_sequences = []
    i = 0
    j = 0
    for record in all_sequences:
        logging.warn(record)
        if len(record.seq) > 300:
            trimmed_sequence, abd_sequence = trim_class_i_alpha_sequence(record.seq)
            if abd_sequence not in unique_sequences:
                description_parts = record.description.split(' ')
                allele_number = description_parts[1]
                allele_group = allele_number.split(':')[0]
                if not allele_group in sequence_set:
                    sequence_set[allele_group] = {
                        'count':0,
                        'alleles': []
                    }

                sequence_set[allele_group]['alleles'].append({
                    'sequence': trimmed_sequence,
                    'id': record.id,
                    'allele': allele_number,
                    'allele_group': allele_group,
                    'description': record.description
                })
                sequence_set[allele_group]['count'] += 1
                unique_sequences.append(abd_sequence)
                j += 1
        i += 1
    sequences = {
        'allele_group_count': len(sequence_set),
        'original_count': i,
        'unique_abd_count': j,
        'sequences': sequence_set
    }
    return sequences