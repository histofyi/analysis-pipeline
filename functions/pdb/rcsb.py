import json

from ..providers import httpProvider

http = httpProvider()

class RCSB():

    def fetch(self, pdb_code):
        url = 'https://files.rcsb.org/download/'+ pdb_code +'.pdb'
        pdb_data = http.get(url, 'txt')
        return pdb_data


    def search(self, query):
        url = 'https://search.rcsb.org/rcsbsearch/v1/query'
        search_content = http.post(url, json.dumps(query), 'json')
        pdb_data = [entry['identifier'].lower() for entry in search_content['result_set']]
        return pdb_data


