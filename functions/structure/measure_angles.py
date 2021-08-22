from Bio import PDB
import logging


def ramachandran_type(residue, next_residue) :
    if residue=='GLY':
        return 'glycine'
    elif residue=='PRO':
        return 'proline'
    elif next_residue is not None and next_residue =='PRO':
        #exlcudes those that are Pro or Gly
        return 'pre_proline'
    else :
        return 'general'

def generate_peptide_angles(structure):
    structure.atom_to_internal_coordinates()
    angle_info = {}
    i = 1
    residue_names = [residue.resname.upper() for residue in structure.get_residues()]
    for residue in structure.get_residues():
        angle_info[i] = {}
        if residue.internal_coord:
            angle_info[i]['position'] = i
            angle_info[i]['residue'] = residue.resname
            angle_info[i]['phi'] = residue.internal_coord.get_angle('phi')
            angle_info[i]['psi'] = residue.internal_coord.get_angle('psi')
            angle_info[i]['omg'] = residue.internal_coord.get_angle('omg')
            angle_info[i]['chi1'] = residue.internal_coord.get_angle('chi1')
            angle_info[i]['chi2'] = residue.internal_coord.get_angle('chi2')
            angle_info[i]['chi3'] = residue.internal_coord.get_angle('chi3')
            angle_info[i]['chi4'] = residue.internal_coord.get_angle('chi4')
            angle_info[i]['cb:ca:c'] = residue.internal_coord.get_angle('CB:CA:C')
            if i < len(residue_names) - 1:
                angle_info[i]['ramachandran_type'] = ramachandran_type(residue_names[i-1], residue_names[i])
            i += 1
    return angle_info