
from functions import pdb
from ..histo import structureInfo


import logging


structurally_assigned = [5,7,9,24,25,33,34,45,59,62,63,64,65,66,67,68,69,70,72,73,74,75,76,77,78,80,81,84,95,97,99,114,116,123,124,133,139,140,142,143,144,146,147,152,155,156,157,158,159,160,163,164,167,168,171]


def generate_flare_file(pdb_code):
    histo_info, success, errors = structureInfo(pdb_code).get()
    flare_info = None
    if 'neighbour_info' in histo_info:
        flare_info = {'edges':[]}
        residue_properties = []
        residue_array = []
        for position in histo_info['neighbour_info']['class_i_peptide']:
            residue = histo_info['neighbour_info']['class_i_peptide'][position]
            name1 = 'P{position_id}-{position_res}'.format(position_id=residue['position'], position_res=residue['residue'])
            residue_properties.append({'nodeName':name1, 'color':'#ff00ff', 'size':.1})
            residue_array.append(name1)
            if len(residue['neighbours']) == 0:
                    row = {'name1':name1,'name2':'none','frames':[0]}
                    flare_info['edges'].append(row)
            else:
                for row in residue['neighbours']:
                    name2 = 'A{position_id}-{position_res}'.format(position_id=row['position'], position_res=row['residue'])     
                    if not name2 in residue_array:
                        if row['position'] < 51:
                            color = '#cc0000'
                        elif row['position'] < 85:
                            color = '#00cc00'
                        elif row['position'] < 138:
                            color = '#cc0000'
                        else:
                            color = '#0000cc'
                        residue_properties.append({'nodeName':name2, 'color':color, 'size':0.1})
                        residue_array.append(name2)
                    row = {'name1':name1,'name2':name2,'frames':[0]}
                    flare_info['edges'].append(row)
        flare_info['tracks'] = [{
            'trackLabel':'Complex',
            'trackProperties':residue_properties
         }]
        flare_info['trees'] = [{
            'treeLabel':'Complex',
            'treePaths':residue_array
        }]
        flare_info['defaults'] = {
            'edgeColor':'rgba(100,100,100,100)',
            'edgeWidth':1
        }
        data = flare_info
        return data, success, errors
    else:
        return None, False, ['no_neighbour_info']


def abd_neighbours(pdb_code):
    histo_info, success, errors = structureInfo(pdb_code).get()

    neighbours = {}
    errors = []
    success = False
    if 'neighbour_info' in histo_info:
        neighbour_info = histo_info['neighbour_info']['class_i_peptide']
        if 'chain_assignments' in histo_info:
            sequence = histo_info['chain_assignments']['class_i_alpha']['sequences'][0]

            if sequence[0:5] not in ['GPHSL', 'GSHSM', 'GFHSL', 'GPHSM', 'GSHSL', 'GSHGF', 'GQHSL', 'MSHSL']:
                logging.warn(sequence[0:5])
                errors.append({'error':'register_shift','pdb_code': pdb_code})
            for position in neighbour_info:
                    for neighbour in neighbour_info[position]['neighbours']:
                        if neighbour['position'] in structurally_assigned:
                            if neighbour['position'] not in neighbours:
                                neighbours[neighbour['position']] = neighbour
                        else:
                            errors.append({'error':'not_in_structurally_assigned','pdb_code': pdb_code, 'position':position})
            success = True
        else:
            errors.append({'error':'no_chain_assignments','pdb_code': pdb_code})
    else:
        errors.append({'error':'no_neighbour_info','pdb_code': pdb_code})
    return neighbours, success, errors





def simplify_angle(angle):
    if angle:
        if angle < 0:
            angle = 360 + angle
        angle = int(angle)
        return angle
    else:
        return None


def peptide_phi_psi(pdb_code, format):
    histo_info, success, errors = structureInfo(pdb_code).get()
    peptide_angle_labels = ['complex_id']
    peptide_angles = []
    if 'peptide_angle_info' in histo_info:
        for peptide in histo_info['peptide_angle_info']:
            this_peptide_angles = ['{pdb_code}_{id}'.format(pdb_code = pdb_code, id = peptide)]
            i = 1
            for position in histo_info['peptide_angle_info'][peptide]['angles']:
                this_position = histo_info['peptide_angle_info'][peptide]['angles'][position]
                phi_label = 'p{position}_phi'.format(position=i)
                psi_label = 'p{position}_psi'.format(position=i)
                phi_angle = simplify_angle(this_position['phi'])
                psi_angle = simplify_angle(this_position['psi'])
                if i == 1:
                    if psi_label not in peptide_angle_labels:
                        peptide_angle_labels.append(psi_label)
                    this_peptide_angles.append(psi_angle)
                elif i == len(histo_info['peptide_angle_info'][peptide]['angles']):
                    if phi_label not in peptide_angle_labels:
                        peptide_angle_labels.append(phi_label)
                    this_peptide_angles.append(phi_angle)
                else:
                    if phi_label not in peptide_angle_labels:
                        peptide_angle_labels.append(phi_label)
                    if psi_label not in peptide_angle_labels:
                        peptide_angle_labels.append(psi_label)
                    this_peptide_angles.append(psi_angle)
                    this_peptide_angles.append(phi_angle)
                i += 1
            peptide_angles.append(this_peptide_angles)
        peptide_angle_data = {
            'row_labels':peptide_angle_labels,
            'data': peptide_angles
        }
        return peptide_angle_data, True, None
    else:
        return None, False, [{'error':'no_angle_info'}]



def abd_sidechain_angles(pdb_code, format):
    histo_info, success, errors = structureInfo(pdb_code).get()
    sidechain_angle_labels = ['complex_id']
    measured_angles = ['chi1','chi2','chi3','chi4']
    less_angles = ['chi1','chi2']
    for position in structurally_assigned:
        for angle in less_angles:
            sidechain_angle_labels.append('c{position}_{angle}'.format(position = position, angle=angle))
    logging.warn(sidechain_angle_labels)
    logging.warn('========')
    sidechain_angles = []
    if 'cleft_angle_info' in histo_info:
        for cleft in histo_info['cleft_angle_info']:
            if cleft == '1':
                logging.warn(cleft)
                logging.warn('========')
                logging.warn(histo_info['cleft_angle_info'][cleft])
                this_cleft_angles = ['{pdb_code}_{id}'.format(pdb_code = pdb_code, id = cleft)]
                logging.warn(this_cleft_angles)
                for position in histo_info['cleft_angle_info'][cleft]['angles']:
                    logging.warn(position)
                    this_position = histo_info['cleft_angle_info'][cleft]['angles'][position]
                    for angle in less_angles:
                        if this_position[angle]:
                            this_angle = round(this_position[angle])
                            if this_angle < 0:
                                this_angle = 360 + this_angle
                        else:
                            this_angle = None
                        this_cleft_angles.append(this_angle)
                    logging.warn(this_cleft_angles)
                sidechain_angles.append(this_cleft_angles)
        sidechain_angle_data = {
            'row_labels':sidechain_angle_labels,
            'data': sidechain_angles
        }
        return sidechain_angle_data, True, None
    else:
        return None, False, [{'error':'no_cleft_angle_info'}]
