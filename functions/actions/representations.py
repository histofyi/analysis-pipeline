
from ..histo import structureInfo


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
            'trackLabel':'Peptide',
            'trackProperties':residue_properties
         }]
        flare_info['trees'] = [{
            'treeLabel':'Peptide',
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