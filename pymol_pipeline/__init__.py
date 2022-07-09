
from flask import Blueprint, current_app, request

from common.providers import httpProvider
from common.decorators import templated
from common.helpers import fetch_constants

from common.models import itemSet


pymol_views = Blueprint('pymol_views', __name__)


def check_file_exists(pdb_code, assembly_id, structure_component, file_format, http):
    exists = False
    try:
        url = f'http://127.0.0.1:8080/structures/downloads/{pdb_code}_{assembly_id}_{structure_component}.cif'
        print (url)
        cif_data = http.get(url, format='txt')
        if cif_data:
                print (f'ALL GOOD {pdb_code}')
                exists = True
        else:
                print (f'404 {pdb_code}')
    except:
            print (f'ERROR {pdb_code}')
    return exists



sizes = {
    'full':{
        'width':2400,
        'height':2200
    },
    'medium':{
        'width':1200,
        'height':1100
    },
    'small':{
        'width':600,
        'height':550
    },
    'thumbnail':{
        'width':240,
        'height':240
    }
}


def get_structures(page_number):
    set_context = 'search_query'
    set_slug = 'class_i_pdbefold_query'
    itemset, success, errors = itemSet(set_slug, set_context).get(page_number=page_number, page_size=100)
    return itemset



@pymol_views.get('/yrb')
@templated('pymol/yrb')
def pymol_yrb():
    http = httpProvider()
    clean_structures = []
    itemset = get_structures(13)
    for pdb_code in itemset['members']:
        if check_file_exists(pdb_code, 1, 'abd', 'cif', http):
            clean_structures.append({'pdb_code':pdb_code})
    return {'structures':clean_structures, 'sizes':sizes}


@pymol_views.get('/cleft/<string:orientation>')
@templated('pymol/cleft')
def pymol_cleft(orientation):
    orientations = {
        'top':{
            'class_i':(\
                0.995811403,    0.028724836,    0.086771332,\
                -0.087024398,    0.007673016,    0.996177554,\
                0.027949072,   -0.999556422,    0.010141926,\
                -0.000007659,   -0.000004176, -150.956878662,\
                -41.813217163,   60.248783112,   63.533638000,\
                149.222396851,  152.691375732,  -20.000000000 ),
            'peptide': (\
                0.995811403,    0.028724836,    0.086771332,\
                -0.087024398,    0.007673016,    0.996177554,\
                0.027949072,   -0.999556422,    0.010141926,\
                -0.000007659,   -0.000004176, -150.956878662,\
                -41.813217163,   60.248783112,   63.533638000,\
                -1795.062377930, 2096.976074219,  -20.000000000 )
        },
        'side': {
            'class_i':(0.999964476,0.001130534,-0.008345760,-0.001050179,0.999953210,0.009623017,0.008356228,-0.009613929,0.999918759,-0.000013337,-0.000001206,-169.672134399,-42.279060364,53.602447510,63.292312622,168.412094116,170.932174683,-20.000000000),
            'peptide':(0.999972939,0.007359593,0.000000000,-0.007359593,0.999972939,0.000000000,0.000000000,0.000000000,1.000000000,-0.000002027,0.000003786,-169.672134399,-42.265258789,53.586551666,61.640075684,158.271789551,181.072418213,-20.000000000)
        }
    }
    http = httpProvider()
    clean_structures = []
    itemset = get_structures(13)
    #itemset = {}
    #itemset['members'] = ['1hhh']
    for pdb_code in itemset['members']:
        if check_file_exists(pdb_code, 1, 'peptide', 'cif', http):
            if check_file_exists(pdb_code, 1, 'abd', 'cif', http):
                clean_structures.append({'pdb_code':pdb_code})
    return {'structures':clean_structures, 'sizes':sizes, 'orientations':orientations, 'orientation':orientation}


@pymol_views.get('/pockets')
@templated('pymol/pockets')
def pymol_pockets():
    http = httpProvider()
    clean_structures = []
    itemset = get_structures(1)
    #itemset = {}
    #itemset['members'] = ['1hhh']
    pockets = {
        "a": {"color":"wheat", "residues":["5","59","63","66","159","163","167","171"]},
        "b": {"color":"lightpink", "residues":["7","9","24","25","33","34","45","60","67","70"]},
        "c": {"color":"palecyan", "residues":["73","74"]},
        "d": {"color":"palegreen", "residues":["99","114","155","156",]},
        "e": {"color":"lightblue", "residues":["97","114","147","152"]},
        "f": {"color":"lightorange", "residues":["77","80","81","84","95","116","123","143","146","147"]}
    }
    pymol_pockets = []
    for pocket in pockets:
        selection_string = ''
        length = len(pockets[pocket]['residues'])
        i = 0
        for residue in pockets[pocket]['residues']:
            if i == length - 1:
                selection_string += f' resi {residue}'
            else:
                selection_string += f' resi {residue},'
            i += 1
        print (selection_string)
        pymol_pockets.append({'letter':pocket.upper(), 'color': pockets[pocket]['color'],'selection':selection_string})
    for pdb_code in itemset['members']:
        if check_file_exists(pdb_code, 1, 'peptide', 'cif', http):
            if check_file_exists(pdb_code, 1, 'abd', 'cif', http):
                clean_structures.append({'pdb_code':pdb_code})
    return {'structures':clean_structures, 'sizes':sizes, 'pockets':pymol_pockets}


@pymol_views.get('/terminii')
@templated('pymol/terminii')
def pymol_terminii():
    http = httpProvider()
    clean_structures = []
    itemset = get_structures(13)
    #itemset = {}
    #itemset['members'] = ['1hhh']
    terminii = {
        "pn": {"color":"pn_col", "residues":["7","59","171"]},
        "p1": {"color":"p1_col", "residues":["159"]},
        "p2": {"color":"p2_col", "residues":["63"]},
        "pc-1": {"color":"pc-1_col", "residues":["147",]},
        "pc": {"color":"pc_col", "residues":["80","84","123","143","146"]}
    }
    groups = []
    for group in terminii:
        selection_string = ''
        length = len(terminii[group]['residues'])
        i = 0
        for residue in terminii[group]['residues']:
            if i == length - 1:
                selection_string += f' resi {residue}'
            else:
                selection_string += f' resi {residue},'
            i += 1
        print (selection_string)
        groups.append({'name':group, 'color': terminii[group]['color'],'selection':selection_string})
    for pdb_code in itemset['members']:
        if check_file_exists(pdb_code, 1, 'peptide', 'cif', http):
            if check_file_exists(pdb_code, 1, 'abd', 'cif', http):
                clean_structures.append({'pdb_code':pdb_code})
    return {'structures':clean_structures, 'sizes':sizes, 'groups':groups}


