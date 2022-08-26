import requests
params = {"username": "suminzz", "access_key": "BXyHLAbtXtCDNpOWtONErHOHRLbEW5kz"}
response = requests.get(url="https://api.lamadava.com/a1/user", params=params)
print(response.text)