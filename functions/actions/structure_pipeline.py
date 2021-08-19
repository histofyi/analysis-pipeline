import Bio

import operator

from ..histo import structureInfo
from ..pdb import RCSB
from ..lists import structureSet
from ..structure import split_assemblies, align_structure

from .sequence_pipeline import get_simplified_sequence_set

import logging

from functions.actions import sequence_pipeline
from functions.lists import structureSet

hetatms = ['HOH','EDO','GOL', ' CA', ' CD', ' CU', ' MG', ' NA', ' NI', ' ZN', 'EDO', 'FMT', 'IOD', 'NAG', 'P4G', 'SO4', ' CL']


### Pipeline for categorising new structures
#
# Step 1 fetch PDB file and PDB info from RCSB
#
# Step 2 run automatic_assignment - this will result, if it fits into a common pattern with a set of assigned chain groups with alike chains grouped
#
# Step 2a if edge case, approve assignment or manually set assignment
#
# Step 3 run split_structure - this will result in a set of individual PDB files for each assembly
#
# Step 4 run align_structures - this will iterate through the split structures and create an aligned file for each
#
# Step 5 run match_structure - this will hopefully result in a match to a specific allele by sequence
#
# Step 6 run peptide_neighbours - this will yield a set of residues which have contact with each other. It can also be used to define if the peptide leaves the cleft at c-terminus
#
# Step 7 run peptide_positions - this will result in a definition of the different peptide positions and the bulge
# TODO refactor Step 7 to accound for peptide extensions



sequence_sets = ['hla-a','hla-b','hla-c','h-2']


def check_mhc_class(histo_info, mhc_class):
    mhc_class_present = False
    if 'best_match' in histo_info:
        if mhc_class in histo_info['best_match']['best_match'] and histo_info['best_match']['confidence'] > 0.8:
            mhc_class_present = True
    elif 'complex_type' in histo_info:
        if mhc_class in histo_info['complex_type']:
            mhc_class_present = True
    return mhc_class_present


def clean_record(pdb_code):
    histo_info, success, errors = structureInfo(pdb_code).clean()
    data = {
        'histo_info': histo_info
    }
    return data, success, errors


def fetch_pdb_data(pdb_code):
    rcsb = RCSB()

    # gets the PDB file and the PDB info from RCSB
    pdb_file = rcsb.fetch(pdb_code)
    pdb_info = rcsb.get_info(pdb_code)

    # gets the initial histo_info file
    histo_info, success, errors = structureInfo(pdb_code).get()

    # create a dictionary of just the RCSB info we need
    rcsb_info = {}
    rcsb_info['primary_citation'] = pdb_info['rcsb_primary_citation']
    if 'pdbx_descriptor' in pdb_info['struct']:
        rcsb_info['description'] = ['pdbx_descriptor']
    rcsb_info['resolution_combined'] = pdb_info['rcsb_entry_info']['resolution_combined']
    rcsb_info['title'] = pdb_info['struct']['title']
    rcsb_info['assembly_count'] = pdb_info['rcsb_entry_info']['assembly_count']
    rcsb_info['pdb_code'] = pdb_code

    # persist it to the histo_info file
    histo_info, success, errors = structureInfo(pdb_code).put('rcsb_info', rcsb_info)

    data = {
        'histo_info': histo_info
    }

    return data, success, errors


def automatic_assignment(pdb_code):
    rcsb = RCSB()

    # gets the histo_info file with the RCSB data from Step 1
    histo_info, success, errors = structureInfo(pdb_code).get()

    # pull out the assembly count
    assembly_count = histo_info['rcsb_info']['assembly_count']

    # load the structure into BioPDB
    structure = rcsb.load_structure(pdb_code)

    if True:
        # predict some initial chain assignments
        structure_stats = rcsb.predict_assigned_chains(structure, assembly_count)

        # get a set of the alike chains
        alike_chains = structure_stats['alike_chains']

        histo_info, success, errors = structureInfo(pdb_code).put('alike_chains', alike_chains)

        best_match = structure_stats['best_match']

        histo_info, success, errors = structureInfo(pdb_code).put('best_match', best_match)

        chain_assignments = structure_stats['chain_assignments']

        histo_info, success, errors = structureInfo(pdb_code).put('chain_assignments', chain_assignments)

        basic_info = structure_stats['basic_info']

        histo_info, success, errors = structureInfo(pdb_code).put('basic_info', basic_info)
        logging.warn("BEST MATCH")
        logging.warn(best_match)
        if best_match['confidence'] > 0.8:
            del structure_stats['complex_hits']
            data, success, errors = structureSet(best_match['best_match']).add(pdb_code)
        elif best_match['confidence'] > 0.5:
            data, success, errors = structureSet('probable_' + best_match['best_match']).add(pdb_code)
        else:
            data, success, errors = structureSet('unmatched').add(pdb_code)

        data, success, errors = structureSet('automatically_matched').add(pdb_code)

    #except:
        #data, success, errors = structureSet('error').add(pdb_code)

    data = {
            'histo_info': histo_info
    }
    return data, success, errors


def split_structure(pdb_code):
    histo_info, success, errors = structureInfo(pdb_code).get()
    current_assembly = RCSB().load_structure(pdb_code)
    split_information = split_assemblies(histo_info, current_assembly, pdb_code)
    histo_info, success, errors = structureInfo(pdb_code).put('split_info', split_information)
    data = {
        'histo_info': histo_info
    }
    return data, success, errors


def align_structures(pdb_code):
    histo_info, success, errors = structureInfo(pdb_code).get()
    align_info = {}
    mhc_alpha_chains = []
    #mhc_beta_chains = []
    aligned_assignment = ''
    for chain in histo_info['chain_assignments']:
        if 'class_i_alpha' in histo_info['chain_assignments'][chain]['label']:
            logging.warn('CLASS I ALPHA FOUND')
            mhc_alpha_chains = histo_info['chain_assignments'][chain]['chains']
            aligned_assignment = 'class_i_alpha'
    errors = []
    if 'split_info' in histo_info:
        logging.warn("HAS SPLIT INFO")
        i = 1
        for complex in histo_info['split_info']['complexes']:
            logging.warn(complex)
            for chain in mhc_alpha_chains:
                logging.warn(chain)
                if chain in complex['chains']:
                    complex_number = 'complex_' + str(i)
                    current_alignment = {
                        'aligned_chain': chain,
                        'chain_assignment': aligned_assignment,
                        'filename': complex['filename']
                    }
                    if True:
                        align_information = align_structure('class_i', pdb_code, str(i), chain)
                        if align_information:
                            current_alignment['rms'] = align_information
                        else:
                            current_alignment['errors'] = ['unable_to_load']
                    else:
                        current_alignment['errors'] = ['unable_to_align']
                    align_info[complex_number] = current_alignment
            i += 1
        histo_info, success, errors = structureInfo(pdb_code).put('align_info', align_info)  
    else:
        align_info = {'error':'structure_not_split'}  
    data = {
        'histo_info': histo_info
    }
    return data, success, errors


def first_pass_sequence_match(sequence_to_test):
    match_info = None
    for locus in sequence_sets:
        locus_set, success, errors = get_simplified_sequence_set('class_i', locus)
        species = locus_set['species']
        for allele_group in  locus_set['sequences']:
            this_sequence = locus_set['sequences'][allele_group]['alleles'][0]['sequence']
            if len(sequence_to_test) < len(this_sequence):
                this_sequence = this_sequence[0:len(sequence_to_test)]
            if sequence_to_test == this_sequence:
                match_info = {
                    'species': species,
                    'allele': locus_set['sequences'][allele_group]['alleles'][0]['allele'],
                    'allele_group': locus_set['sequences'][allele_group]['alleles'][0]['allele_group'],
                    'locus':locus,
                    'confidence': 1
                }
                break
        if match_info:
            break
    return match_info
    

def second_pass_sequence_match(sequence_to_test):
    match_info = None
    for locus in sequence_sets:
        locus_set, success, errors = get_simplified_sequence_set('class_i', locus)
        species = locus_set['species']
        for allele_group in  locus_set['sequences']:
            allele_set = locus_set['sequences'][allele_group]['alleles']
            for allele in allele_set:
                this_sequence = allele['sequence']
                if len(sequence_to_test) < len(this_sequence):
                    this_sequence = this_sequence[0:len(sequence_to_test)]
                if sequence_to_test == this_sequence:
                    match_info = {
                        'species': species,
                        'allele': allele['allele'],
                        'allele_group': allele['allele_group'],
                        'locus':locus,
                        'confidence': 1
                    }
                    break
        if match_info:
            break
    return match_info


def match_structure(pdb_code):
    histo_info, success, errors = structureInfo(pdb_code).get()
    match_info = None
    has_class_i_alpha = check_mhc_class(histo_info, 'class_i')
    if has_class_i_alpha:
        sequence_to_test = histo_info['chain_assignments']['class_i_alpha']['sequences'][0]
        if len(sequence_to_test) > 275:
            sequence_to_test = sequence_to_test[0:275]
        match_info = first_pass_sequence_match(sequence_to_test)
        if not match_info:
            match_info = second_pass_sequence_match(sequence_to_test)
    if match_info:
        logging.warn("MATCH")
        logging.warn(match_info)
        histo_info, success, errors = structureInfo(pdb_code).put('match_info', match_info)
        if 'species' in match_info:
            species = match_info['species']
        else:
            species = 'other'
        data, success, errors = structureSet('alleles/' + species + '/all').add(pdb_code)
        data, success, errors = structureSet('alleles/' + species + '/'+ match_info['locus'] + '/all').add(pdb_code)
        data, success, errors = structureSet('alleles/' + species + '/'+ match_info['locus'] + '/' + match_info['allele_group'].replace('*','')).add(pdb_code)
        data, success, errors = structureSet('alleles/' + species + '/'+ match_info['locus'] + '/' + match_info['allele'].replace(':','_').replace('*','')).add(pdb_code)
    else:
        data, success, errors = structureSet('alleles/nomatch').add(pdb_code)
    data = {
        'histo_info': histo_info
    }
    return data, True, None


def peptide_positions(pdb_code):
    histo_info, success, errors = structureInfo(pdb_code).get()
    is_class_i = check_mhc_class(histo_info, 'class_i')
    current_assembly = RCSB().load_structure(pdb_code)
    extension = []
    if histo_info['neighbour_info']:
        #logging.warn(histo_info['neighbour_info'])
        for chain in current_assembly.get_chains():
            if chain.id == histo_info['chain_assignments']['class_i_peptide']['chains'][0]:
                sequence_array = [residue.resname for residue in chain]
                clean_array = [residue for residue in sequence_array if residue not in hetatms]
                sequence_array = clean_array
                peptide_length = len(sequence_array)
                if histo_info['neighbour_info']['extended_peptide']:
                    extension_positions = histo_info['neighbour_info']['extension_positions']
                    extension_positions.sort()
                    logging.warn('EXTENDED PEPTIDE')
                    logging.warn(extension_positions)
                    logging.warn(sequence_array)
                    i = 0
                    for position in extension_positions:
                        extension.append(sequence_array[position - 1])                        
                        i += 1
                    logging.warn(extension)
                    peptide_length -= i
                    logging.warn(peptide_length)
                if peptide_length >= 8:
                    peptide_positions = {
                        'p1':sequence_array[0],
                        'p2':sequence_array[1],                        
                        'p3':sequence_array[2],
                        'pn-2':sequence_array[peptide_length - 3],
                        'pn-1':sequence_array[peptide_length - 2],
                        'pn':sequence_array[peptide_length - 1],
                        'bulge': sequence_array[3:peptide_length - 3],
                        'bulge_length': peptide_length - 6,
                        'extension': extension
                    }
                else:
                    peptide_positions = None
        if peptide_positions:
            data, success, errors = structureSet('peptides/class_i/positions/p1/'+ peptide_positions['p1'].lower()).add(pdb_code)
            data, success, errors = structureSet('peptides/class_i/positions/p2/'+ peptide_positions['p2'].lower()).add(pdb_code)
            data, success, errors = structureSet('peptides/class_i/positions/p3/'+ peptide_positions['p3'].lower()).add(pdb_code)
            data, success, errors = structureSet('peptides/class_i/positions/pn-2/'+ peptide_positions['pn-2'].lower()).add(pdb_code)
            data, success, errors = structureSet('peptides/class_i/positions/pn-1/'+ peptide_positions['pn-1'].lower()).add(pdb_code)
            data, success, errors = structureSet('peptides/class_i/positions/pn/'+ peptide_positions['pn'].lower()).add(pdb_code)
            data, success, errors = structureSet('peptides/class_i/bulges/length_'+ str(peptide_positions['bulge_length'])).add(pdb_code)
            if len(peptide_positions['extension']) > 0:
                data, success, errors = structureSet('peptides/class_i/extensions/length_'+ str(len(peptide_positions['extension']))).add(pdb_code)

            histo_info, success, errors = structureInfo(pdb_code).put('peptide_positions', peptide_positions)
            #logging.warn(peptide_positions)
    data = {
        'histo_info': histo_info
    }
    return data, True, None


def offset_id(histo_info, chain_type, id):
    if 'chain_offsets' in histo_info:
        if chain_type in histo_info['chain_offsets']:
            if id >= histo_info['chain_offsets'][chain_type]['start_id']:
                revised_id = id + histo_info['chain_offsets'][chain_type]['offset']
                return revised_id
    return id




def peptide_neighbours(pdb_code):
    histo_info, success, errors = structureInfo(pdb_code).get()
    is_class_i = check_mhc_class(histo_info, 'class_i')
    current_assembly = RCSB().load_structure(pdb_code +'_1', directory='structures/pdb_format/single_assemblies')
    all_atoms = []

    peptide_set = {}
    peptide_length = 0

    if is_class_i:
        class_i_alpha = histo_info['chain_assignments']['class_i_alpha']['chains'][0]
        class_i_peptide = histo_info['chain_assignments']['class_i_peptide']['chains'][0]
        peptide_length = histo_info['chain_assignments']['class_i_peptide']['lengths'][0]
        for chain in current_assembly.get_chains():
            if chain.id == class_i_peptide:
                for residue in chain:
                    if residue.id[0] == ' ':
                        residue_id = offset_id(histo_info, 'class_i_peptide', residue.id[1])
                        peptide_set[residue_id] = {'residue':residue.resname,'position':residue_id}

 # TODO reduce computational problem by only looking at one set of chains

    chains_to_test = [histo_info['chain_assignments'][chain]['chains'][0] for chain in histo_info['chain_assignments'] if chain in ['class_i_alpha','class_i_peptide']]                      
    
    for chain in current_assembly.get_chains():
        if chain.get_id() in chains_to_test:
            for residue in chain:
                if residue.id[0] == ' ':
                    for atom in residue:
                        all_atoms.append(atom)

    neighbor = Bio.PDB.NeighborSearch(all_atoms)
    neighbours = neighbor.search_all(5, level='R')

    contacts = {
        class_i_alpha:{},
        class_i_peptide:{}
    }

    for residue_pair in neighbours:
        residue_1 = residue_pair[0]
        residue_2 = residue_pair[1]
        if residue_1.get_parent().id != residue_2.get_parent().id:
            chain_pair = [residue_1.get_parent().id, residue_2.get_parent().id]
            if class_i_peptide in chain_pair and class_i_alpha in chain_pair:
                if residue_1.get_parent().id == class_i_alpha:
                    class_i_details = {'residue':residue_1.resname, 'position':residue_1.get_id()[1]}
                    peptide_details = {'residue':residue_2.resname, 'position':residue_2.get_id()[1]}
                else:
                    peptide_details = {'residue':residue_1.resname, 'position':residue_1.get_id()[1]}
                    class_i_details = {'residue':residue_2.resname, 'position':residue_2.get_id()[1]}


                class_i_residue_id = offset_id(histo_info, 'class_i_alpha', class_i_details['position'])
                peptide_residue_id = offset_id(histo_info, 'class_i_peptide', peptide_details['position'])

                class_i_details['position'] = class_i_residue_id
                peptide_details['position'] = peptide_residue_id


                if class_i_residue_id not in contacts[class_i_alpha]:
                    contacts[class_i_alpha][class_i_residue_id] = {'position':class_i_residue_id, 'residue':class_i_details['residue'], 'neighbours':[] }
                contacts[class_i_alpha][class_i_residue_id]['neighbours'].append(peptide_details)

                if peptide_residue_id not in contacts[class_i_peptide]:
                    contacts[class_i_peptide][peptide_residue_id] = {'position':peptide_residue_id, 'residue':peptide_details['residue'], 'neighbours':[] }
                contacts[class_i_peptide][peptide_residue_id]['neighbours'].append(class_i_details)

    sorted_peptide = dict(sorted(contacts[class_i_peptide].items()))
    


    i = 1
    extended_peptide = False
    exposed_bulge = False
    extension_positions = []
    extension_length = 0
    for residue in peptide_set:
        if residue not in sorted_peptide:
            sorted_peptide[residue] = {'position':residue, 'residue': peptide_set[residue]['residue'], 'neighbours': []}
            extension_positions.append(residue)
    sorted_peptide = dict(sorted(sorted_peptide.items()))


    last_position = False
    for position in sorted_peptide:
        if last_position:
            if position not in extension_positions:
                extension_positions.append(position)
                extended_peptide = True

        abd_contacts = [neighbour['position'] for neighbour in sorted_peptide[position]['neighbours']]
        if 116 in abd_contacts and 143 in abd_contacts:
            logging.warn('116/143')
            logging.warn('LAST POSITION')
            logging.warn(sorted_peptide[position])
            last_position = True
        
    sorted_peptide = dict(sorted(sorted_peptide.items()))
    sorted_abd = dict(sorted(contacts[class_i_alpha].items()))

    for position in extension_positions:
        if position == peptide_length and peptide_length > 8:
            extended_peptide = True
    if not extended_peptide and len(extension_positions) > 0 and peptide_length > 8:
        exposed_bulge = True

    if len(extension_positions) == peptide_length:
        logging.warn(extension_positions)
        logging.warn('MISMATCHED COMPLEX')
        data, success, errors = structureSet('possible_mismatched_chains').add(pdb_code)


    else:
        if extended_peptide and len(peptide_set) > 8:
            data, success, errors = structureSet('possible_extended_peptide').add(pdb_code)
        if exposed_bulge and len(peptide_set) > 8:
            data, success, errors = structureSet('possible_exposed_bulge').add(pdb_code)

        neighbour_info = {
            'class_i_peptide': sorted_peptide,
            'class_i_alpha': sorted_abd,
            'extended_peptide': extended_peptide,
            'exposed_bulge': exposed_bulge
        }

        if extended_peptide:
            neighbour_info['extension_positions'] = extension_positions
        if exposed_bulge:
            neighbour_info['exposed_bulge_positions'] = extension_positions

        if extension_positions or exposed_bulge:
            logging.warn(neighbour_info)

        histo_info, success, errors = structureInfo(pdb_code).put('neighbour_info', neighbour_info)
    
    logging.warn(sorted_peptide)

    data = {
        'histo_info': histo_info
    }
    return data, True, None