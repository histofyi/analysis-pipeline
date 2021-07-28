import logging
import json


def filesystem():
    return True



class filesystemProvider():

    basedir = ''

    def __init__(self,basedir):
        self.results = None
        self.errors = []
        self.basedir = basedir

    def __buildfilepath(self, filename, format):
        filepath = self.basedir +'/' + filename + '.' + format
        return filepath
    
    def get(self,filename,format='json'):
        logging.warn(self.__buildfilepath(filename,format))
        return True


