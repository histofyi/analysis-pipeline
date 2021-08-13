import json

import logging

from ..providers import filesystemProvider

file = filesystemProvider(None)



class structureInfo():

    pdb_code = None

    def __init__(self, pdb_code):
        self.pdb_code = pdb_code
        pass


    def build_info_path(self):
        path = 'structures/histo_info/{pdb_code}'.format(pdb_code = self.pdb_code)
        return path


    def get(self):
        structure_info, success, errors = file.get(self.build_info_path())
        if not success:
            structure_info, success, errors = file.put(self.build_info_path(), json.dumps({}))
        return structure_info, success, errors


    def put(self, key, payload):
        structure_info, success, errors = self.get()
        if type(structure_info) == str:
            structure_info = json.loads(structure_info)
        if type(payload) == str:
            payload = json.loads(payload)
        structure_info[key] = payload
        structure_info, success, errors = file.put(self.build_info_path(), json.dumps(structure_info))
        return structure_info, success, errors

    
    def clean(self):
        structure_info, success, errors = self.get()
        clean_record = {}
        keep_keys = ['complex_type','publication']
        for key in structure_info:
            if key in keep_keys:
                clean_record[key] = structure_info[key]
        structure_info, success, errors = file.put(self.build_info_path(), json.dumps(clean_record))
        return structure_info, success, errors





