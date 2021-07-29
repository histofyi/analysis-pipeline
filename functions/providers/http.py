import requests
import json

import logging



class httpProvider():

    def get(self, url, format, params=None):
        r = requests.get(url)
        if r.status_code == 200:
            if format == 'txt':
                content = r.text
            elif format == 'json':
                content = r.json()
            return content
        else:
            return None


    def post(self, url, payload, format):
        r = requests.post(url, data = payload)
        if r.status_code == 200:
            content = r.json()
            return content
        else:
            return None
