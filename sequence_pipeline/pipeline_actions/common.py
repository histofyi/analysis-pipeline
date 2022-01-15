from io import StringIO


def build_s3_sequence_key(item, privacy='public', format='json'):
    s3_key = 'sequences/files/{privacy}/{item}.{format}'.format(privacy=privacy, item=item, format=format)
    return s3_key


def build_s3_constants_key(item, privacy='public', format='json'):
    s3_key = 'constants/{item}.{format}'.format(item=item, format=format)
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


def generate_fasta_file_handle(data, format='bytes'):
    if format == 'bytes':
        fasta_file = StringIO(data.decode('utf-8'))
    else:
        fasta_file = StringIO(data)
    return fasta_file
