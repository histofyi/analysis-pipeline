
from ..histo import structureInfo


import logging

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



def peptide_phi_psi(pdb_code, format):
    histo_info, success, errors = structureInfo(pdb_code).get()
    peptide_angle_labels = []
    peptide_angles = []
    if 'peptide_angle_info' in histo_info:
        for peptide in histo_info['peptide_angle_info']:
            this_peptide_angles = []
            i = 1
            for position in histo_info['peptide_angle_info'][peptide]['angles']:
                this_position = histo_info['peptide_angle_info'][peptide]['angles'][position]
                phi_label = 'p{position}_phi'.format(position=i)
                psi_label = 'p{position}_psi'.format(position=i)
                if i == 1:
                    if psi_label not in peptide_angle_labels:
                        peptide_angle_labels.append(psi_label)
                    this_peptide_angles.append(this_position['psi'])
                elif i == len(histo_info['peptide_angle_info'][peptide]['angles']):
                    if phi_label not in peptide_angle_labels:
                        peptide_angle_labels.append(phi_label)
                    this_peptide_angles.append(this_position['phi'])
                else:
                    if phi_label not in peptide_angle_labels:
                        peptide_angle_labels.append(phi_label)
                    if psi_label not in peptide_angle_labels:
                        peptide_angle_labels.append(psi_label)
                    this_peptide_angles.append(this_position['psi'])
                    this_peptide_angles.append(this_position['phi'])
                i += 1
            peptide_angles.append(this_peptide_angles)
        peptide_angle_data = {
            'row_labels':peptide_angle_labels,
            'data': peptide_angles
        }
        return peptide_angle_data, True, None
    else:
        return None, False, [{'error':'no_angle_info'}]