import urllib3
import json

import logging

http = urllib3.PoolManager()


basepath = '../../../data'



def rcsb_search(mhc_class):
    filename = basepath + '/constants/'+ mhc_class +'_shape_query.json'
    f = open(filename)
    query = json.load(f)

    r = http.request(
        'POST',
        'https://search.rcsb.org/rcsbsearch/v1/query',
        body=json.dumps(query),
        headers={'Content-Type': 'application/json'})

    if r.status == 200:
        search_content = json.loads(r.data.decode('utf-8'))
        logging.warning(search_content)

        download_list = [entry['identifier'].lower() for entry in search_content['result_set']]

        with open(basepath + '/logs/'+ mhc_class + '_search_set.json', 'w') as outfile:
            json.dump(download_list, outfile)

        return download_list, True, None
    else:
        return None, False, 'error'



def rcsb_download(pdb_code, mhc_class):
    url = 'https://files.rcsb.org/download/'+ pdb_code.upper() +'.pdb'
    filepath = basepath + '/structures/'+ mhc_class + '/raw/' + pdb_code +'.pdb'
    logging.warn(url)
    logging.warn(filepath)

    r = http.request('GET', url)
    if r.status == 200:
        pdb_content = r.data.decode('utf-8')
        f = open(filepath, 'w')
        f.write(pdb_content)
        f.close()
        return pdb_content, True, None
    else:
        return None, False, 'error'




def get_download_list(data, structure_list):
    to_download = []
    for pdb_code in data:
        if pdb_code not in structure_list:
            to_download.append(pdb_code)
    return to_download
