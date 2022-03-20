import requests
import json
import boto3
import botocore.config
import logging
FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
if logger.hasHandlers():
    # Logger is already configured, remove all handlers
    logger.handlers = []
logger.setLevel(logging.INFO)

cfg = botocore.config.Config(retries={'max_attempts': 0}, read_timeout=900000, connect_timeout=900000)
LAMBDA_CLIENT = boto3.client('lambda',
                             region_name='ap-northeast-2',
                             aws_access_key_id='AKIAYHHL7L4IP25TWTQQ',
                             aws_secret_access_key='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',
                             config= cfg)

def lambda_get_target_user_info(username):
    try:
        payload = {"function_name": "instagram_username_to_userid"}
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

def get_target_user_info(keyword,search_type, proxy = None, scrapingbee=None):
    if search_type == "hashtag":
        instagram_target_url = f'https://www.instagram.com/explore/tags/{keyword}/?__a=1'
    if search_type == "user":
        instagram_target_url = f'https://www.instagram.com/{keyword}/?__a=1'
    else:
        instagram_target_url = f'https://www.instagram.com/explore/tags/{keyword}/?__a=1'
    try:
        response = send_request(instagram_target_url, search_type, proxy, scrapingbee)
    except:
        return None

    if response:
        response_to_json = json.loads(response.text)
        try:
            pk = response_to_json["graphql"]["user"]["id"]
        except:
            return None
    else:
        return None
    return pk

def send_request(instagram_target_url, search_type,proxy ,scrapingbee=None):
    if search_type == "hashtag" or scrapingbee:
        response = requests.get(
            url="https://app.scrapingbee.com/api/v1/",
            params={
                "api_key": "XAZN5Y277PEU020TOQWCSZL8PXCM3AKBZPXTX67S6ZBO7Y7QXC9WTV0T7O2EK4QRWR0O2I3Z0F0EM92X",
                "url": instagram_target_url,
                "render_js": "false",
            },
            timeout=30
        )
        return response

    if proxy:
        proxy_username = 'sp22064497'
        proxy_password = 'amdc2580!'
        proxy = f"http://user-{proxy_username}-sessionduration-10:{proxy_password}@gate.smartproxy.com:10000"
        response = requests.get(instagram_target_url,proxies={'http': proxy, 'https': proxy})
        return response
    else:
        response = requests.get(instagram_target_url)
        return response
