from Bio import PDB
import logging

class SelectChains(PDB.Select):
    """ Only accept the specified chains when saving. """
    def __init__(self, chain_letters):
        self.chain_letters = chain_letters

    def accept_chain(self, chain):
        return (chain.get_id() in self.chain_letters)


def split_assemblies(histo_info, current_assembly, pdb_code):
    split_information = None
    if histo_info['best_match']['confidence'] > 0.8:
        split_information = {}
        chains = histo_info['chain_assignments']
        assembly_count = histo_info['basic_info']['assembly_count']
        i = 0
        complex_array = []
        chain_labels = [chain for chain in chains]
        while i < assembly_count:
            this_complex = []
            for chain in chain_labels:
                this_complex.append(chains[chain]['chains'][i])
            complex_array.append(this_complex)
            i += 1
    else:
        complex_array = []
    if len(complex_array) > 0:
        j = 1
        complexes = []
        for complex in complex_array:
            complex_filename = '{pdb_code}_{complex}.pdb'.format(pdb_code = pdb_code, complex = str(j))
            complex_filepath = '../../data/structures/pdb_format/single_assemblies/{filename}'.format(filename = complex_filename)  
            j += 1
            writer = PDB.PDBIO()
            writer.set_structure(current_assembly)
            writer.save(complex_filepath, select=SelectChains(complex))
            complexes.append({
                'filename': complex_filename,
                'chains': complex
            })
        split_information['complexes'] = complexes    
    else:
        split_information = None
    return split_information
