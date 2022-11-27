from dm.model import Task
from dm.service.gpi_service import *
from dm.engine.user import *
from src.utils import get_project_root
from dm.engine import s3_image
from threading import Thread, Semaphore
import pandas as pd
from dm.engine import gpi

_sem = Semaphore(100)

# a = "모노키니 콘치웨어 비키니 비키니화보 뷰티화보 하이레그 뒷태 헬스녀 요가복 안다르 언더웨어 요가 필라테스 오운완 운동하는여자 수영복 폴댄스 호캉스 호텔 레깅스 등산하는여자 승무원 등산복 엉덩이 협찬"
# s = a.split(" ")
# s = str(s).replace("'","\"")
# print(s)
# #
# input()

def image_upload(userinfo_list):

    _sem.acquire()

    for userinfo in userinfo_list:
        thread_i = userinfo["thread"]
        index = userinfo["index"]
        username = userinfo["username"]
        userid = userinfo["userid"]


        logger.info(f"{thread_i} task_start- index: {index}// {userid}")

        try:
            profile_url = gpi.get_user_profile_by_id_gpi(userid=userid)
        except Exception as e:
            logger.error(f"프로필 가져오기 실패:{e}")
            continue

        if profile_url == None:
            continue

        try:
            custom_url = s3_image.upload_profile(profile_url=profile_url, profile_key_name=f"hclass_{username}_{userid}")

            USER_CHECKPOINT.update_one({"userid": str(userid)}, {"$set":
                {
                    "profile_url": custom_url,
                    "image_type": "custom_hclass"
                }})
        except Exception as e:
            logger.error(e)
            continue

        logger.info(f"{thread_i} task_done- index: {index}// {userid}// {custom_url}")
        # push_influencer_completed(project_name=task.project.name, influencer_completed=userid)
    _sem.release()

if __name__ == "__main__":

    ##1. 프로젝트 이름 설정
    project_name = "hclass_monokini_link"

    ###테스크 조회 하기
    task = get_dm_source.get_source(source_type="task", filename=f"{project_name}")
    task = json.loads(task)
    task = Task(**task)

    project_dir = get_project_root()

    df = pd.read_excel(f"{project_dir}/dm/result/target_influencer_list/hclass_target_100000.xlsx")

    # update influnecer info by threading
    threads = []

    try:
        userinfo_list = []
        for i in df.index:
            userid = df.at[i, "userid"]
            username = df.at[i, "username"]
            profile_url = df.at[i, "profile_url"]
            userinfo = {"thread": f"thread_{int(i/1000)}", "index": i, "userid": userid, "username": username, "profile_url": profile_url}
            userinfo_list.append(userinfo)

            if i%1000 == 0 and i/1000>0:
                threads.append(Thread(target=image_upload, args=[userinfo_list], daemon=True))
                userinfo_list = []

        logger.info(f"{len(threads)}개의 threads 를 생성함")

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

    except Exception as e:
        logger.error(e)
        df.to_excel(f"{project_dir}/dm/result/target_influencer_list/hclass_test_target_100000.xlsx")
    else:
        logger.info("success")
        df.to_excel(f"{project_dir}/dm/result/target_influencer_list/hclass_test_target_100000.xlsx")




