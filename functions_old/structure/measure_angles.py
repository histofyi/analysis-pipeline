from Bio import PDB
import logging

structurally_assigned = [5,7,9,24,25,33,34,45,59,62,63,64,65,66,67,68,69,70,72,73,74,75,76,77,78,80,81,84,95,97,99,114,116,123,124,133,139,140,142,143,144,146,147,152,155,156,157,158,159,160,163,164,167,168,171]


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


def generate_cleft_torsion_angles(structure, chain_id):
    structure.atom_to_internal_coordinates()
    angle_info = {}
    for model in structure:
        for chain in model:
            if chain.get_id() == chain_id:
                for residue in chain:
                    if residue.get_id()[1] in structurally_assigned:
                        i = residue.get_id()[1]
                        angle_info[i] = {}
                        angle_info[i]['residue'] = residue.resname
                        #angle_info[i]['omg'] = residue.internal_coord.get_angle('omg')
                        angle_info[i]['chi1'] = residue.internal_coord.get_angle('chi1')
                        angle_info[i]['chi2'] = residue.internal_coord.get_angle('chi2')
                        angle_info[i]['chi3'] = residue.internal_coord.get_angle('chi3')
                        angle_info[i]['chi4'] = residue.internal_coord.get_angle('chi4')
    return angle_info