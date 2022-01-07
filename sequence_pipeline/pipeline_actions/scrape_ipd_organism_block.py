from .http import httpProvider
from .common import slugify
from bs4 import BeautifulSoup

import logging
import json

species_url_parts = ['NHP','DLA','FISH','OLA','BoLA','ELA','SLA','RT1','CHICKEN','CLA']


def fetch_ipd_species_set(aws_config, species_url_part):
    url = 'https://www.ebi.ac.uk/ipd/mhc/group/{species_part}/species/'.format(species_part=species_url_part)
    data = httpProvider().get(url, 'txt')
    soup = BeautifulSoup(data, 'html.parser')
    table = soup.table
    header = table.thead
    item_types = []
    for item in header:
        item_types.append(slugify(item.string))

    body = table.tbody
    species = {}
    j = 0
    for row in body:
        i = 0
        for item in row:
            
            if i == 0:
                try:
                    thisspecies = item.a.i.string
                except:
                    thisspecies = 'Unknown' + str(j)
                    j += 1
                if thisspecies is None:
                    thisspecies = 'Unknown' + str(j)
                    j += 1
                if '(' in thisspecies:
                    species_parts = thisspecies.replace(')','').split(' (')
                    species_scientific_name = species_parts[0]
                    species_stem = species_parts[1].lower()
                else:
                    species_scientific_name = thisspecies.lower()
                    species_stem = 'unkn'
                species_slug = slugify(species_scientific_name)
                species[species_slug] = {'class_i':[],'class_ii':[]}
                species[species_slug]['scientific_name'] = species_scientific_name
                species[species_slug]['stem'] = species_stem
            if i == 1:
                species[species_slug]['common_name'] = item.string
            if i == 2 or i == 3:
                for locus in item:
                    if locus is not None:
                        if locus != ', ':
                            if i == 2:
                                if locus.string.lower() not in species[species_slug]['class_i']:
                                    species[species_slug]['class_i'].append(locus.string.lower())
                            else:
                                if locus.string.lower() not in species[species_slug]['class_ii']:
                                    species[species_slug]['class_ii'].append(locus.string.lower())

            i += 1
    return species, True, []


def fetch_ipd_species(aws_config):
    all_species = {}
    for species in species_url_parts:
        data, success, errors = fetch_ipd_species_set(aws_config, species)
        for sub_species in data:
            if  'unknown' in sub_species:
                all_species[sub_species + '_' + species.lower()] = data[sub_species]
            else:
                all_species[sub_species] = data[sub_species]

            
    #return json.dumps(all_species), True, []
    return all_species, True, []
