import json
import toml
import logging



from ..providers import httpProvider
from ..providers import filesystemProvider



http = httpProvider()
file = filesystemProvider(None)

class RCSB():

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


