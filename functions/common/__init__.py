from flask import request
import json

import logging

def request_variables(params, ignore_empty_strings=True):
    if not params:
        params = str(request.form['params'])
        if len(params) > 0:
            params = json.loads(params)
        else:
            params = []
    variables = {}
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
        if variables[param] == 'on':
            variables[param] = True
        if variables[param] == 'off':
            variables[param] = False

    return variables