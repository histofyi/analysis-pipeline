import json

from Bio.PDB import *
from Bio.SeqUtils import *
import doi 

import logging


from ..providers import httpProvider
from ..providers import filesystemProvider

from ..textanalysis import levenshtein_ratio_and_distance

http = httpProvider()
file = filesystemProvider(None)


class RCSB():

    hetgroups = None
    amino_acids = None
    complexes = None
    peptide_cutoff = None

    def __init__(self):
        self.hetgroups = ['HOH','IOD','PEG','NAG','NA','GOL','EDO','S04','15P','PG4',' NA','FME',' CD','SEP',' CL',' CA', 'SO4','ACT',' MG','Q81',' NI','2LJ','P6G','MAN','FUC',' CO']
        self.amino_acids, success, errors = file.get('constants/shared/amino_acids')
        self.complexes, success, errors = file.get('constants/shared/complexes')
        self.peptide_cutoff = 30


    def fetch(self, pdb_code):
        filepath = 'structures/pdb_format/raw/{pdb_code}'.format(pdb_code = pdb_code)
        pdb_data, success, errors = file.get(filepath, format='pdb')
        if not success:
            url = 'https://files.rcsb.org/download/{pdb_code}.pdb'.format(pdb_code = pdb_code)
            pdb_data = http.get(url, 'txt')
            payload, success, errors = file.put(filepath, pdb_data, format='pdb')
        return pdb_data


    def search(self, query):
        url = 'https://search.rcsb.org/rcsbsearch/v1/query'
        search_content = http.post(url, json.dumps(query), 'json')
        pdb_data = [entry['identifier'].lower() for entry in search_content['result_set']]
        return pdb_data


    def get_info(self, pdb_code):
        filepath = 'structures/pdb_info/{pdb_code}'.format(pdb_code = pdb_code)
        pdb_info, success, errors = file.get(filepath)
        if not success:
            url = 'https://data.rcsb.org/rest/v1/core/entry/{pdb_code}'.format(pdb_code = pdb_code)
            pdb_info = http.get(url, 'json')
            payload, success, errors = file.put(filepath, json.dumps(pdb_info))
        return pdb_info


    def load_structure(self, pdb_code, directory='structures/pdb_format/raw'):
        filepath = '{directory}/{pdb_code}'.format(pdb_code = pdb_code, directory = directory)
        full_filepath = file.build_filepath(filepath,'pdb')
        parser = PDBParser(PERMISSIVE=1)
        structure = parser.get_structure('mhc', full_filepath)
        return structure


    def three_letter_to_one(self, residue):
        if residue.upper() not in self.hetgroups:
            try:
                one_letter = self.amino_acids["natural"]["translations"]["three_letter"][residue.lower()]
            except:
                logging.warn('NEW HET ATOM ' + residue)
                one_letter = 'z'
        else:
            one_letter = 'x'
        return one_letter


    def one_letter_to_three(self, residue):
        if residue.upper() not in ['Z']:
            try:
                three_letter = self.amino_acids["natural"]["translations"]["one_letter"][residue.lower()]
            except:
                logging.warn('UNNATURAL ' + residue)
                three_letter = 'ZZZ'
        else:
            three_letter = 'ZZZ'
        return three_letter



    def chunk_one_letter_sequence(self, sequence, residues_per_line):
        # splits sequence into blocks
        chunked_sequence = []
        length = len(sequence)

        while length > residues_per_line:
            chunked_sequence.append(sequence[0:residues_per_line])
            sequence = sequence[residues_per_line:]
            length = len(sequence)
        chunked_sequence.append(sequence)
        return chunked_sequence


    def suggest_possible_complexes(self, chain_count):
        possible_complexes = {}
        possible_complexes_labels = []
        for item in self.complexes['complexes']:
            if item['chain_count'] == chain_count:
                possible_complexes = item['possible_complexes']
                possible_complexes_labels = [option['label'] for option in item['possible_complexes']]
        return possible_complexes, possible_complexes_labels



    def get_structure_stats(self, structure, assembly_count):
        chainset = {}
        chainlist = [chain.id for chain in structure.get_chains()]
        chains = [chain for chain in structure.get_chains()]
        total_chains = len(chains)
        chain_count = int(total_chains)/int(assembly_count)
        for chain in chains:
            chainset[chain.id] = {
                'sequence':self.get_sequence(chain)
        }   
        return {
            'chainlist': chainlist,
            'total_chains': total_chains,
            'assembly_count': assembly_count,
            'chain_count':chain_count,
            'chainset':chainset
        }


    def get_sequence(self,chain):
        clean_chain_sequence_array = [residue.resname for residue in chain if residue.resname not in self.hetgroups]
        one_letter_sequence_string = ''.join([self.three_letter_to_one(residue).upper() for residue in clean_chain_sequence_array])
        chunked_one_letter_sequence_array = self.chunk_one_letter_sequence(one_letter_sequence_string,80) 
        return {
            'one_letter_sequence_string': one_letter_sequence_string,
            'chunked_one_letter_sequence_array': chunked_one_letter_sequence_array,
            'length': len(one_letter_sequence_string)
        }
            

    def predict_assigned_chains(self, structure, assembly_count):
        # get the basic stats on the structure
        basic_info = self.get_structure_stats(structure, assembly_count)

        # given the number of unique chains, get a set of all the possible complexes
        possible_complexes, possible_complex_labels = self.suggest_possible_complexes(basic_info['chain_count'])

        # initialise some variables
        possible_chains = {}
        chain_assignments = {}
        possible_class = None


        # first generate a set of all possible chain types in all the possible complexes
        for complex in possible_complexes:
            for item in complex:
                if item == 'label':
                    label = complex['label']
                else:
                    if complex[item] not in possible_chains and 'peptide' not in complex[item]:
                        possible_chains[complex[item]] = self.complexes['chains'][complex[item]]


        # then group the alike chains to reduce the computational space
        alike_chains = self.cluster_alike_chains(structure, assembly_count)


        # then start working on the chains within the comples
        for chain in alike_chains:
            current_chain = alike_chains[chain]
            current_chain['id'] = chain
            chain_assigned = False
            # Look for peptide chains, they'll be the easiest to assign as they're short
            if current_chain['lengths'][0] < self.peptide_cutoff:
                if not 'peptide' in chain_assignments:
                    chain_assignments['peptide'] = {'chains':current_chain['chains'],'sequences':current_chain['sequences'],'lengths':current_chain['lengths']}
                    chain_assignments['peptide']['chunked_sequence'] = current_chain['chunked_sequence'][0],
                chain_assignments['peptide']['confidence'] = 1.0
                chain_assigned = True
            else:
                # then iterate through all the possible chains and calculate the Levenshtein ratio for all the possible chains vs the current actual chain
                for possible_chain_label in possible_chains:
                    possible_chain = possible_chains[possible_chain_label]
                    # first check there's an example sequence in the possible chain to compare against. In future this should be an array of sequences
                    if 'example' in possible_chain:
                        if len(possible_chain['example']) > 1:
                            try:
                                ratio, distance = levenshtein_ratio_and_distance(possible_chain['example'], current_chain['sequences'][0])
                            except:
                                ratio = None

                            logging.warn(ratio)
                            if ratio:
                                # next see if the score is above the acceptable distance 
                                if ratio > possible_chain['acceptable_distance']:
                                    if not possible_chain_label in chain_assignments:
                                        # and if this is the case and that chain is not in the assignments already, then add it to them
                                        chain_assignments[possible_chain_label] = {'chains':current_chain['chains'],'sequences':current_chain['sequences'],'lengths':current_chain['lengths']}
                                        chain_assignments[possible_chain_label]['chunked_sequence'] = current_chain['chunked_sequence']                                
                                        chain_assignments[possible_chain_label]['confidence'] = ratio
                                        chain_assignments[possible_chain_label]['label'] = possible_chain_label
                                        chain_assigned = True
                                    # if we see a good match for one of the Class I or Class II chains, we can assign that complex
                                    logging.warn(possible_chain_label)
                                    if 'class_i_' in possible_chain_label:
                                        possible_class = 'class_i'
                                    elif 'class_ii_' in possible_chain_label:
                                        possible_class = 'class_ii'
            # we can now reassign the chain marked as 'peptide' into either a Class I or Class II bound peptide        
            if 'peptide' in chain_assignments and possible_class is not None:
                chain_assignments[possible_class +'_peptide'] = chain_assignments['peptide']
                chain_assignments[possible_class +'_peptide']['label'] = possible_class +'_peptide'
                del chain_assignments['peptide']
            if '_peptide' in chain_assignments and possible_class is not None:
                chain_assignments[possible_class +'_peptide'] = chain_assignments['_peptide']
                chain_assignments[possible_class +'_peptide']['label'] = possible_class +'_peptide'
                del chain_assignments['_peptide']
            if chain_assigned is False:
                chain_assignments['unassigned'] = {'chains':current_chain['chains'],'sequences':current_chain['sequences'],'lengths':current_chain['lengths']}
                chain_assignments['unassigned']['chunked_sequence'] = current_chain['chunked_sequence']


        # next up scoring and assigning the complexes                
        complex_hits = {}

        # iterate through the possible complexes to look for matches
        for complex in possible_complexes:
            score = 0
            itemcount = 0
            matches = []
            for item in complex:
                if item == 'label':
                    label = complex['label']
                else:
                    if '_peptide' == complex[item]:
                        # if there's something marked as a peptide but without a class (as we couldn't assign either alpha or beta chain), it's likely to be a peptide, so we'll add it to the matches so it can be part of the aggregate score
                        score += 1
                        matches.append(complex[item])
                    if complex[item] in chain_assignments:
                        logging.warn(complex[item])
                        # if we find a matching label, we assign the confidence score of the individual chain to be part of an aggregate score
                        score += chain_assignments[complex[item]]['confidence']
                        # add it to the list of chain matches
                        matches.append(complex[item])
                    # and iterate the number of chains
                    itemcount += 1

            # for now, we're going to avoid non-classical assignments as they're a bit more complex        
            if not 'non_classical' in label:
                complex_hits[label] = {
                    'matches':matches,
                    'score':score,
                    'itemcount':itemcount,
                    'confidence':float(score)/float(itemcount)
                }            

        # finally we're looking for the best scoring complex as something to recommend, we're not automatically assigning yet
        # TODO automatically assign for the high confidence matches
        best_score = 0
        best_match = ''
        for item in complex_hits:
            confidence = complex_hits[item]['confidence']
            if confidence > 0.5:
                if confidence > best_score:
                    best_score = confidence
                    best_match = item

        # remove this keyed item as we're not going to be using it
        del basic_info['chainset']

        variables = {
            'chain_assignments':chain_assignments,
            'basic_info':basic_info,
            'best_match': {
                'best_match': best_match,
                'confidence': best_score
            },
            'alike_chains':alike_chains,
            'complex_hits':complex_hits
        }
        return variables




    def cluster_alike_chains(self,structure, assembly_count):
        logging.warn("CLUSTERING ALIKE CHAINS")
        ### Performs a clustering of similar chains (on sequence basis) in the structure ###
        # First get the basic stats on the structure
        structure_stats = self.get_structure_stats(structure, assembly_count)
        logging.warn(structure_stats)
        unique_chain_set = {}
        # if there's only one assembly, then just assign the chains, no clustering needed
        if int(assembly_count) == 1:
            logging.warn("only one assembly")
            i = 1
            for chain in structure_stats['chainset']:
                chainset = {}
                chainset['chains'] = [chain]
                chainset['chunked_sequence'] = structure_stats['chainset'][chain]['sequence']['chunked_one_letter_sequence_array']
                this_sequence = structure_stats['chainset'][chain]['sequence']['one_letter_sequence_string']
                chainset['lengths'] = [len(this_sequence)]
                chainset['sequences'] = [this_sequence]
                unique_chain_set['chain_' + str(i)] = chainset

                i += 1
        else:
            logging.warn("more than one assembly")
            # if more than one assembly we need to start creating clusters of matched chains        
            matched = []
            matches = []
            # we're doing pairwise matches of chains now
            for first_chain in structure_stats['chainset']:
                first_sequence = structure_stats['chainset'][first_chain]['sequence']['one_letter_sequence_string']
                logging.warn(first_chain)
                logging.warn(first_sequence)
                for second_chain in structure_stats['chainset']:
                    # first of all, make sure we're not matching the same chain!
                    if second_chain != first_chain:
                        this_sequence = structure_stats['chainset'][second_chain]['sequence']['one_letter_sequence_string']
                        # reset the found_match variable
                        found_match = False
                        # then checking we're not doing work already done
                        if second_chain not in matched:
                            # first see if the sequences match, this is the most common case and least expensive calculation
                            if this_sequence == first_sequence:
                                logging.warn([first_chain, second_chain])
                                logging.warn('same sequence')
                                found_match = True
                            else:
                                if len(this_sequence) < 20 and len(first_sequence) < 20:
                                    logging.warn('peptides')
                                    ratio, distance = levenshtein_ratio_and_distance(first_sequence, this_sequence)
                                    logging.warn(ratio)
                                    found_match = True
                                else:
                                    # sadly not, then we're going to look and see if the sequences are roughly the same length before we do the more expensive fuzzy matching calculation
                                    if len(this_sequence) > len(first_sequence):
                                        length_score = float(len(first_sequence)) / float(len(this_sequence))
                                    else:
                                        length_score = float(len(this_sequence)) / float(len(first_sequence))
                                    # if they're roughly the same length, calculate the Levenshtein distance/ratio
                                    if length_score > 0.9:
                                        logging.warn([first_chain, second_chain])
                                        logging.warn('length match')
                                        ratio, distance = levenshtein_ratio_and_distance(first_sequence, this_sequence)
                                        if ratio > 0.8:
                                            logging.warn([first_chain, second_chain])
                                            logging.warn('text match')
                                            found_match = True
                            # if through any of these methods we've found a match, we append the items into the relevant sets
                            if found_match:
                                matched.append(first_chain)
                                matched.append(second_chain)
                                for match in matches:
                                    if match:
                                        if first_chain in match:
                                            if second_chain not in match:
                                                match.append(second_chain)              
                                else:
                                    matches.append([first_chain,second_chain])
            correct_matches = []
            for match in matches:
                if len(match) == assembly_count:
                    correct_matches.append(match)
            # now we've found the matches, we can build a dictionary of the matched chains
            unique_chain_set = {}
            i = 1
            for match in correct_matches:
                chainset = {}
                first_match = match[0]
                
                chainset['chains'] = match
                chainset['chunked_sequence'] = structure_stats['chainset'][first_match]['sequence']['chunked_one_letter_sequence_array']
                chainset['lengths'] = []
                chainset['sequences'] = []
                unique_chain_set['chain_' + str(i)] = chainset
                for chain in match:
                    this_sequence = structure_stats['chainset'][chain]['sequence']['one_letter_sequence_string']
                    chainset['sequences'].append(this_sequence)
                    chainset['lengths'].append(len(this_sequence))
                i += 1
        # and finally, return it
        return unique_chain_set


    def generate_basic_information(self, structure, assembly_count):
        logging.warn(assembly_count)
        structure_stats = self.get_structure_stats(structure, assembly_count)
        possible_complexes, possible_complexes_labels = self.suggest_possible_complexes(structure_stats['chain_count'])
        basic_information = {
            "structure_stats":structure_stats,
            "possible_complexes":possible_complexes,
            "possible_complexes_labels": possible_complexes_labels,
        }
        return basic_information


#TODO move resolve_doi, doesn't fit here
    def resolve_doi(self, paper_doi):
        url = doi.get_real_url_from_doi(paper_doi)
        return url


