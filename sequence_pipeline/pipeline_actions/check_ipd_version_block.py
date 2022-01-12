from .http import httpProvider
from .s3 import s3Provider

from .common import build_s3_sequence_key

from bs4 import BeautifulSoup

import logging
import json


def check_ipd_version(aws_config):
    s3 = s3Provider(aws_config)
    key = build_s3_sequence_key('ipd_versions', format='json')
    previous_version, success, errors = s3.get(key)
    url = 'https://www.ebi.ac.uk/ipd/mhc/version/'
    data = httpProvider().get(url, 'txt')
    soup = BeautifulSoup(data, 'html.parser')
    table = soup.table
    header = table.thead
    item_types = []
    for item in header.tr:
        try:
            item_types.append(item.string.lower())
        except:
            item = None
    body = table.tbody
    versions = []
    j = 0
    for row in body:
        this_version = {}
        i = 0
        for item in row:
            if i < 2:
                this_version[item_types[i]] = item.string
            i+= 1
        versions.append(this_version)
    this_version = {
        'latest_version':versions[0]['version'],
        'latest_version_date':versions[0]['date'],
        'versions': versions
    }
    if previous_version is None:
        s3.put(key, this_version)
    else:
        if previous_version['versions'][0]['version'] != versions[0]['version']:
            s3.put(key, this_version)
            # TODO put in the alert to run the rest of the pipeline
    return this_version, True, []


