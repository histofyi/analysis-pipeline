from ..fasta import read_sequence_set


def get_simplified_sequence_set(mhc_class, locus):
    sequences, success, errors = read_sequence_set(mhc_class, locus)
    return sequences, success, errors


