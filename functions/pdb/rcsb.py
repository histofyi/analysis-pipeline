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
        self.hetgroups = ['HOH','IOD','PEG','NAG','NA','GOL','EDO','S04','15P','PG4',' NA','FME',' CD','SEP',' CL',' CA', 'SO4','ACT',' MG']
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
            #'chunked_one_letter_sequence_array': chunked_one_letter_sequence_array
            'length': len(one_letter_sequence_string)
        }
            

    def predict_assigned_chains(self, structure, assembly_count):
        structure_stats = self.get_structure_stats(structure, assembly_count)
        possible_complexes, possible_complex_labels = self.suggest_possible_complexes(structure_stats['chain_count'])
        possible_chains = {}
        possible_assignments = {}
        for complex in possible_complexes:
            for item in complex:
                if item == 'label':
                    label = complex['label']
                else:
                    if complex[item] not in possible_chains and 'peptide' not in complex[item]:
                        possible_chains[complex[item]] = self.complexes['chains'][complex[item]]

        for chain in structure_stats['chainset']:
            current_chain = structure_stats['chainset'][chain]
            current_chain['id'] = chain

            # Look for peptide chains, they'll be the easiest to assign as they're short
            if current_chain['sequence']['length'] < self.peptide_cutoff:
                if not 'peptide' in possible_assignments:
                    possible_assignments['peptide'] = {'chains':[],'sequences':[],'lengths':[]}
                possible_assignments['peptide']['chains'].append(current_chain['id'])
                possible_assignments['peptide']['sequences'].append(current_chain['sequence']['one_letter_sequence_string'])
                possible_assignments['peptide']['lengths'].append(current_chain['sequence']['length'])
                logging.warn("Chain " + current_chain['id'] + " is likely to be peptide")

            for possible_chain_label in possible_chains:
                possible_chain = possible_chains[possible_chain_label]
                if possible_chain['example']:
                    if len(possible_chain['example']) > 1:
                        ratio, distance = levenshtein_ratio_and_distance(possible_chain['example'], current_chain['sequence']['one_letter_sequence_string'])
                        if ratio > possible_chain['acceptable_distance']:
                            logging.warn("Chain " + current_chain['id'] + " is likely to be " + possible_chain_label)
                            logging.warn(ratio)
                



        variables = {
            'possible_complexes':possible_complexes,
            'possible_assignments':possible_assignments,
            'possible_chains': possible_chains,
            'structure_stats':structure_stats
        }
        return variables



    def generate_basic_information(self, structure, assembly_count):
        logging.warn(structure)        

        structure_stats = self.get_structure_stats(structure, assembly_count)

        
        possible_complexes, possible_complexes_labels = self.suggest_possible_complexes(structure_stats['chain_count'])

        logging.warn("BUILDING CHAIN LABEL SETS")

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


