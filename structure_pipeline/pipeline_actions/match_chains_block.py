from common.providers import s3Provider, awsKeyProvider
from common.helpers import fetch_constants, update_block, slugify, levenshtein_ratio_and_distance

import logging


def build_match_block(allele, locus, match_type, confidence):
    match_info = {
        'allele': allele['allele'],
        'allele_group':allele['allele_group'],
        'locus':locus.upper(),
        'id':allele['id'],
        'match_type':match_type,
        'confidence': confidence
    }
    return match_info



def truncate_class_i_sequence_to_match(sequence_to_match):
    # some sequences start at the position before the first one of the canonical strucutures, chop off the first aa
    if sequence_to_match['start'] == 0:
        this_sequence = sequence_to_match['sequence'][1:]
        start = 1
    # most strucutures start at 1    
    elif sequence_to_match['start'] == 1:
        this_sequence = sequence_to_match['sequence']
        start = 1
    # some are missing the first amino acid
    elif sequence_to_match['start'] == 2:
        this_sequence = sequence_to_match['sequence']
        start = 2
    # some have strange start points, either numbering from the start of the signal peptide, these will need to be renumbered
    # TODO add some more starting sequences
    elif sequence_to_match['start'] > 0 and sequence_to_match['sequence'][:3] in ['GSH','CSH']:
        this_sequence = sequence_to_match['sequence']
        start = 1
    else:
    # catch all
        this_sequence = sequence_to_match['sequence']
        start = 1
    # then chop down to the correct length
    this_sequence = this_sequence[:200]
    sequence = {'start':start,'sequence':this_sequence,'length':len(this_sequence)}
    return sequence


# if the start point of the protein sequence is 2 we need to truncate the start of the sequence we're matching it to
# if the structure sequence is shorter than the sequence we're matching it to, we need to make the sequence we're matching it to shorter
def truncate_test_sequence(sequence, start, length):
    if start == 2:
        sequence = sequence[1:]
    if len(sequence) > length:
        return sequence[:length]
    else:
        return sequence


def perform_exact_match(allele_to_test, structure_sequence):
    # this is where exact matching happens, it's super simple it's a string equality of two strings of amino acids which have been truncated to hopefully the same length.
    # it won't deal with deletions due to disorder (such as the HLA-B*08:01 structures - 1m05, 3skm, 4qrq, 5wmr)
    # first we truncate the test sequence to match the start (and length) of the sequence of the structure
    test_sequence = truncate_test_sequence(allele_to_test['sequence'], structure_sequence['start'], structure_sequence['length'])
    # sometimes in this truncation we end up with a sequence longer than the structure sequence, so we need to truncate that to match
    if len(test_sequence) < len(structure_sequence['sequence']):
        match_sequence = structure_sequence['sequence'][:len(test_sequence)]
    else:
        match_sequence = structure_sequence['sequence']
    # then the equivalence
    if match_sequence == test_sequence:
        return allele_to_test
    else:
        return False


def exact_match(mhc_class, locus, sequence_to_match, first_allele_only=True):
    match = None
    # all of this currently relates to matching MHC class I molecules. 
    # TODO At some point we'll need to add in matching for MHC class II and for TCRs
    if mhc_class == 'class_i':
        # first trim the class I sequence
        sequence = truncate_class_i_sequence_to_match(sequence_to_match)
        # then iterate through allele groups
        for allele_group in locus['sequences']:
            this_allele_set = locus['sequences'][allele_group]
            # to speed the matching we'll look only at the first allele in a group e.g. HLA-A*02:01 as it's often the most common - especially HLA-A*02:01 which is overrepresented in structure database
            if first_allele_only:
                allele = this_allele_set['alleles'][0]
                if perform_exact_match(allele, sequence):
                    match = allele
                    break
            # if there isn't a match for the first allele, we'll go through the process again looking at all alleles
            else:
                for allele in this_allele_set['alleles']:
                    if perform_exact_match(allele, sequence):
                        match = allele
                        break
    return match


def perform_fuzzy_match(allele_to_test, structure_sequence, best_ratio):
    ratio, distance = levenshtein_ratio_and_distance(structure_sequence['sequence'][:200], allele_to_test['sequence'][:200])
    if ratio > 0.97 and ratio > best_ratio:
        best_ratio = ratio
        match = allele_to_test
        best_match = True
    else:
        match = False
        best_match = False
    return match, best_match, best_ratio



def fuzzy_match(mhc_class, locus, sequence_to_match):
    match = None
    best_ratio = 0
    best_group = None
    if mhc_class == 'class_i':
        sequence = sequence_to_match
        for allele_group in locus['sequences']:
            this_allele_set = locus['sequences'][allele_group]
            # run through the first alleles to see if we can find a match
            allele = this_allele_set['alleles'][0]
            this_match, best_match, best_ratio = perform_fuzzy_match(allele, sequence, best_ratio)
            if best_match:
                best_group = allele_group
                match = this_match
        # then we'll run through it again with the specific allelegroup
        if best_group:
            logging.warn("BEST GROUP")
            logging.warn(best_group)
            this_allele_set = locus['sequences'][best_group]
            for allele in this_allele_set['alleles']:
                this_match, best_match, best_ratio = perform_fuzzy_match(allele, sequence, best_ratio)
                if best_match:
                    match = this_match
    return match, best_ratio


def match_chains(pdb_code, aws_config, force=False):
    step_errors = []
    s3 = s3Provider(aws_config)
    chains_to_match = {}
    best_match = None
    allele_match = None
    this_chain = None
    match_key = awsKeyProvider().block_key(pdb_code, 'allele_match', 'info')
    data, success, errors = s3.get(match_key)
    if success:
        allele_match = data
    else:
        core_key = awsKeyProvider().block_key(pdb_code, 'core', 'info')
        data, success, errors = s3.get(core_key)
        organism = slugify(data['organism_scientific'])
        species = fetch_constants('species')
        logging.warn(organism)
        scientific_names = [scientific for scientific in species]
        logging.warn(scientific_names)
        if organism not in scientific_names:
            step_errors.append('no_match_for:'+ organism)
            return None, False, step_errors
        else:
            if organism in ['homo_sapiens','mus_musculus']:
                mhc_class = None
                chains_key = awsKeyProvider().block_key(pdb_code, 'chains', 'info')
                data, success, errors = s3.get(chains_key)
                if success:
                    for chain in data:
                        for this_mhc_class in ['class_i','class_ii']:
                            if this_mhc_class in data[chain]['best_match']:
                                mhc_class = this_mhc_class
                                this_chain = data[chain]['best_match'].replace(mhc_class + '_','')
                                if this_chain in ['alpha','beta']:
                                    chains_to_match[this_chain] = {
                                        'label':this_chain,
                                        'sequence':data[chain]['sequences'][0],
                                        'length':data[chain]['length'],
                                        'start':data[chain]['start'][0]
                                    }
                    if mhc_class and len(chains_to_match) > 0:
                        loci = {}
                        for chain in chains_to_match:
                            this_chain = chains_to_match[chain]
                            if this_chain['length'] < 200:
                                break
                            else:
                                for locus in fetch_constants('loci')[slugify(organism)][mhc_class][chain]:
                                    sequence_key = awsKeyProvider().sequence_key(mhc_class, locus)
                                    sequence_data, success, errors = s3.get(sequence_key)
                                    loci[locus] = sequence_data
                                for this_locus in loci:
                                    best_match = exact_match(mhc_class, loci[this_locus], this_chain)
                                    if best_match:
                                        best_ratio = 1
                                        match_type = 'exact'
                                        step_errors = []
                                        allele_match = build_match_block(best_match, this_locus, match_type, best_ratio)
                                        break
                                    else:
                                        best_match = exact_match(mhc_class, loci[this_locus], this_chain, first_allele_only=False)
                                        if best_match:
                                            best_ratio = 1
                                            match_type = 'exact'
                                            step_errors = []
                                            allele_match = build_match_block(best_match, this_locus, match_type, best_ratio)
                                            break
                                        else:
                                            best_match, best_ratio = fuzzy_match(mhc_class, loci[this_locus], this_chain)
                                            if best_match:
                                                match_type = 'fuzzy'
                                                step_errors = []
                                                allele_match = build_match_block(best_match, this_locus, match_type, best_ratio)
                                                break
                    else:
                        step_errors.append('no_chain_info')
                if not best_match:
                    if 'no_match' not in step_errors:
                        step_errors.append('no_match')
            else:
                step_errors.append('no_loci_yet')
                step_errors.append(organism)
    if step_errors:
        logging.warn('-----')
        logging.warn(pdb_code)
        logging.warn(step_errors)
        logging.warn(this_chain)
        logging.warn('-----')
    else:   
        logging.warn('-----')
        logging.warn(pdb_code)
        logging.warn(allele_match)
        logging.warn('-----')
        match_key = awsKeyProvider().block_key(pdb_code, 'allele_match', 'info')
        s3.put(match_key, allele_match)
        update = {}
        update['locus'] = allele_match['locus']
        update['allele'] = {'mhc_alpha':allele_match['allele']}
        update['allele_group'] = {'mhc_alpha':allele_match['allele_group']}
        data, success, errors = update_block(pdb_code, 'core', 'info', update, aws_config)
    return allele_match, True, step_errors
