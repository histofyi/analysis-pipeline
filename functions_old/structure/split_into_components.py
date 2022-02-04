from Bio import PDB

from ..pdb import RCSB

import logging

class SelectChains(PDB.Select):
    """ Only accept the specified chains when saving. """
    def __init__(self, chain_letters):
        self.chain_letters = chain_letters

    def accept_chain(self, chain):
        return (chain.get_id() in self.chain_letters)


class NonHetSelect(PDB.Select):
    def accept_residue(self, residue):
        return 1 if residue.id[0] == " " else 0



def extract_peptide(current_complex_peptide, complex_filename, current_complex):
    complex_filepath = '../../data/structures/pdb_format/fragments/peptides/{filename}'.format(filename = complex_filename)  
    complex_id = complex_filename.replace('.pdb','')
    writer = PDB.PDBIO()
    writer.set_structure(current_complex)
    writer.save(complex_filepath, select=SelectChains([current_complex_peptide]))
    peptide = RCSB().load_structure(complex_id, directory = 'structures/pdb_format/fragments/peptides')
    only_peptide_filepath = '../../data/structures/pdb_format/fragments/peptides/{filename}_no_het.pdb'.format(filename = complex_id) 
    writer.set_structure(peptide)
    writer.save(only_peptide_filepath, select=NonHetSelect())
    return True