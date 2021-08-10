from flask import request
import json

from datetime import datetime

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



def slugify(string):
    return string.replace(' ','_').lower()
    

def de_slugify(slug):
    return slug.replace('_',' ').title()


def timesince(start_time):
    delta = datetime.now() - start_time

    # assumption: negative delta values originate from clock
    #             differences on different app server machines
    if delta.total_seconds() < 0:
        return 'a few seconds ago'

    num_years = delta.days // 365
    if num_years > 0:
        return '{} year{} ago'.format(
            *((num_years, 's') if num_years > 1 else (num_years, '')))

    num_weeks = delta.days // 7
    if num_weeks > 0:
        return '{} week{} ago'.format(
            *((num_weeks, 's') if num_weeks > 1 else (num_weeks, '')))

    num_days = delta.days
    if num_days > 0:
        return '{} day{} ago'.format(
            *((num_days, 's') if num_days > 1 else (num_days, '')))

    num_hours = delta.seconds // 3600
    if num_hours > 0:
        return '{} hour{} ago'.format(*((num_hours, 's') if num_hours > 1 else (num_hours, '')))

    num_minutes = delta.seconds // 60
    if num_minutes > 0:
        return '{} minute{} ago'.format(
            *((num_minutes, 's') if num_minutes > 1 else (num_minutes, '')))

    return 'a few seconds ago'