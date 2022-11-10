from dm.engine.gpi_auth import select_user, login_by_sessionid_v_gpi, login_v_gpi
from dm.engine.exceptions import AccountException, AccountRetryExcessException
from dm import config
from dm.engine.gpi import *
from instagrapi.types import DirectMessage


def infinite_login(client: Client, username, max_messages_per_day, client_name=None, session_id=None):
    while True:
        ##1. 사용할 계정 DB 에서 가져오기
        account_setting_info = select_user(username=None, client_name=client_name, max_messages_per_day=max_messages_per_day)

        if account_setting_info is None:
            logger.error("사용가능한 계정이 없습니다 infinite login 을 종료합니다.")
            raise AccountException

        ##2. 가져온 계정으로 로그인 시도. session 받아오기
        # try:
        #     session_id = account_setting_info["session"]["sessionid"]
        # except:
        #     session_id = None

        if session_id:
            login_session = login_by_sessionid_v_gpi(client, session_id)
        else:
            login_session = login_v_gpi(client, account_setting_info["username"], account_setting_info["password"])


        ##2.1 가져온 계정으로 로그인이 성공한 경우 받아온 session을 return 해준다
        if login_session:
            account_setting_info.update(graph_session=client.sessionid)
            return account_setting_info

        ##2.2 가져온 계정으로 로그인이 실패한 경우 계정을 새로 가져온다.
        else:
            continue

def get_valid_user_ids(user_ids):
    valid_user_ids = []
    for user_id in user_ids:
        try:
            valid_user_id = get_user_by_id_gpi(user_id)
        except Exception as e:
            logger.warning(f"{e}//user_id-{user_id} is not valid_user_id,{e.__class__.__name__}")
            if e.__class__.__name__ == UserNotFound.__name__:
                ITEM_USER_COLLECTION.delete_many(filter={"$or": [{"pk": str(user_id)}, {"pk": int(user_id)}]})
                USER_CHECKPOINT.delete_many(filter={"$or": [{"userid": str(user_id)}, {"userid": int(user_id)}]})
            continue
        else:
            valid_user_ids.append(valid_user_id)
    # user_ids = list(filter(lambda x: get_user_by_id_lamadava(x), user_ids))
    # user_ids = list(filter(lambda x: x is not None, user_ids))
    return valid_user_ids

def send_message(client, user_infos, text, next_account_info=None, proxy=None):
    max_account_retry_num = config.max_account_retry_num
    max_request_retry_num = config.max_request_retry_num
    request_retry_num = 0
    account_retry_num = 0

    ###next_account_info 가 없으면 계정을 가져오기 있으면 해당 계정을 사용한다.

    if not next_account_info:
        account_info = infinite_login(client, username="ikitpro.2u3xp86", max_messages_per_day=config.max_messages_per_day, client_name=None,
                                      session_id=None)
    else:
        account_info = next_account_info

    user_ids = list(map(lambda x: int(x["userid"]), user_infos))
    logger.info(f"user_ids:{user_ids}")
    user_ids = get_valid_user_ids(user_ids=user_ids)

    if len(user_ids) == 0:
        logger.error(f"len(user_ids)==0//{user_ids}")
        return account_info

    ###dummy
    # user_ids = []
    # user_ids.append(33873703194)
    # logger.info(f"get_valid_user_names:{user_infos}/{user_ids}")

    while True:
        sessionid = account_info.get('graph_session')
        username = account_info.get('username')
        password = account_info.get('password')

        ##send message
        try:
            response = client.direct_send(text=text, user_ids=user_ids)
        except Exception as e:
            logger.error(f"response 에러:{e.__class__.__name__},{e}")

            request_retry_num += 1
            ### request 가 max retry 를 초과했을 때 다른 아이디로 로그인 해준다. request_retry_num -> 0 , account_retry_num += 1
            if request_retry_num >= max_request_retry_num:
                logger.error(f"client error:{e}, retry login //request 횟수 초과({request_retry_num}) 다른아이디로 로그인 해줍니다. // account_retry_num :{account_retry_num}")
                request_retry_num = 0
                account_retry_num += 1

                if e.__class__.__name__ == "ChallengeRequired":
                    INSTA_ACCOUNT_OBJ.account_collection.update_one({"username": account_info["username"]},
                                                                    {"$set": {"status": "unavailable"}})
                if account_retry_num >= max_account_retry_num:
                    raise AccountRetryExcessException

                client = Client()
                client.set_proxy(dsn=proxy)
                account_info = infinite_login(client, username=None, max_messages_per_day=config.max_messages_per_day, session_id=None)
                continue
            logger.error(f"client error:{e}, retry request // request_retry_num :{request_retry_num}")
            continue

        ##dm 발송 실패
        try:
            DirectMessage(**response.dict())
        except Exception as e:
            logger.error(f"response 타입 에러:{e.__class__.__name__}")
            request_retry_num += 1
            ### request 가 max retry 를 초과했을 때 다른 아이디로 로그인 해준다. request_retry_num -> 0 , account_retry_num += 1
            if request_retry_num >= max_request_retry_num:
                logger.error(
                    f"client error:{e}, retry login //request 횟수 초과({request_retry_num}) 다른아이디로 로그인 해줍니다. // account_retry_num :{account_retry_num}")
                request_retry_num = 0
                account_retry_num += 1
                if account_retry_num >= max_account_retry_num:
                    raise AccountRetryExcessException

                client = Client()
                client.set_proxy(dsn=proxy)
                account_info = infinite_login(client, username=None, max_messages_per_day=config.max_messages_per_day, session_id=None)
                continue

            logger.error(f"client error:{response}, retry request // request_retry_num :{request_retry_num}")
            continue

        ###dm 발송 성공

        logger.info(
            f"디엠 발송 성공 username:{username} /password:{password}/ sessionid:{sessionid} -> user_info:{user_infos}")

        ###dm 발송량
        INSTA_ACCOUNT_OBJ.account_collection.update_one({"username": account_info["username"]},
                                                        {"$inc": {"usage.dm": 1}})
        account_info["usage"]["dm"] += len(user_ids)

        if account_info["usage"]["dm"] < config.max_messages_per_day:
            next_account_info = account_info
        else:
            INSTA_ACCOUNT_OBJ.account_collection.update_one({"username": account_info["username"]},
                                                            {"$set": {"status": "available"}})
            next_account_info = None

        ###
        return next_account_info

def get_valid_user_ids_by_names(user_name_list):
    valid_user_ids = []
    for username in user_name_list:
        try:
            # user_id = get_user_id_by_db(username)
            # valid_user_id = get_user_by_id_gpi(user_id)

            valid_user_id = get_user_id_by_username_rapid_api(username)

        except Exception as e:
            logger.warning(f"{e}//user_id-{username} is not valid_username,{e.__class__.__name__}")
            if e.__class__.__name__ == UserNotFound.__name__:
                ITEM_USER_COLLECTION.delete_many(filter={"$or": [{"username": str(username)}]})
                USER_CHECKPOINT.delete_many(filter={"$or": [{"username": str(username)}]})
            continue
        else:
            valid_user_ids.append(valid_user_id)
    # user_ids = list(filter(lambda x: get_user_by_id_lamadava(x), user_ids))
    # user_ids = list(filter(lambda x: x is not None, user_ids))
    return valid_user_ids