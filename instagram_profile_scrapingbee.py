import requests
import json

def send_request(username, scrapingbee=True):
    response = None
    if scrapingbee:
        response = requests.get(
            url='https://app.scrapingbee.com/api/v1/',
            params={
                'api_key': '1TQRBZRTTWJUZ5R8ZO4GAK5IQ06KJLFO641LWF0KXAKFUBNOJB4FZCCG6VWFQSVKCBK1LYTJ6WCLCTMR',
                'url': f'https://www.instagram.com/{username}/?__a=1&__d=dis',
                'premium_proxy': 'true',
                'country_code': 'us'
            }
        )

    return response

def lambda_handler(event, context):
    username = event["username"]
    try:
        response = send_request(username, scrapingbee=True)
        json_data = json.loads(response.text)
        print(json_data)
        userid = json_data["graphql"]["user"]
        return {
            'statusCode': 200,
            'body': {"user_id":userid}
        }

    except:
        return {
            'statusCode': 400,
            'body': None
        }

s = lambda_handler(event={"username":"faker"} ,context=None)
print(s)