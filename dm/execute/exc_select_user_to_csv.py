from dm.engine.user import push_influencer_completed
from dm.model import Task
from dm.service.gpi_service import *
from dm.filter.influencer import get_influencer_list_by_task
from src.utils import get_project_root

# a = "모노키니 콘치웨어 비키니 비키니화보 뷰티화보 하이레그 뒷태 헬스녀 요가복 안다르 언더웨어 요가 필라테스 오운완 운동하는여자 수영복 폴댄스 호캉스 호텔 레깅스 등산하는여자 승무원 등산복 엉덩이 협찬"
# s = a.split(" ")
# s = str(s).replace("'","\"")
# print(s)
# #
# input()

def to_csv(total_user_info):
    with open(
            file=f"{project_dir}/dm/result/userid/{task.project.name}_{task.project.start_date.strftime('%Y-%m-%d')}_{task.search_hashtag[0:10]}",
            mode="a+") as f:
        for user_info in total_user_info:
            username = str(user_info["username"])
            userid = str(user_info["userid"])
            profile_url = str(user_info["profile_url"])

            f.writelines(f"{username}\t{userid}\t{profile_url}\n")


if __name__ == "__main__":
    ##1. 프로젝트 이름 설정
    project_name = "hclass_monokini_link"

    ###테스크 조회 하기
    task = get_dm_source.get_source(source_type="task", filename=f"{project_name}")
    task = json.loads(task)
    task = Task(**task)
    finished = True

    project_dir = get_project_root()

    total_user_infos_group = get_influencer_list_by_task(task)

    total_user_id = list(map(lambda group: f'{group[0]["userid"]}\n', total_user_infos_group))
    total_user_info = list(map(lambda group: group[0], total_user_infos_group))

    print(total_user_id)

    print(f"총 {len(total_user_info)} 개의 유저를 찾았습니다.")
    to_csv(total_user_info)


    ###완료됐을 경우
    if finished:
        for group in total_user_infos_group:
            push_influencer_completed(project_name=task.project.name, influencer_completed=group[0]["userid"])