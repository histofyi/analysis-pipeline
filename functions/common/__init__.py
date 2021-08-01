from flask import request
import json

import logging

def request_variables(params, ignore_empty_strings=True):
    if not params:
        params = str(request.form['params'])
        logging.warn(request.form)
        if len(params) > 0:
            params = json.loads(params)
        else:
            params = []
    variables = {}
    logging.warn(params)
    for param in params:
        if request.method == "GET":
            variables[param] = request.args.get(param)
        else:
            try:
                variables[param] = request.form[param]
            except:
                try:
                    variables[param] = request.get_json()[param]
                except:
                    variables[param] = None

        if variables[param] is not None and len(variables[param]) == 0 and ignore_empty_strings is True:
            variables[param] = None
        if variables[param] == 'none':
            variables[param] = None
        if variables[param] == 'on':
            variables[param] = True
        if variables[param] == 'off':
            variables[param] = False
    
    if ignore_empty_strings is True:
        clean_variables = {}
        for param in params:
            if variables[param] is not None:
                clean_variables[param] = variables[param]
        variables = clean_variables

    return variables