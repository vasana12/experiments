import random
import time
API_DOMAIN = "i.instagram.com"
API_URL = "https://{domain}/api/v1/".format(domain=API_DOMAIN)

NEW_PASSWORD = "ahfmsek2!"

SIG_KEY_VERSION = "4"
IG_SIG_KEY = "a86109795736d73c9a94172cd9b736917d7d94ca61c9101164894b3f0d43bef4"

REQUEST_HEADERS = {
    "X-IG-App-Locale": "en_US",
    "X-IG-Device-Locale": "en_US",
    "X-Pigeon-Session-Id": "21aa671b-a5f3-4093-8ec2-0c98420675e1",
    "X-Pigeon-Rawclienttime": str(round(time.time() * 1000)),
    "X-IG-Connection-Speed": "-1kbps",
    "X-IG-Bandwidth-Speed-KBPS": str(random.randint(7000, 10000)),
    "X-IG-Bandwidth-TotalBytes-B": str(random.randint(500000, 900000)),
    "X-IG-Bandwidth-TotalTime-MS": str(random.randint(50, 150)),
    "X-IG-Prefetch-Request": "foreground",
    "X-Bloks-Version-Id": "0a3ae4c88248863609c67e278f34af44673cff300bc76add965a9fb036bd3ca3",
    "X-IG-WWW-Claim": "0",
    "X-MID": "XkAyKQABAAHizpYQvHzNeBo4E9nm",
    "X-Bloks-Is-Layout-RTL": "false",
    "X-Bloks-Enable-RenderCore": "false",
    # TODO get the uuid from api_login here
    # "X-IG-Device-ID": "{uuid}",
    # TODO get the device_id from api_login here
    # "X-IG-Android-ID": "{device_id}",
    "X-IG-Connection-Type": "WIFI",
    "X-IG-Capabilities": "3brTvwE=",
    "X-IG-App-ID": "567067343352427",
    "X-IG-App-Startup-Country": "US",
    "Accept-Language": "en-US",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Accept-Encoding": "gzip, deflate",
    "Host": "i.instagram.com",
    "X-FB-HTTP-Engine": "Liger",
    "Connection": "close",
}

PROXY_HOST = 'resi3.ipb.cloud'  # rotating proxy or host
PROXY_PORT = 9000  # port
PROXY_USER = 'AX7S3xZk5L9RF1So'  # username
PROXY_PASS = 'wifi;us;;;;'  # password

# PROXY_HOST = 'residential.ipb.cloud'  # rotating proxy or host
# PROXY_PORT = 7777 # port
# PROXY_USER = 'customer-lsgr20040901-asn-22394-sessid-zmmT-sesstime-1' # username
# PROXY_PASS = 'UG2xaDXxC' # password

#
# PROXY_PASS = 'UG2xaDXxC' # password
#
# PROXY_HOST = 'texas1.thesocialproxy.com'  # rotating proxy or host
# PROXY_PORT = 10000 # port
# PROXY_USER = '5rfpjo4evhm0c8dx' # username
# PROXY_PASS = 'ihzoneqam4p3vt2b' # password


PROXY={
        'http': f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}',
        'https': f'https://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}'
        }