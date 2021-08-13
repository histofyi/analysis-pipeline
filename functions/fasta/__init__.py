from Bio import SeqIO
from ..providers import filesystemProvider

import logging

file = filesystemProvider(None)



def read_sequence_set(mhc_class, locus):
    path = '../../data/sequences/{mhc_class}/{locus}.fasta'.format(mhc_class = mhc_class, locus = locus)
    all_sequences = SeqIO.parse(path, "fasta")
    return all_sequences, True, None