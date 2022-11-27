from dm.model import Task
from dm.service.gpi_service import *
from dm.engine.user import *
from instagrapi import Client
from dm.filter.influencer import get_influencer_list_by_task
from src.utils import get_project_root
from dm.engine import s3_image
from dm.db import model
import threading
from queue import Queue
from dm.engine import gpi

# a = "모노키니 콘치웨어 비키니 비키니화보 뷰티화보 하이레그 뒷태 헬스녀 요가복 안다르 언더웨어 요가 필라테스 오운완 운동하는여자 수영복 폴댄스 호캉스 호텔 레깅스 등산하는여자 승무원 등산복 엉덩이 협찬"
# s = a.split(" ")
# s = str(s).replace("'","\"")
# print(s)
# #
# input()
def job_crawl():

    task: str
    task = jobs.get()
    total_user_info = task.split("\t")
    username = total_user_info[0]
    userid = total_user_info[1]
    profile_url = total_user_info[2]

    if "super" in profile_url:
        gpi.get_user_by_id_gpi("")
    logger.info(f"작업 진행/task:{task}")

    custom_url = s3_image.upload_profile(profile_url=profile_url, profile_key_name=f"hclass_{username}_{userid}")
    USER_CHECKPOINT.update_one({"userid": str(userid)}, {"$set":
        {
            "profile_url": custom_url,
            "image_type": "custom_hclass"
        }})

    jobs.task_done()
    logger.info(f"task_done:{task}")

def run_thread(queue_size):
    for i in range(queue_size):
        worker = threading.Thread(target=job_crawl, daemon=True)
        worker.start()

if __name__ == "__main__":

    ##1. 프로젝트 이름 설정
    project_name = "hclass_monokini_link"

    ###테스크 조회 하기
    task = get_dm_source.get_source(source_type="task", filename=f"{project_name}")
    task = json.loads(task)
    task = Task(**task)

    project_dir = get_project_root()



    ###큐 생성하기
    jobs = Queue()

    with open(file=f"{project_dir}/dm/result/userid/{task.project.name}_{task.project.start_date.strftime('%Y-%m-%d')}_{task.search_hashtag[0:10]}", mode="r") as f:
        user_info_list = f.readlines()
        for user_info in user_info_list:
            jobs.put(user_info)
    run_thread(queue_size)

