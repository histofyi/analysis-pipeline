CONSTANTS_FILES = {
    'amino_acids':{'slug':'amino_acids','name':'Amino acids','description':'A set of mappings between one letter and three letter codes.'},
    'chains':{'slug':'chains','name':'Chains','description':'A set of standardised names, colours and details of individual chains of immune system complexes.'},
    'class_i_starts':{'slug':'class_i_starts','name':'Class I alpha 1 starts', 'description':'A set of the first four amino acids of the alpha 1 chain of Class I molecules to allow for removal of signal peptide sequences.'},
    'hetatoms':{'slug':'hetatoms', 'name':'Hetatoms', 'description': 'A set of the HETATOMS found in MHC structures in the PDB'},
    'loci':{'slug':'loci', 'name': 'Loci', 'description':'A set of MHC Class I and Class II loci derived from the IPD dataset'},
    'peptide_lengths':{'slug':'peptide_lengths', 'name': 'Peptide lengtsh', 'description': 'A set of human readable names for different length peptides' },
    'species_overrides':{'slug':'species_overrides','name':'Species overrides','description':'A dataset to correct the species of specific structures.'},
    'species':{'slug':'species','name':'Species','description':'A set of standardised names, colours and details of individual chains of immune system complexes.'}
}


def constants_array(constants_dict=CONSTANTS_FILES):
    return [CONSTANTS_FILES[constant] for constant in CONSTANTS_FILES]
