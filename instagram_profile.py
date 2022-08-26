import requests


params = {
    '__a': '1',
    '__d': 'dis',
}

host, port, mobile_proxy_username, mobile_proxy_password = "residential.ipb.cloud", "7777", "customer-lsgr20040901-cc-US-sessid-oBGP-sesstime-1", "UG2xaDXxC"
proxy = f"http://{mobile_proxy_username}:{mobile_proxy_password}@{host}:{port}"
response = requests.get('https://www.instagram.com/faker/', params=params, proxies={"http":proxy,
                                                                                    "https":proxy})

print(response.text)