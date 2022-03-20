import instabot
from db import m_instagram
import json
import boto3
import botocore.config
cfg = botocore.config.Config(retries={'max_attempts': 0}, read_timeout=900000, connect_timeout=900000)
LAMBDA_CLIENT = boto3.client('lambda',
                             region_name='ap-northeast-2',
                             aws_access_key_id='AKIAYHHL7L4IP25TWTQQ',
                             aws_secret_access_key='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',
                             config = cfg)

payload = {"checkpoint_update_term": 0}
username = "jh84sa86"
hashtag_name = "꽃게탕"
payload.update(username=username,hashtag=hashtag_name)
res = LAMBDA_CLIENT.invoke(FunctionName="user_brief_by_username", InvocationType="RequestResponse", Payload=json.dumps(payload))
print(res)
