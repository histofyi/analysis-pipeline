

def build_s3_sequence_key(item, privacy='public', format='json'):
    s3_key = 'sequences/files/{privacy}/{item}.{format}'.format(privacy=privacy, item=item, format=format)
    return s3_key


def trim_class_i_alpha_sequence(sequence):
    # TODO first chop out the signal peptide
    # TODO then cut to length (275)
    trimmed_sequence = str(sequence)[24:299]
    # then chop out the ABD
    abd_sequence = trimmed_sequence[0:180]
    return trimmed_sequence, abd_sequence

def trim_class_ii_alpha_sequence(sequence):
    pass

def trim_class_ii_beta_sequence(sequence):
    pass



def slugify(string):
    return string.replace(' ','_').lower()
