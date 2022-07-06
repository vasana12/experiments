import json
import re
s = {"uuids": {"phone_id": "0ab9a040-0800-476d-a926-a0dfc5dd1a7a", "uuid": "d5c009e6-072e-41ab-8575-7eb1de143e1c", "client_session_id": "77cfbe06-9eb8-41d5-ade0-cd94b96feab2", "advertising_id": "91cb279b-faf4-4876-8550-d0a6fefc76fc", "device_id": "android-c81c2e2c32d7193e"}, "cookie": {"csrftoken": "nhAYZX5N0dMINNVLbTX2B0ZyvLfALXHG", "ds_user_id": "53639318325", "ig_direct_region_hint": "\"NAO\\05453639318325\\0541688195713:01f7098acdd55baabde42a4eca98eca5ef50e747eb5ddefc9cf1cb11a3a238bef948061e\"", "mid": "Yr6erQABAAFqGKvb8eUeur03I9YV", "rur": "\"ODN\\05453639318325\\0541688195720:01f775660958c68ec7a1858d6efe36b659609ee77951c2d5268dafaac25a865788014e92\"", "sessionid": "53639318325%3A5GYC1TIiKCyeUx%3A29%3AAYdiyi-RvXeQrOUfpi9p_RUymvAT58b3_EAkndp6hg"}, "timing_value": {"last_login": 1656659639.0452852, "last_experiments": 1656659639.045418}, "device_settings": {"app_version": "117.0.0.28.123", "android_version": "28", "android_release": "9.0", "dpi": "420dpi", "resolution": "1080x1920", "manufacturer": "OnePlus", "device": "ONEPLUS A3003", "model": "OnePlus3", "cpu": "qcom", "version_code": "180322800"}, "user_agent": "Instagram 117.0.0.28.123 Android (28/9.0; 420dpi; 1080x1920; OnePlus; ONEPLUS A3003; OnePlus3; qcom; en_US; 180322800)"}

info = 'christopher00@dyazo.icu | Ruthpr344s | Mozilla/5.0 (Linux; Android 10; SM-A013F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.92 Mobile Safari/537.36 | IN | [{"domain":".instagram.com","expires":1719564833.398859,"httpOnly":false,"name":"mid","path":"\/","priority":"Medium","sameParty":false,"secure":true,"session":false,"size":31,"sourcePort":443,"sourceScheme":"Secure","value":"YrwTIAABAAGjMDsW7ROa0A_PMbcI"},{"domain":".instagram.com","expires":1719564833.3989229,"httpOnly":true,"name":"ig_did","path":"\/","priority":"Medium","sameParty":false,"secure":true,"session":false,"size":42,"sourcePort":443,"sourceScheme":"Secure","value":"23C74B6E-0115-48DA-9435-85CA87B002A9"},{"domain":".instagram.com","expires":1688028833.398967,"httpOnly":false,"name":"ig_nrcb","path":"\/","priority":"Medium","sameParty":false,"secure":true,"session":false,"size":8,"sourcePort":443,"sourceScheme":"Secure","value":"1"},{"domain":".instagram.com","expires":1664268991.316607,"httpOnly":false,"name":"ds_user_id","path":"\/","priority":"Medium","sameParty":false,"secure":true,"session":false,"size":21,"sourcePort":443,"sourceScheme":"Secure","value":"53873270237"},{"domain":".instagram.com","expires":1688028970.8876619,"httpOnly":true,"name":"sessionid","path":"\/","priority":"Medium","sameParty":false,"secure":true,"session":false,"size":87,"sourcePort":443,"sourceScheme":"Secure","value":"53873270237%3AjWNuXGDbKYiTnX%3A19%3AAYdG5txEP9ohcA48cURDeN9IWYGG7WgxIYSMrzDcDw"},{"domain":".instagram.com","expires":1687942591.3164921,"httpOnly":false,"name":"csrftoken","path":"\/","priority":"Medium","sameParty":false,"secure":true,"session":false,"size":41,"sourcePort":443,"sourceScheme":"Secure","value":"uG6tg4Kp6ZBXp0m1INCeZNM3xeWE76Zm"},{"domain":".instagram.com","expires":1657097787,"httpOnly":false,"name":"dpr","path":"\/","priority":"Medium","sameParty":false,"sameSite":"None","secure":true,"session":false,"size":4,"sourcePort":443,"sourceScheme":"Secure","value":"2"},{"domain":".instagram.com","expires":1719564988.12027,"httpOnly":true,"name":"datr","path":"\/","priority":"Medium","sameParty":false,"sameSite":"None","secure":true,"session":false,"size":28,"sourcePort":443,"sourceScheme":"Secure","value":"tBO8YmWBoL_hebXHNGChap_B"},{"domain":".instagram.com","expires":-1,"httpOnly":true,"name":"rur","path":"\/","priority":"Medium","sameParty":false,"secure":true,"session":true,"size":110,"sourcePort":443,"sourceScheme":"Secure","value":"\"EAG\\05453873270237\\0541688028991:01f7cc98859795230879cb346c3414b8b521e3efa557daa217bc4805c57104e02c6d4f1b\""}]'

username = info.split(" | ")[0]
password = info.split(" | ")[1]
cookies = info.split("| IN |")[1]

cookies = cookies.replace("\\054", "\054")
cookies = cookies.replace('""','"')
cookies = json.loads(cookies)


cookie_info = {}
for cookie in cookies:
    cookie_info[cookie["name"]] = cookie["value"]
print(cookie_info)
    # print(cookie)
# # print(cookies)
# # cookies = dict(cookies)
# """
# "value":"\"EAG\\05453873270237\\0541688028991:01f7cc98859795230879cb346c3414b8b521e3efa557daa217bc4805c57104e02c6d4f1b\""
# """
# text= """
# {"value":"\\"EAG\05453873270237\0541688028991:01f7cc98859795230879cb346c3414b8b521e3efa557daa217bc4805c57104e02c6d4f1b\\""}
# """
# # print(text)
# s= json.loads("""
# {"value": "\\"EAG\05453873270237\0541688028991:01f7cc98859795230879cb346c3414b8b521e3efa557daa217bc4805c57104e02c6d4f1b\\""}
# """)
# print(s)
#
# test = '{"value": "\"sss\""}'
# data = test.replace('"', 'sdf\\')
# print(data)
# data = json.loads(test)
# print(data)





