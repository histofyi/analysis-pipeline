from typing import Dict, List, Optional
from flask import request


def request_variables(form:Optional[Dict], params:List=None):
    """
    This function returns the variables from querystrings, form posts and json body posts for either the form dictionary or a list of parameters

    Args:
        form (Dict): a dictionary which describes the form and validation rules (if None a list of variables MUST be provided)
        params (List): a list of variable names. The default is None as it is assumed that a form dictionary is the more common use case

    Returns:
        Dict: a dictionary of variables corresponding to either the form or the list of params from the request
    
    """
    if not params:
        params = [element for element in form['elements']]
    variables = {}
    default_value = None
    for param in params:
        variables[param] = None
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
        if form:
            if variables[param] == form['elements'][param]['null_text']:
                variables[param] = None
        if variables[param] is not None and len(variables[param]) == 0:
            variables[param] = None
        if variables[param] == 'None':
            variables[param] = None
    return variables


def validate_variables(variables, params):
    validated = True
    errors = []
    for variable in variables:
        if variable in params:
            if variables[variable] is None:
                validated = False
                errors.append(variable)
    return validated, errors


