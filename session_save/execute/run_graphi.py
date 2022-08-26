from dm.engine import gpi
import requests

def test():
    access_key = "nTYC9RbjpV8axJ3I9OnKI9Z4QVu7hzrE"
    headers = {"x-access-key": access_key}
    data = {"username": "pelageya_8595", "password": "cre2giwv", "locale": "ko-kr"}
    url = "https://api.lamadava.com/s1/auth/login"
    response = requests.post(url=url, data=data, headers=headers)
    print(response.text)
# res = gpi.login(username="bandntest_11", password="ahfmsek2!")
# print(res)
test()
