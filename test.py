import requests
import json

def get_raw(username):
    try_num = 0
    while True:
        if try_num > 10:
            return None
        try_num += 1
        print(try_num)
        try:
            response = requests.get(
                url='https://app.scrapingbee.com/api/v1/',
                params={
                    'api_key': '1TQRBZRTTWJUZ5R8ZO4GAK5IQ06KJLFO641LWF0KXAKFUBNOJB4FZCCG6VWFQSVKCBK1LYTJ6WCLCTMR',
                    'url': f'https://www.instagram.com/{username}/?__a=1&__d=dis',
                    'premium_proxy': 'true',
                    'country_code': 'us'
                }
            )
            json_data = json.loads(response.text)["graphql"]["user"]
        except Exception as e:
            print(e)
            continue
        else:
            return json_data

response = get_raw(username="faker")
print(response)