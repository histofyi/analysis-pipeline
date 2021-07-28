
import boto3
import json


class s3Provider():

    client = None

    def __init__(self, aws_access_key_id, aws_secret_access_key):
        self.client = boto3.client('s3',
        aws_access_key_id = aws_access_key_id,
        aws_secret_access_key = aws_secret_access_key)


    def get(self, bucket, key, data_format='json'):
        data = self.client.get_object(Bucket=bucket, Key=key)['Body'].read()
        try:
            data = self.client.get_object(Bucket=bucket, Key=key)['Body'].read()
            if len(data) > 0:
                if data_format == 'json':
                    try:
                        data = json.loads(data)
                        return data, True, []
                    except:
                        return None, False, ['not_json']
        except:
            return None, False, ['not_json']


    def put(self, bucket, key, contents, data_format='json'):
        if len(contents) > 0:
            if key:
                if data_format == 'json':
                    try:
                        contents = json.dumps(contents)
                    except:
                        return None, False, ['not_json']
                else:
                    contents = contents
                try:
                    self.client.put_object(Body=contents, Bucket=bucket, Key=key)
                    return contents, True, []
                except:
                    return None, False, ['unable_to_persist_to_s3']
            else:
                return None, False, ['no_key_provided']
        else:
            return None, False, ['no_content_provided']