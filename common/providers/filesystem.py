import json
import logging

class filesystemProvider():

    basedir = 'constants/files'

    def __init__(self,basedir):
        if basedir is not None:
            self.basedir = basedir


    def build_filepath(self, filename, format):
        filepath = self.basedir +'/' + filename + '.' + format
        return filepath
    

    def get_file_handle(self, filename, format, mode):
        return open(self.build_filepath(filename, format), mode)


    def check_exists(self, filename, format='json'):
        try:
            _file = self.get_file_handle(filename, format, 'r')
            return True
        except:
            return False


    def get(self,filename,format='json'):
        errors = []
        success = False
        data = None
        _file = None
        try:
            _file = self.get_file_handle(filename, format, 'r')
        except:
            errors.append('not_found')
        if _file:
            if format == 'json':
                try:
                    data = json.load(_file)
                    success = True
                except:
                    data = None
            else:
                data = _file.read()
                success = True
        return data, success, errors


    def put(self, filename , payload, format='json'):
        errors = []
        success = False
        data = None
        _file = None
        try:
            _file = self.get_file_handle(filename, format, 'w')
        except:
            _file = self.get_file_handle(filename, format, 'x')
        if _file: 
            success = True
            if payload:
                _file.write(payload)
                _file.close()
            if format == 'json':
                data = json.loads(payload)
            else:     
                data = payload
            return data, True, []   
        else:
            return None, False, ['cannot_get_or_create']
        

