

def get_aws_config(app):
    if app.config['USE_LOCAL_S3'] == True:
        return {
            'aws_access_key_id':app.config['LOCAL_ACCESS_KEY_ID'],
            'aws_access_secret':app.config['LOCAL_ACCESS_SECRET'],
            'aws_region':app.config['AWS_REGION'],
            's3_url':app.config['LOCAL_S3_URL'],
            'local':True,
            's3_bucket':app.config['S3_BUCKET'] 
        }
    else:
        return {
            'aws_access_key_id':app.config['AWS_ACCESS_KEY_ID'],
            'aws_access_secret':app.config['AWS_ACCESS_SECRET'],
            'aws_region':app.config['AWS_REGION'],
            'local':False,
            's3_bucket':app.config['S3_BUCKET'] 
    }