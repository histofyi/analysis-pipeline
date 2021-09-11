
from flask import Blueprint, current_app, request, redirect, make_response, Response


import functions.actions as actions


represenataion_views = Blueprint('represenataion_views', __name__)


representation_actions = {
    'flare': {'action':actions.generate_flare_file},
    'peptide_phipsi': {'action':actions.peptide_phi_psi, 'format':'csv'},
    'peptide_sidechain': {'action':None, 'format':'csv'},
    'abd_sidechain': {'action':actions.abd_sidechain_angles, 'format':'csv'}
}


### Representations ###


def to_csv(array):
    si = StringIO()
    cw = csv.writer(si, quotechar='"')
    cw.writerows(array)
    #output = make_response(si.getvalue())
    return si.getvalue()


@represenataion_views.get('/<string:route>/single/<string:pdb_code>')
def representation_handler(route, pdb_code):
    format = None
    if 'format' in representation_actions[route]:
        format = representation_actions[route]['format']
        data, success, errors = representation_actions[route]['action'](pdb_code, format)
    else:
        data, success, errors = representation_actions[route]['action'](pdb_code)
    if data:
        if not format:
            return json.dumps(data)
        else:
            if format == 'csv':
                flat_array = [data['row_labels']]
                for row in data['data']:
                    flat_array.append(row)
                filename = pdb_code +'_' + route
                return Response(
                    to_csv(flat_array),
                    mimetype='text/csv',
                    headers={'Content-disposition':'attachment; filename={filename}.csv'.format(filename=filename)})
    else:
        return {'erors':errors}


@represenataion_views.get('/<string:route>/set/<path:set_name>')
def set_representation_handler(route, set_name):
    format = None
    structureset, success, errors = lists.structureSet(set_name).get()
    header_row_added = False
    flat_array = []
    labels = []
    for pdb_code in structureset['set']:
        data, success, errors = representation_actions[route]['action'](pdb_code, format)
        logging.warn(data)
        if data:
            if not header_row_added:
                flat_array = [data['row_labels']]
                labels = data['row_labels']
                header_row_added = True
            for row in data['data']:
                if len(row) == len(labels):
                    flat_array.append(row)
    return Response(to_csv(flat_array),
        mimetype='text/csv',
        headers={'Content-disposition':'attachment; filename={filename}.csv'.format(filename=set_name)})
