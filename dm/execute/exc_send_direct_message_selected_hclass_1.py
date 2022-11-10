from dm.model import Task
from dm.service.gpi_service import *
from dm.engine.user import *
from instagrapi import Client
from dm.filter.influencer import get_influencer_list_by_task
from dm.config import *
# host, port, proxy_username, proxy_password = "mobile.ipb.cloud", "7777", "customer-fydh21628401-asn-20057-sessid-RcPU-sesstime-1", "awR4Sad2t"
# host, port, proxy_username, proxy_password = "resi3.ipb.cloud", "9000", "AX7S3xZk5L9RF1So", "wifi;us;;;;"
# host, port, proxy_username, proxy_password = "resi3.ipb.cloud", "9000", "MrIlCvzYImHc0I3t", "wifi;us;;;;"
proxy = f"http://{proxy_username}:{proxy_password}@{host}:{port}"

project_name = "hclass"

### 1. 소스파일 가져오기
task = get_dm_source.get_source(source_type="task", filename="hclass")
task = json.loads(task)
task = Task(**task)

### 2. 텍스트 가져오기
text = get_dm_source.get_source_message(f"hclass_5.txt")

logger.info(f"소스파일을 가져왔습니다\n-프로젝트:{task.project.name}\n-타겟해시태그: {task.search_hashtag}\n-필터링기준:{task.user_followed_by_gte}\n-디엠내용:{text[0:10]}")

total_user_infos_group = get_influencer_list_by_task(task)
total_user_infos_group = total_user_infos_group[0:1000]
next_account_info = None

client = Client()
client.set_proxy(dsn=proxy)

count_send_message = 0

while True:
    logger.info(f"디엠 발송 시작")
    ## user_infos_list 중 첫번째 리스트를 뽑아서 메세지 발송
    if len(total_user_infos_group) == 0:
        logger.info(f"디엠 발송 완료")
        break

    if count_send_message != 0 and count_send_message%250==0:

        logger.info(f"쉽니다 5분")
        time.sleep(300)
        pass
    target_user_infos = total_user_infos_group.pop(0)
    logger.info(f"target_user_infos:{target_user_infos}")

    try:
        next_account_info = send_message(client, user_infos=target_user_infos, text=text, next_account_info=next_account_info,  proxy=proxy)
        count_send_message+=1
    except Exception as e:
        count_send_message += 1
        if e.__class__.__name__ == AccountException.__name__:
            logger.error(f"{e.__class__.__name__}")
            logger.error(f"simal")
            break
        if e.__class__.__name__ == AccountRetryExcessException.__name__:
            logger.error(f"{e.__class__.__name__}")
            logger.error(f"sibul")

            next_account_info = None
            continue
        else:
            logger.error(f"error:{e}, type(e): {type(e)}")

            next_account_info = None
            continue
    else:
        pass
        # push_influencer_completed(project_name=task.project.name, start_date=task.project.start_date, influencer_completed=target_user_infos)