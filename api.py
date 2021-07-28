from flask import Blueprint
import json
import logging

import functions


basepath = '../../../data'


api = Blueprint('api', __name__)

@api.route('/rcsb_search/<path:mhc_class>')
def rscb_search_handler(mhc_class):
    pdb_set, success, errors = functions.rcsb_search(mhc_class)

    f = open(basepath + '/logs/'+ mhc_class + '_structure_list.json')
    structure_list = json.load(f)

    to_download = functions.get_download_list(pdb_set, structure_list)
    response = {'search_count':len(pdb_set), 'to_download_count':len(to_download),'pbd_codes':pdb_set}

    return json.dumps(response)



@api.route('/rcsb_download/<path:mhc_class>/all')
def rcsb_download_all_handler(mhc_class):
    f = open(basepath + '/logs/'+ mhc_class + '_search_set.json')
    pdb_set = json.load(f)
    f = open(basepath + '/logs/'+ mhc_class + '_structure_list.json')
    structure_list = json.load(f)
    response = {'download_count':0, 'messages':[]}
    to_download = functions.get_download_list(pdb_set, structure_list)
    for pdb_code in to_download:
        data, success, errors = functions.rcsb_download(pdb_code, mhc_class)
        if success:
            structure_list.append(pdb_code)
            response['messages'].append({'pdb_code':pdb_code,'downloaded':True})
            response['download_count'] += 1
            logging.warning(pdb_code + ' downloaded successfully')
            f = open(basepath + '/logs/' + mhc_class + '_structure_list.json', 'w')
            f.write(json.dumps(structure_list))
            f.close()
        else:
            logging.warning(pdb_code + ' download failed')
            response['messages'].append({'pdb_code':pdb_code,'downloaded':False})
    return json.dumps(response)



@api.route('/rcsb_download/<path:mhc_class>/<path:pdb_code>')
def rcsb_download_handler(mhc_class, pdb_code):
    data, success, errors = functions.rcsb_download(pdb_code, mhc_class)
    return json.dumps({'pdb_code':pdb_code,'downloaded':success})
