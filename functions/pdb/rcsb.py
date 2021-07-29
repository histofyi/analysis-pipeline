from functions.providers import filesystem
import json

from Bio.PDB import *
from Bio.SeqUtils import *
import doi 

import logging



from ..providers import httpProvider
from ..providers import filesystemProvider



http = httpProvider()
file = filesystemProvider(None)

class RCSB():

    hetgroups = None

    def __init__(self):
        self.hetgroups = ['HOH','IOD','PEG','NAG','NA','GOL','EDO','S04','15P','PG4',' NA','FME']

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


    def generate_basic_information(self, structure, assembly_count):
        complexes, success, errors = file.get('constants/shared/complexes')
        logging.warn("GENERATING BASIC INFORMATION")
        
        basic_information = {}

        chains = [chain.id for chain in structure.get_chains()]

        structure_stats = {
            'chains': chains,
            'total_chains': len(chains),
            'assembly_count': assembly_count
        }



        structures = []

        chain_count = int(structure_stats['total_chains'])/int(structure_stats['assembly_count'])

        possible_complexes = {}

        for item in complexes['complexes']:
            if item['chain_count'] == chain_count:
                possible_complexes = item
                logging.warn(item)
                logging.warn([option['label'] for option in item['possible_complexes']])

        logging.warn("ASSEMBLY COUNT" + str(assembly_count))

        logging.warn("CHAIN COUNT" + str(chain_count))


        chain_sequence_arrays = [[IUPACData.protein_letters_3to1[residue.resname.title()] for residue in chain if residue.resname not in self.hetgroups] for chain in structure.get_chains()]

        

        for chain_sequence_array in chain_sequence_arrays:
            logging.warn(len(chain_sequence_array))
            logging.warn(chain_sequence_array)



        return basic_information


    def resolve_doi(self, paper_doi):
        url = doi.get_real_url_from_doi(paper_doi)
        return url


