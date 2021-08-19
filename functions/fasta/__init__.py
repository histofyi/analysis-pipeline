from Bio import SeqIO
from ..providers import filesystemProvider
import json
import datetime

import logging

file = filesystemProvider(None)







def read_sequence_set(mhc_class, locus):
    base_file_ppath = 'sequences/{mhc_class}/{locus}'.format(mhc_class = mhc_class, locus = locus)
    sequences, success, errors = file.get(base_file_ppath)
    if not success:        
        last_updated = datetime.datetime.now().isoformat()
        fasta_path = '../../data/{base_file_ppath}.fasta'.format(base_file_ppath = base_file_ppath)
        all_sequences = SeqIO.parse(fasta_path, "fasta")
        sequences = filter_sequence_set(all_sequences)
        sequences['last_updated'] = last_updated
        if 'hla-' in locus:
            sequences['species'] = 'human'            
        sequences, success, errors = file.put(base_file_ppath, json.dumps(sequences))
    return sequences, True, None


def filter_sequence_set(all_sequences):
    sequence_set = {}
    unique_sequences = []
    i = 0
    j = 0
    for record in all_sequences:
        logging.warn(record)
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
    return sequences