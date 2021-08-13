from ..fasta import read_sequence_set


def get_simplified_sequence_set(mhc_class, locus):
    all_sequences, success, errors = read_sequence_set(mhc_class, locus)
    sequence_set = {}
    unique_sequences = []
    i = 0
    j = 0
    for record in all_sequences:
        if len(record.seq) > 300:
            trimmed_sequence = str(record.seq)[24:299]
            abd_sequence = trimmed_sequence[0:180]
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
    return sequences, success, errors


