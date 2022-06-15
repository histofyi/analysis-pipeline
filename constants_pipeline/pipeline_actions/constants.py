from typing import Dict, List


CONSTANTS_FILES = {
    'amino_acids':{'slug':'amino_acids','name':'Amino acids','description':'A set of mappings between one letter and three letter codes.'},
    'chains':{'slug':'chains','name':'Chains','description':'A set of standardised names, colours and details of individual chains of immune system complexes.'},
    'mhc_starts':{'slug':'mhc_starts','name':'MHC chain starts', 'description':'A set of the first amino acids of the different MHC chains to allow for removal of signal peptide sequences.'},
    'hetatoms':{'slug':'hetatoms', 'name':'Hetatoms', 'description': 'A set of the HETATOMS found in MHC structures in the PDB'},
    'loci':{'slug':'loci', 'name': 'Loci', 'description':'A set of MHC Class I and Class II loci derived from the IPD dataset'},
    'peptide_lengths':{'slug':'peptide_lengths', 'name': 'Peptide lengths', 'description': 'A set of human readable names for different length peptides' },
    'species_overrides':{'slug':'species_overrides','name':'Species overrides','description':'A dataset to correct the species of specific structures.'},
    'species':{'slug':'species','name':'Species','description':'A set of standardised species and loci dervied from IPD dataset.'}
}


def constants_array(constants_dict: Dict=CONSTANTS_FILES) -> List:
    """
    Function to return an array of constants from the constants dictionary

    Args:
        constants_dict (dictionary) : used to override the constants dictionary declared in this file
    Returns:
        An array of metadata about the constants
    """
    if not constants_dict:
        constants_dict = CONSTANTS_FILES
    return [constants_dict[constant] for constant in constants_dict]


def constants_details(slug:str) -> Dict:
    """
    Function to return the metadata on a specific constants file

    Args:
        slug (str) : the slug for a specific file
    Returns:
        A dictionary containing the metadata for the specific file
    """
    for constants in constants_array():
        if constants['slug'] == slug:
            return constants    