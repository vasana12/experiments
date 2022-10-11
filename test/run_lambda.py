import json
import boto3
import botocore.config
cfg = botocore.config.Config(retries={'max_attempts': 0}, read_timeout=900000, connect_timeout=900000)

LAMBDA_CLIENT = boto3.client('lambda',
                             region_name='ap-northeast-2',
                             aws_access_key_id='AKIA4DGUF43FYYPHFNL5',
                             aws_secret_access_key='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',
                             config= cfg)

def lambda_get_target_user_info(username):
    try:
        payload = {"function_name": "mecab_test"}
        payload["username"] = username
        res = LAMBDA_CLIENT.invoke(
            FunctionName=payload["function_name"],
            InvocationType="RequestResponse",  # default : RequestResponse, Event
            Payload=json.dumps(payload))

        json_response = json.loads(res["Payload"].read())
        body = json_response["body"]
    except Exception as e:
        logger.error(f"lambda invoke error : {e} ")
        return None
    return body