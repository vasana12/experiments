import requests
import json
def get_user_by_id_gpi(userid, proxy=None):
    host, port, mobile_proxy_username, mobile_proxy_password = "95.165.2.49", "7508", "test2711", "dks02lxls8s"
    host, port, mobile_proxy_username, mobile_proxy_password = "142.132.168.249", "59413", "2zqm8xget6", "g0d8o6j3ebizwk2"
    # host, port, mobile_proxy_username, mobile_proxy_password = "resi3.ipb.cloud", "9000", "MrIlCvzYImHc0I3t", "wifi;us;;;;"

    # host, port, mobile_proxy_username = "89.248.167.144", "11157", "218.153.187.124"
    # host, port = "177.53.153.171", "999"
    proxy = f"{mobile_proxy_username}:{mobile_proxy_password}@{host}:{port}"
    proxies = {
        "http": f"http://{proxy}",
        "https": f"http://{proxy}"
    }

    url = "https://www.instagram.com/graphql/query/"
    variables = {
        "user_id": str(53913868020),
        "include_reel": True,
    }

    default_params = {"variables": json.dumps(variables, separators=(",", ":"))}
    default_params["query_hash"] = 'ad99dd9d3646cc3c0dda65debcd266a7'
    params = default_params


    # client.set_proxy(dsn=proxy)
    # print(client.proxy)
    # try:
    #     response = client.user_short_gql(user_id=userid)
    #     userid = response
    # except Exception as e:
    #     print(e)

    print(params)

    response = requests.get(url=url, params=params, proxies= proxies, verify=False)
    print(response.text)

        # if e.__class__.__name__ == UserNotFound.__name__:
        #     raise e
        # elif e.__class__.__name__ == ClientError.__name__:
        #     response = get_user_by_id_lamadava(userid)
        #     userid = response.get("pk")
    return response

s = get_user_by_id_gpi(53913868020)
print(s)