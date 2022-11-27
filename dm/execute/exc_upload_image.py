from dm.model import Task
from dm.service.gpi_service import *
from dm.engine.user import *
from src.utils import get_project_root
from dm.engine import s3_image
from dm.engine import gpi
import pandas as pd
import requests

# a = "모노키니 콘치웨어 비키니 비키니화보 뷰티화보 하이레그 뒷태 헬스녀 요가복 안다르 언더웨어 요가 필라테스 오운완 운동하는여자 수영복 폴댄스 호캉스 호텔 레깅스 등산하는여자 승무원 등산복 엉덩이 협찬"
# s = a.split(" ")
# s = str(s).replace("'","\"")
# print(s)
# #
# input()
project_dir = get_project_root()
file = f"{project_dir}/dm/result/target_influencer_list/a1_hclass_100000_monokini_link_2.xlsx"


def to_image_upload(username, userid):
    params = {"username": username, "userid": userid, "profile_upload": True}
    requests.get(url="http://0.0.0.0:8000/user_analyze", params=params)

if __name__ == "__main__":

    ##1. 프로젝트 이름 설정
    project_name = "hclass_monokini_link"


    project_dir = get_project_root()

    df = pd.read_excel(file)

    for idx in df.index[53709:100000]:

        # if idx%15 == 0 and idx/15 > 0:
        #     time.sleep(10)

        username = df.at[idx, "username"]
        userid = df.at[idx, "userid"]

        #
        to_image_upload(username=str(username), userid=str(userid))
        logger.info(f"{idx}// {userid}//{username}")
        time.sleep(0.5)

        # push_influencer_completed(project_name=task.project.name, start_date=task.project.start_date, influencer_completed=userid)
        #
        # # profile_url = gpi.get_user_profile_by_id_gpi(userid=userid)
        # #
        # # custom_url = s3_image.upload_profile(profile_url=profile_url, profile_key_name=f"hclass_{username}_{userid}")
        # # doc = USER_CHECKPOINT.update_one({"userid": str(userid)}, {"$set":
        # #                                                          {
        # #                                                              "profile_url": custom_url,
        # #                                                              "image_type": "custom_hclass"
        # #                                                          }})
        # print(idx, userid, custom_url)




