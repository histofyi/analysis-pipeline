from functions import pdb
import Bio.PDB
import numpy
from ..pdb import RCSB

baseline_pdb_code = '3hla'



def align_structures(pdb_code, complex_number):
    rcsb = RCSB()
    baseline = rcsb.load_structure(baseline_pdb_code)
    complex_filename = '{pdb_code}_{complex_number}'.format(pdb_code = pdb_code, complex_number = complex_number)
    target = rcsb.load_structure(complex_filename, directory = 'structures/pdb_format/single_assemblies')
    seq_str = 'GSHSMRYFFTSVSRPGRGEPRFIAVGYVDDTQFVRFDSDAASQRMEPRAPWIEQEGPEYWDGETRKVKAHSQTHRVDLGTLRGYYNQSEAGSHTVQRMYGCDVGSDWRFLRGYHQYAYDGKDYIALKEDLRSWTAADMAAQTTKHKWEAAHVAEQLRAYLEGTCVEWLRRYLENGKETL'
    use_str = '--HSMRYFFTSVSRPGRGEPRFIAVGYVDDTQFVRFDSDAASQRMEPRAPWIEQEGPEYWDGETRKVKAHSQTHRVDLGTLRGYYNQSEAGSHTVQRMYGCDVGSDWRFLRGYHQYAYDGKDYIALKEDLRSWTAADMAAQTTKHKWEAAHVAEQLRAYLEGTCVEWLRRYLENGKE--'
    #use = [letter<>"-" for letter in use_str]

    baseline_model = baseline[0]
    target_model = target[0]

    baseline_atoms = []
    target_atoms = []
