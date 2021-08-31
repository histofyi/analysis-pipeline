import Bio

import operator

from ..histo import structureInfo
from ..pdb import RCSB
from ..lists import structureSet
from ..structure import split_assemblies, align_structure, extract_peptide, generate_peptide_angles

from .sequence_pipeline import get_simplified_sequence_set

import logging

from functions.actions import sequence_pipeline
from functions.lists import structureSet

from ..providers import filesystemProvider
from ..textanalysis import levenshtein_ratio_and_distance


hetatms = ['HOH','EDO','GOL', ' CA', ' CD', ' CU', ' MG', ' NA', ' NI', ' ZN', 'EDO', 'FMT', 'IOD', 'NAG', 'P4G', 'SO4', ' CL']
filesystem = filesystemProvider(None)


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
# 
# Step 8 run extract_peptides - this will result in a separate pdb file for the peptide in a structure
# 
# Step 9 run measure_peptide_angles - this will create a dictionary of dihedral angles and torsion angles for the peptides


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


# Step 0
def clean_record(pdb_code):
    step_errors = []
    histo_info, success, errors = structureInfo(pdb_code).clean()
    if success:
        data = {
            'histo_info': histo_info
        }
        step_errors = None
    else:
        data = None
        step_errors.append({'error':'unknown_error'})
    return data, success, step_errors


# Step 1
def fetch_pdb_data(pdb_code):
    step_errors = []
    try:
        rcsb = RCSB()

        # gets the PDB file and the PDB info from RCSB
        pdb_file = rcsb.fetch(pdb_code)
        pdb_info = rcsb.get_info(pdb_code)
    except:
        step_errors.append({'error':'unknown_error'})

    if len(step_errors) == 0:
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
        step_errors = None
    else:
        data = None
        success = False
    return data, success, errors


# Step 2
def automatic_assignment(pdb_code):
    step_errors = []
    rcsb = RCSB()

    # gets the histo_info file with the RCSB data from Step 1
    histo_info, success, errors = structureInfo(pdb_code).get()

    # pull out the assembly count
    assembly_count = histo_info['rcsb_info']['assembly_count']

    try:
        # load the structure into BioPDB
        structure = rcsb.load_structure(pdb_code)
    except:
        step_errors.append({'error':'unable_to_load_structure', 'pdb_code':pdb_code})

    if len(step_errors) == 0:
        # predict some initial chain assignments
        structure_stats = rcsb.predict_assigned_chains(structure, assembly_count)

        if structure_stats and 'alike_chains' in structure_stats:
            # get a set of the alike chains
            alike_chains = structure_stats['alike_chains']
            histo_info, success, errors = structureInfo(pdb_code).put('alike_chains', alike_chains)
        else:
            step_errors.append({'error':'no_alike_chains', 'pdb_code':pdb_code})

        if structure_stats and 'best_match' in structure_stats:
            best_match = structure_stats['best_match']
            histo_info, success, errors = structureInfo(pdb_code).put('best_match', best_match)
        
        if structure_stats and 'chain_assignments' in structure_stats:
            chain_assignments = structure_stats['chain_assignments']
            histo_info, success, errors = structureInfo(pdb_code).put('chain_assignments', chain_assignments)

        basic_info = structure_stats['basic_info']

        histo_info, success, errors = structureInfo(pdb_code).put('basic_info', basic_info)

        if best_match:
            if best_match['confidence'] > 0.8:
                del structure_stats['complex_hits']
                data, success, errors = structureSet(best_match['best_match']).add(pdb_code)
                data, success, errors = structureSet('automatically_matched').add(pdb_code)

            elif best_match['confidence'] > 0.5:
                data, success, errors = structureSet('probable_' + best_match['best_match']).add(pdb_code)
            else:
                data, success, errors = structureSet('unmatched').add(pdb_code)
                step_errors.append({'error':'not_matched', 'pdb_code':pdb_code})
        else:
            data, success, errors = structureSet('error').add(pdb_code)
            step_errors.append({'error':'not_matched', 'pdb_code':pdb_code})
    
    if len(step_errors) == 0:
        data = {
            'histo_info': histo_info
        }
        step_errors = None
        success = True
    else:
        data = None
        success = False

    return data, success, step_errors


def split_structure(pdb_code):
    step_errors = []
    rcsb = RCSB()

    histo_info, success, errors = structureInfo(pdb_code).get()
    try:
        # load the structure into BioPDB
        current_assembly = rcsb.load_structure(pdb_code)
    except:
        step_errors.append({'error':'unable_to_load_structure', 'pdb_code':pdb_code})

    if len(step_errors) == 0:
        split_information = split_assemblies(histo_info, current_assembly, pdb_code)
        if split_information:
            if len(split_information) > 0:
                histo_info, success, errors = structureInfo(pdb_code).put('split_info', split_information)
            else:
                step_errors.append({'error':'unable_to_split_structure', 'pdb_code':pdb_code})
        else:
            step_errors.append({'error':'unable_to_split_structure', 'pdb_code':pdb_code})
    if len(step_errors) == 0:
        data = {
            'histo_info': histo_info
        }
    else:
        data = None
        success = False
    return data, success, step_errors


def align_structures(pdb_code):
    histo_info, success, errors = structureInfo(pdb_code).get()
    step_errors = []
    if 'split_info' in histo_info:
        align_info = {}
        mhc_alpha_chains = []
        aligned_assignment = ''
        for chain in histo_info['chain_assignments']:
            logging.warn(pdb_code)
            logging.warn(chain)
            logging.warn(histo_info['chain_assignments'][chain])
            if chain != 'unassigned':
                if 'label' in histo_info['chain_assignments'][chain]:
                    if 'class_i_alpha' in histo_info['chain_assignments'][chain]['label']:
                        mhc_alpha_chains = histo_info['chain_assignments'][chain]['chains']
                        aligned_assignment = 'class_i_alpha'
                else:
                    aligned_assignment = 'unassigned'    
            else:
                aligned_assignment = 'unassigned'
        if aligned_assignment == 'class_i_alpha':
            i = 1
            logging.warn(pdb_code)
            logging.warn(histo_info['split_info'])
            if histo_info['split_info'] is not None:
                for complex in histo_info['split_info']['complexes']:
                    for chain in mhc_alpha_chains:
                        current_alignment = None
                        if chain in complex['chains']:
                            complex_number = 'complex_' + str(i)
                            current_alignment = {
                                'aligned_chain': chain,
                                'chain_assignment': aligned_assignment,
                                'filename': complex['filename']
                            }
                            if current_alignment:
                                align_information, errors = align_structure('class_i', pdb_code, str(i), chain)
                                if align_information:
                                    current_alignment['rms'] = align_information
                                else:
                                    step_errors.append({'error':errors, 'pdb_code':pdb_code})
                            else:
                                step_errors.append({'error':'unable_to_align', 'pdb_code':pdb_code})
                            align_info[complex_number] = current_alignment
                    i += 1
                histo_info, success, errors = structureInfo(pdb_code).put('align_info', align_info) 
            else:
                step_errors.append({'error':'no_split_complexes', 'pdb_code':pdb_code}) 
        else:
            step_errors.append({'error':'unassigned_chains', 'pdb_code':pdb_code})
    else:
        step_errors.append({'error':'structure_not_split', 'pdb_code':pdb_code})
    if len(step_errors) == 0:
        data = {
            'histo_info': histo_info
        }
    else:
        data = None
        success = False
    return data, success, step_errors


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


def third_pass_sequence_match(sequence_to_test):
    match_info = None
    best_ratio = 0
    ratio = 0
    for locus in sequence_sets:
        locus_set, success, errors = get_simplified_sequence_set('class_i', locus)
        species = locus_set['species']
        for allele_group in  locus_set['sequences']:
            this_sequence = locus_set['sequences'][allele_group]['alleles'][0]['sequence']
            if len(sequence_to_test) < len(this_sequence):
                this_sequence = this_sequence[0:len(sequence_to_test)]
                ratio, distance = levenshtein_ratio_and_distance(this_sequence, sequence_to_test)
            if ratio > 0.97 and ratio > best_ratio:
                best_ratio = ratio
                match_info = {
                    'species': species,
                    'allele': locus_set['sequences'][allele_group]['alleles'][0]['allele'],
                    'allele_group': locus_set['sequences'][allele_group]['alleles'][0]['allele_group'],
                    'locus':locus,
                    'match_type':'fuzzy',
                    'confidence': ratio
                }
    return match_info

def match_structure(pdb_code):
    histo_info, success, errors = structureInfo(pdb_code).get()
    step_errors = []
    match_info = None
    # first of all, check if it's actually been assigned as a Class I molecule, some of the steps in this are expensive so we don't want to d
    has_class_i_alpha = check_mhc_class(histo_info, 'class_i')
    if has_class_i_alpha:
        # get the relevant sequence to test, at the moment we're just picking the first one, which may not be optimal
        sequence_to_test = histo_info['chain_assignments']['class_i_alpha']['sequences'][0]
        # the stored sequences are all 275 long, so trim the sequence to match, at some point doing this less bluntly would be better
        if len(sequence_to_test) > 275:
            sequence_to_test = sequence_to_test[0:275]
        # then get testing, first pass tests against the first allele in a group, i.e. A*02:01:01:01 which is often the most common
        match_info = first_pass_sequence_match(sequence_to_test)
        if not match_info:
            # if it doesn't match against the first one, we then run through again against all alleles
            step_errors.append({'error':'first_match_failure', 'pdb_code':pdb_code})
            match_info = second_pass_sequence_match(sequence_to_test)
            if not match_info:
                # if that doesn't match we go for the more expensive option which is a fuzzy match, at the moment this is done against all alleles which is quite slow
                step_errors.append({'error':'second_match_failure', 'pdb_code':pdb_code})
                match_info = third_pass_sequence_match(sequence_to_test)
                if not match_info:
                    step_errors.append({'error':'third_match_failure', 'pdb_code':pdb_code})
        if match_info:
            # if we get a match, we clear the step errors
            step_errors = []
            # and add the match information to the record
            if 'species' in match_info:
                species = match_info['species']
            else:
                species = 'other'
            histo_info, success, errors = structureInfo(pdb_code).put('match_info', match_info)
            # then we add the structure to the relevant sets
            data, success, errors = structureSet('alleles/' + species + '/all').add(pdb_code)
            data, success, errors = structureSet('alleles/' + species + '/'+ match_info['locus'] + '/all').add(pdb_code)
            data, success, errors = structureSet('alleles/' + species + '/'+ match_info['locus'] + '/' + match_info['allele_group'].replace('*','')).add(pdb_code)
            data, success, errors = structureSet('alleles/' + species + '/'+ match_info['locus'] + '/' + match_info['allele'].replace(':','_').replace('*','')).add(pdb_code)
        else:
            # if we don't get a match, we add it to the nomatch set for error checking and more manual matching 
            data, success, errors = structureSet('alleles/nomatch').add(pdb_code)
            step_errors.append({'error':'no_match_possible', 'pdb_code':pdb_code})
    else:
        step_errors.append({'error':'structure_not_assigned_as_class_i', 'pdb_code':pdb_code})
    if len(step_errors) == 0:
        data = {
            'histo_info': histo_info
        }
    else:
        data = None
        success = False
    return data, success, step_errors


def peptide_positions(pdb_code):
    mhc_class = 'class_i'
    step_errors = []
    histo_info, success, errors = structureInfo(pdb_code).get()
    current_assembly = None
    try:
        current_assembly = RCSB().load_structure(pdb_code +'_1', directory='structures/pdb_format/single_assemblies')
    except:
        step_errors.append({'error':'file_not_found', 'pdb_code':pdb_code})

    if current_assembly:
        extension = []
        if histo_info['neighbour_info']:
            for chain in current_assembly.get_chains():
                if chain.id == histo_info['chain_assignments']['class_i_peptide']['chains'][0]:
                    sequence_array = [residue.resname for residue in chain]
                    clean_array = [residue for residue in sequence_array if residue not in hetatms]
                    sequence_array = clean_array
                    peptide_length = len(sequence_array)
                    if 'extension_positions' in histo_info['neighbour_info']:
                        extension_positions = histo_info['neighbour_info']['extension_positions']
                        extension_positions.sort()
                        i = 0
                        for position in extension_positions:
                            extension.append(sequence_array[position - 1])                        
                            i += 1
                        peptide_length -= i
                    if peptide_length >= 8:
                        peptide_lengths, success, errors = filesystem.get('constants/shared/peptide_lengths')
                        peptide_sequence = histo_info['chain_assignments']['class_i_peptide']['sequences'][0]
                        if len(sequence_array) < 20:
                            for peptide_type in peptide_lengths:
                                if peptide_lengths[peptide_type]['length'] == len(sequence_array):
                                    length_name = peptide_type
                                    data, success, errors = structureSet('peptides/' + mhc_class + '/lengths/' + length_name).add(pdb_code)
                        data, success, errors = structureSet('peptides/' + mhc_class + '/sequences/' + peptide_sequence).add(pdb_code)
                        peptide_positions = {
                            'p1':sequence_array[0],
                            'p2':sequence_array[1],                        
                            'p3':sequence_array[2],
                            'pn-2':sequence_array[peptide_length - 3],
                            'pn-1':sequence_array[peptide_length - 2],
                            'pn':sequence_array[peptide_length - 1],
                            'bulge': sequence_array[3:peptide_length - 3],
                            'bulge_length': peptide_length - 6,
                            'extension': extension,
                            'length_name': length_name
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
                
        else:
            step_errors.append({'error':'no_neighbour_info', 'pdb_code':pdb_code})
    if len(step_errors) == 0:
        data = {
            'histo_info': histo_info
        }
    else:
        data = None
        success = False
    return data, success, step_errors





def offset_id(histo_info, chain_type, id):
    if 'chain_offsets' in histo_info:
        if chain_type in histo_info['chain_offsets']:
            if id >= histo_info['chain_offsets'][chain_type]['start_id']:
                revised_id = id + histo_info['chain_offsets'][chain_type]['offset']
                return revised_id
    return id




def peptide_neighbours(pdb_code):
    step_errors = []
    histo_info, success, errors = structureInfo(pdb_code).get()
    is_class_i = check_mhc_class(histo_info, 'class_i')

    current_assembly = None
    try:
        current_assembly = RCSB().load_structure(pdb_code +'_1', directory='structures/pdb_format/single_assemblies')
    except:
        step_errors.append({'error':'file_not_found', 'pdb_code':pdb_code})

    if current_assembly:
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
        else:
            step_errors.append({'error':'structure_not_assigned_as_class_i', 'pdb_code':pdb_code})
    if len(step_errors) == 0:
        data = {
            'histo_info': histo_info
        }
    else:
        data = None
        success = False
    return data, success, step_errors


def extract_peptides(pdb_code):
    step_errors = []
    histo_info, success, errors = structureInfo(pdb_code).get()
    if 'align_info' in histo_info:
        i = 0
        for complex in histo_info['align_info']:
            filename = histo_info['align_info'][complex]['filename']
            try:
                current_complex = RCSB().load_structure(filename.replace('.pdb',''), directory = 'structures/pdb_format/aligned')
                current_complex_peptide = histo_info['chain_assignments']['class_i_peptide']['chains'][i]
                extract_info = extract_peptide(current_complex_peptide, filename, current_complex)
            except:
                step_errors.append({'error':'file_not_found', 'pdb_code':pdb_code})
            i += 1
        data = {
            'histo_info': histo_info
        }
        return data, success, errors
    else:
        step_errors.append({'error':'no_align_info', 'pdb_code':pdb_code})
    if len(step_errors) == 0:
        data = {
            'histo_info': histo_info
        }
    else:
        data = None
        success = False
    return data, success, step_errors



def measure_peptide_angles(pdb_code):
    histo_info, success, errors = structureInfo(pdb_code).get()
    step_errors = []
    if 'align_info' in histo_info:
        angle_info = {}
        i = 1
        for complex in histo_info['align_info']:
            filename = histo_info['align_info'][complex]['filename']
            peptide_filename = filename.split('.pdb')[0] + '_no_het'
            try:
                current_complex = RCSB().load_structure(peptide_filename, directory = 'structures/pdb_format/fragments/peptides')
                peptide_angle_info = generate_peptide_angles(current_complex)
                angle_info[i] = {'peptide': i, 'angles': peptide_angle_info}
            except(FileNotFoundError):
                step_errors.append({'error':'file_not_found', 'filename':filename, 'pdb_code':pdb_code})
            i += 1
        if len(angle_info) > 0:
            histo_info, success, errors = structureInfo(pdb_code).put('peptide_angle_info', angle_info)
        data = {
            'histo_info': histo_info
        }
    else:
        step_errors.append({'error':'no_align_info', 'pdb_code':pdb_code})
    if len(step_errors) == 0:
        data = {
            'histo_info': histo_info
        }
    else:
        data = None
        success = False
    return data, success, step_errors



