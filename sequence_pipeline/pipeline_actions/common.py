

def build_s3_sequence_key(item, privacy='public', format='json'):
    s3_key = 'sequences/files/{privacy}/{item}.{format}'.format(privacy=privacy, item=item, format=format)
    return s3_key


