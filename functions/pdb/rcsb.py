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


    def load_structure(self, pdb_code):
        filepath = 'structures/pdb_format/raw/{pdb_code}'.format(pdb_code = pdb_code)
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
        chain_sequence_array = [residue.resname for residue in chain]
        clean_chain_sequence_array = [residue.resname for residue in chain if residue.resname not in self.hetgroups]
        one_letter_sequence_string = ''.join([self.three_letter_to_one(residue).upper() for residue in clean_chain_sequence_array])
        chunked_one_letter_sequence_array = self.chunk_one_letter_sequence(one_letter_sequence_string,80) 
        return {
            #'chain_sequence_array':chain_sequence_array,
            #'clean_chain_sequence_array': clean_chain_sequence_array,
            'one_letter_sequence_string': one_letter_sequence_string,
            'chunked_one_letter_sequence_array': chunked_one_letter_sequence_array,
            'length': len(one_letter_sequence_string)
        }
            

    def predict_assigned_chains(self, structure, assembly_count):
        # get the basic stats on the structure
        structure_stats = self.get_structure_stats(structure, assembly_count)

        # given the number of unique chains, get a set of all the possible complexes
        possible_complexes, possible_complex_labels = self.suggest_possible_complexes(structure_stats['chain_count'])

        # initialise some variables
        possible_chains = {}
        chain_assignments = {}
        possible_class = ''


        # first generate a set of all possible chain types in all the possible complexes
        for complex in possible_complexes:
            for item in complex:
                if item == 'label':
                    label = complex['label']
                else:
                    if complex[item] not in possible_chains and 'peptide' not in complex[item]:
                        possible_chains[complex[item]] = self.complexes['chains'][complex[item]]


        # then start working on the chains within the comples
        for chain in structure_stats['chainset']:
            current_chain = structure_stats['chainset'][chain]
            current_chain['id'] = chain

            # Look for peptide chains, they'll be the easiest to assign as they're short
            if current_chain['sequence']['length'] < self.peptide_cutoff:
                if not 'peptide' in chain_assignments:
                    chain_assignments['peptide'] = {'chains':[],'sequences':[],'lengths':[]}
                    chain_assignments['peptide']['chunked_sequence'] = current_chain['sequence']['chunked_one_letter_sequence_array'],
                chain_assignments['peptide']['chains'].append(current_chain['id'])
                chain_assignments['peptide']['sequences'].append(current_chain['sequence']['one_letter_sequence_string'])
                chain_assignments['peptide']['chunked_sequence'] = current_chain['sequence']['chunked_one_letter_sequence_array'],
                chain_assignments['peptide']['lengths'].append(current_chain['sequence']['length'])
                chain_assignments['peptide']['confidence'] = 1.0

            # then iterate through all the possible chains and calculate the Levenshtein ratio for all the possible chains vs the current actual chain
            for possible_chain_label in possible_chains:
                possible_chain = possible_chains[possible_chain_label]
                if 'example' in possible_chain:
                    # first check there's an example sequence in the possible chain to compare against. In future this should be an array of sequences
                    if len(possible_chain['example']) > 1:
                        ratio, distance = levenshtein_ratio_and_distance(possible_chain['example'], current_chain['sequence']['one_letter_sequence_string'])
                        # next see if the score is above the acceptable distance 
                        if ratio > possible_chain['acceptable_distance']:
                            if not possible_chain_label in chain_assignments:
                                # and if this is the case and that chain is not in the assignments already, then add it to them
                                chain_assignments[possible_chain_label] = {'chains':[],'sequences':[],'lengths':[]}
                                chain_assignments[possible_chain_label]['chunked_sequence'] = current_chain['sequence']['chunked_one_letter_sequence_array'],
                            chain_assignments[possible_chain_label]['confidence'] = ratio
                            chain_assignments[possible_chain_label]['lengths'].append(current_chain['sequence']['length'])
                            chain_assignments[possible_chain_label]['chains'].append(current_chain['id'])
                            chain_assignments[possible_chain_label]['sequences'].append(current_chain['sequence']['one_letter_sequence_string'])
                            chain_assignments[possible_chain_label]['label'] = possible_chain_label
                            # if we see a good match for one of the Class I or Class II chains, we can assign that complex
                            if 'class_i_' in possible_chain_label:
                                possible_class = 'class_i'
                            elif 'class_ii_' in possible_chain_label:
                                possible_class = 'class_ii'
        # we can now reassign the chain marked as 'peptide' into either a Class I or Class II bound peptide        
        if 'peptide' in chain_assignments:
            chain_assignments[possible_class +'_peptide'] = chain_assignments['peptide']
            chain_assignments[possible_class +'_peptide']['label'] = possible_class +'_peptide'
            del chain_assignments['peptide']

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
                    if complex[item] in chain_assignments:
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

        #unique_chain_set = self.cluster_alike_chains(structure, assembly_count)


        variables = {
            'possible_complexes':possible_complexes,
            'chain_assignments':chain_assignments,
            'structure_stats':structure_stats,
            'best_match': {
                'best_match': best_match,
                'confidence': best_score
            },
            'complex_hits':complex_hits
            #'unique_chain_set':unique_chain_set
        }
        return variables




    def cluster_alike_chains(self,structure, assembly_count):
        structure_stats = self.get_structure_stats(structure, assembly_count)
        unique_chain_set = {}
        logging.warn(assembly_count)
        if int(assembly_count) == 1:
            logging.warn("ONLY ONE ASSEMBLY")
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
            matched = []
            matches = []
            for first_chain in structure_stats['chainset']:
                first_sequence = structure_stats['chainset'][first_chain]['sequence']['one_letter_sequence_string']
                for second_chain in structure_stats['chainset']:
                    if second_chain != first_chain:
                        this_sequence = structure_stats['chainset'][second_chain]['sequence']['one_letter_sequence_string']
                        found_match = False
                        if first_chain not in matched and second_chain not in matched:
                            if this_sequence == first_sequence:
                                found_match = True
                            else:
                                if len(this_sequence) > len(first_sequence):
                                    length_score = float(len(first_sequence)) / float(len(this_sequence))
                                else:
                                    length_score = float(len(this_sequence)) / float(len(first_sequence))
                                if length_score > 0.8:
                                    ratio, distance = levenshtein_ratio_and_distance(first_sequence, this_sequence)
                                    if ratio > 0.9:
                                        found_match = True
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
            unique_chain_set = {}
            i = 1
            for match in matches:
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

        logging.warn(unique_chain_set)
        return unique_chain_set






    def generate_basic_information(self, structure, assembly_count):

        structure_stats = self.get_structure_stats(structure, assembly_count)

        
        possible_complexes, possible_complexes_labels = self.suggest_possible_complexes(structure_stats['chain_count'])


        chain_label_sets = {}

        i = 1

        for chain in structure.get_chains():
            chain_number = 'chain_' + str(i)
            if not chain_number in chain_label_sets:
                chain_label_sets[chain_number] = [chain.id]
            else:
                chain_label_sets[chain_number].append(chain.id)
            if i < structure_stats['chain_count']:
                i += 1
            else:
                i = 1

        chain_sequence_arrays = [[residue.resname for residue in chain if residue.resname not in self.hetgroups] for chain in structure.get_chains()]
        
        i = 0

        unique_chains = []
        unique_chain_sequences = {}
        unique_one_letter_sequences = {}
        unique_chain_lengths = []
        chunked_one_letter_sequences = {}
        chain_lengths = {}
        chain_letters = {}
        while i < structure_stats['chain_count']:
            this_chain_sequence_array = chain_sequence_arrays[i]
            i += 1
            unique_chains.append('chain_' + str(i))
            unique_chain_sequences['chain_' + str(i)] = this_chain_sequence_array
            unique_one_letter_sequences['chain_' + str(i)] = ''.join([self.three_letter_to_one(residue).upper() for residue in this_chain_sequence_array])
            unique_chain_lengths.append(len(this_chain_sequence_array))
            chunked_one_letter_sequences['chain_' + str(i)] = self.chunk_one_letter_sequence(unique_one_letter_sequences['chain_' + str(i)],80) 
            chain_lengths['chain_' + str(i)] = len(this_chain_sequence_array)



        basic_information = {
            "structure_stats":structure_stats,
            "possible_complexes":possible_complexes,
            "possible_complexes_labels": possible_complexes_labels,
            "unique_chain_count": len(unique_chains),
            "chain_lengths":chain_lengths,
            "chain_label_sets":chain_label_sets,
            "chain_sequences":{
                "unique_one_letter_sequences":unique_one_letter_sequences,
                "unique_chains_three_letter":unique_chain_sequences,
                "unique_chain_lengths":unique_chain_lengths,
                "chunked_one_letter_sequences":chunked_one_letter_sequences
            }
        }

        return basic_information


    def resolve_doi(self, paper_doi):
        url = doi.get_real_url_from_doi(paper_doi)
        return url


