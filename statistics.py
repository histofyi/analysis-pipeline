





@app.get('/statistics/abd_neighbour_positions/single/<string:pdb_code>')
def abd_neighbours_handler(pdb_code):
    data, success, errors = actions.abd_neighbours(pdb_code)
    return data


@app.get('/statistics/abd_neighbour_positions/set/<path:set_name>')
def set_abd_neighbours_handler(set_name):
    neighbours = {}
    step_errors = []
    register_shift_list = []
    no_neighbour_list = []
    structureset, success, errors = lists.structureSet(set_name).get()
    for pdb_code in structureset['set']:
        data, success, errors = actions.abd_neighbours(pdb_code)
        if data:
            for position in data:
                residue = data[position]['residue'] 
                if position not in neighbours:
                    neighbours[position] = {'position':position, 'residues':{}}
                if residue not in neighbours[position]['residues']:
                    neighbours[position]['residues'][residue] = {'examples':[], 'count':0}
                neighbours[position]['residues'][residue]['examples'].append(pdb_code)
                neighbours[position]['residues'][residue]['count'] += 1
        for error in errors:
            step_errors.append(error)
            if error['error'] == 'register_shift':
                register_shift_list.append(pdb_code)
            if error['error'] == 'no_neighbour_info':
                no_neighbour_list.append(pdb_code)

    if len(neighbours) > 0:
        for neighbour in neighbours:
            this_neighbour = neighbours[neighbour]
            for residue in this_neighbour['residues']:
                this_residue = this_neighbour['residues'][residue]
                if this_residue['count'] > 20:
                    this_residue['examples'] = []
            

    return {'neighbours':neighbours, 'errors':{'register_shift_list':register_shift_list, 'no_neighbour_list':no_neighbour_list}}
