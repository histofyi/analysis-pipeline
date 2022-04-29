from flask import request
import json

from datetime import datetime

import logging


def de_slugify(slug):
    return slug.replace('_',' ').title()


def timesince(start_time):
    if isinstance(start_time, str):
        start_time = datetime.fromisoformat(start_time)
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


def prettify_json(this_json):
    try:
        return json.dumps(this_json, sort_keys=True, indent=4)
    except:
        return this_json


def get_allele_display_name(match_info):
    if 'hla' in match_info['locus']:
        locus = 'HLA-'
        allele = match_info['allele'][0:7].upper()
        display_name = locus + allele
    if 'h-2' in match_info['locus']:
        locus = match_info['locus'].upper()
        allele = match_info['allele'].title()
        display_name = locus + allele
    return display_name


def describe_complex(histo_info):
    if 'match_info' in histo_info and 'peptide_positions' in histo_info and 'chain_assignments' in histo_info:
        description_block = {
            'allele_name': get_allele_display_name(histo_info['match_info']),
            'peptide_length': histo_info['peptide_positions']['length_name'],
            'peptide_sequence': histo_info['chain_assignments']['class_i_peptide']['sequences'][0],
            'features': '',
            'resolution': histo_info['rcsb_info']['resolution_combined']
        }
    else:
        description_block = None
    return description_block


def return_to(pdb_code):
    return '/structures/information/{pdb_code}'.format(pdb_code=pdb_code)
