
import boto3
from botocore.client import Config

import json
import logging

class s3Provider():

    client = None
    bucket = None

    def __init__(self, aws_config):
        
        if aws_config['local']:
            self.client = boto3.client('s3',
                endpoint_url=aws_config['s3_url'],
                aws_access_key_id=aws_config['aws_access_key_id'],
                aws_secret_access_key=aws_config['aws_access_secret'],
                config=Config(signature_version='s3v4')
            )
        else:
            self.client = boto3.client('s3',
                aws_access_key_id = aws_config['aws_access_key_id'],
                aws_secret_access_key = aws_config['aws_access_secret']
            )
        self.bucket = aws_config['s3_bucket']


    def get(self, key, data_format='json'):
        try:
            data = self.client.get_object(Bucket=self.bucket, Key=key)['Body'].read()
            if len(data) > 0:
                if data_format == 'json':
                    try:
                        data = json.loads(data)
                        return data, True, []
                    except:
                        return None, False, ['not_json']
                else:
                    return data, True, []
            else:
               return None, False, ['no_data'] 
        except:
            return None, False, ['no_matching_key']


    def put(self, key, contents, data_format='json'):
        if len(contents) > 0:
            if key:
                if data_format == 'json':
                    try:
                        contents = json.dumps(contents)
                    except:
                        return None, False, ['not_json']
                else:
                    contents = contents
                if contents:
                    self.client.put_object(Body=contents, Bucket=self.bucket, Key=key)
                    return contents, True, []
                else:
                    return None, False, ['unable_to_persist_to_s3']
            else:
                return None, False, ['no_key_provided']
        else:
            return None, False, ['no_content_provided']

    
    def update(self, key, contents, data_format='json'):
        if len(contents) > 0:
            if key:
                if data_format == 'json':
                    try:
                        contents = json.dumps(contents)
                    except:
                        return None, False, ['not_json']
                else:
                    contents = contents
                if contents:
                    self.client.put_object(Body=contents, Bucket=self.bucket, Key=key)
                    return contents, True, []
                else:
                    return None, False, ['unable_to_persist_to_s3']
            else:
                return None, False, ['no_key_provided']
        else:
            return None, False, ['no_content_provided']