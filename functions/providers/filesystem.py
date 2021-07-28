import logging
import json


class filesystemProvider():

    basedir = ''

    def __init__(self,basedir):
        self.basedir = basedir

    def __build_filepath(self, filename, format):
        filepath = self.basedir +'/' + filename + '.' + format
        return filepath
    
    def get_file_handle(self, filename, format, mode):
        return open(self.__build_filepath(filename, format), mode)


    def get(self,filename,format='json'):
        errors = []
        success = True
        data = None
        _file = None
        try:
            _file = self.get_file_handle(filename, format, 'r')
        except:
            errors.append('not_found')
        if _file:
            if format == 'json':
                data = json.load(_file)
                logging.warn(data)
            else:
                data = _file.read()
        return data, success, errors


    def put(self, filename , payload, format='json'):
        errors = []
        success = True
        data = None
        _file = None
        try:
            _file = self.get_file_handle(filename, format, 'r')
        except:
            errors.append('not_found')
        if _file:
            _file.write(payload)
            _file.close()     
            data = payload   
        return data, success, errors

