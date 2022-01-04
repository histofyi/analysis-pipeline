

def build_s3_constants_key(item, privacy='public', format='json'):
    s3_key = 'constants/{item}.{format}'.format(item=item, format=format)
    return s3_key
