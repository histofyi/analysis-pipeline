from turtle import ht, pd
from common.providers import httpProvider



import logging
import json




class PDBeProvider():

    pdb_code = None

    def __init__(self, pdb_code):
        self.pdb_code = pdb_code
        self.url_stem = 'https://www.ebi.ac.uk/pdbe/api/pdb/entry/'

    def fetch(self, route, first_only=True):
        url = f'{self.url_stem}/{route}/{self.pdb_code}'
        results = httpProvider().get(url, format='json')[self.pdb_code]
        if results:
            trimmed_results = results
            if isinstance(results, list):
                if first_only:
                    trimmed_results = results[0]
            return trimmed_results, True, []
        else:
            return {}, False, ['unable_to_fetch']

    def fetch_summary(self):
        return self.fetch('summary')
    

    def fetch_publications(self):
        return self.fetch('publications')

    
    def fetch_experiment(self):
        return self.fetch('experiment')


    def fetch_molecules(self):
        return self.fetch('molecules', first_only=False)


    def fetch_assembly(self):
        return self.fetch('assembly', first_only=False)


    def fetch_files(self):
        return self.fetch('files')


    def fetch_observed_residues_ratio(self):
        return self.fetch('observed_residues_ratio')


    def fetch_file_list(self):
        return self.fetch('files')



