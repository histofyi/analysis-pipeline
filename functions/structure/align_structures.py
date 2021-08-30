from functions import pdb
import Bio.PDB
from ..pdb import RCSB
import logging





def align_structure(mhc_class,pdb_code, complex_number, target_chain_id):
    rcsb = RCSB()
    baseline = rcsb.load_structure(mhc_class, directory = 'structures/pdb_format/orientations')
    complex_filename = '{pdb_code}_{complex_number}'.format(pdb_code = pdb_code, complex_number = complex_number)
    if complex_filename:
        target = rcsb.load_structure(complex_filename, directory = 'structures/pdb_format/single_assemblies')
    else:
        target = None
    
    if target is not None:
        start_id = 1
        end_id   = 180
        residues_to_be_aligned = range(start_id, end_id + 1)

        baseline_model = baseline[0]
        target_model = target[0]

        baseline_atoms = []
        target_atoms = []

        baseline_res_ids = []
        baseline_res_aa = []
        target_res_ids = []
        target_res_aa = []

        # Iterate of all chains in the model in order to find all residues
        for baseline_chain in baseline_model:
            if baseline_chain.id == 'A':
                # Iterate of all residues in each model in order to find proper atoms
                for baseline_residues in baseline_chain:
                    # Check if residue number ( .get_id() ) is in the list
                    if baseline_residues.get_id()[1] in residues_to_be_aligned:
                        baseline_res_ids.append(baseline_residues.get_id()[1])
                        baseline_res_aa.append(baseline_residues.resname)
                        # Append CA atom to list
                        baseline_atoms.append(baseline_residues['CA'])


        # Do the same for the target structure
        for target_chain in target_model:
            if target_chain.id == target_chain_id:
                logging.warn(target_chain.id)
                for target_residues in target_chain:
                    if target_residues.get_id()[1] in residues_to_be_aligned:
                        target_res_ids.append(target_residues.get_id()[1])
                        target_res_aa.append(target_residues.resname)
                        target_atoms.append(target_residues['CA'])


        logging.warn(len(baseline_atoms))
        logging.warn(len(target_atoms))
        logging.warn(baseline_res_ids)
        logging.warn(target_res_ids)
        logging.warn(baseline_res_aa)
        logging.warn(target_res_aa)

        rmsd = None
        try:
            super_imposer = Bio.PDB.Superimposer()
            super_imposer.set_atoms(baseline_atoms, target_atoms)
            super_imposer.apply(target_model.get_atoms())
            rmsd = super_imposer.rms
        except Bio.PDB.PDBExceptions.PDBException as e:
            rmsd = False
            errors = str(e).replace(' ','_').lower()

        if rmsd:
            aligned_filename = '{pdb_code}_{complex}.pdb'.format(pdb_code = pdb_code, complex = complex_number)
            aligned_filepath = '../../data/structures/pdb_format/aligned/{filename}'.format(filename = aligned_filename)


            io = Bio.PDB.PDBIO()
            io.set_structure(target) 
            io.save(aligned_filepath)
            errors = None

        return rmsd, errors
    else:
        return False, 'unable_to_load_target'