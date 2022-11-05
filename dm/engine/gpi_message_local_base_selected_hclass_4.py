# -*- coding: utf-8 -*-

import json
import math
import sys
import requests
import time
from dm import config
from dm.engine.gpi_auth import login_v_gpi, login_by_sessionid_v_gpi, select_user
from dm.engine.user import user_split, divide_user_infos_list
from instagrapi import Client
from instagrapi.types import User
import logging
from instagrapi.types import DirectMessage
from instagrapi.exceptions import UserNotFound, ClientForbiddenError, ClientError
from db import m_instagram
from db.model import *
from dm.engine import completed_target_influencer
from dm.engine.exceptions import *
from dm.execute.run_select_influencer import get_influnecer_info_by_project, search_influencer_info, \
    get_influnecer_user_id_by_project
from dm.prepare import get_dm_source, get_influencer
from dm.engine.gpi import get_user_id_by_username_rapid_api, get_user_by_id_lamadava, get_user_by_id_gpi, \
    get_user_id_by_db, get_user_by_username_lamadava

FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s %(lineno)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
if logger.hasHandlers():
    # Logger is already configured, remove all handlers
    logger.handlers = []
logger.setLevel(logging.INFO)

host, port, proxy_username, proxy_password = "mobile.ipb.cloud", "7777", "customer-fydh21628401-asn-20057-sessid-RcPU-sesstime-1", "awR4Sad2t"
# host, port, proxy_username, proxy_password = "resi3.ipb.cloud", "9000", "MrIlCvzYImHc0I3t", "wifi;us;;;;"
# host, port, proxy_username, proxy_password = "resi3.ipb.cloud", "9000", "AX7S3xZk5L9RF1So", "wifi;us;;;;"
# host, port, proxy_username, proxy_password = "142.132.164.245", "58090", "huzpgfaxit", "6b0p5ekl9yw8p7d"

proxy = f"http://{proxy_username}:{proxy_password}@{host}:{port}"

max_login_try_num = 2
max_messages_per_day = 200
max_group_size = 30


def infinite_login(client: Client, username, max_messages_per_day, client_name=None, session_id=None, proxy=None):

    while True:
        ##1. 사용할 계정 DB 에서 가져오기
        account_setting_info = select_user(username=username, client_name=client_name, max_messages_per_day=max_messages_per_day)

        if account_setting_info is None:
            logger.error("사용가능한 계정이 없습니다 infinite login 을 종료합니다.")
            raise AccountException

        ##2. 가져온 계정으로 로그인 시도. session 받아오기
        # session_id = account_setting_info["session"]["sessionid"]
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
            valid_user_id = get_user_by_id_gpi(user_id, proxy)
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

def get_valid_user_ids_by_names(user_name_list):
    valid_user_ids = []
    for username in user_name_list:
        try:
            valid_user_id = get_user_by_username_lamadava(username)
            # valid_user_id = get_user_by_id_gpi(user_id, proxy)

            # valid_user_id = get_user_id_by_username_rapid_api(username)
            # valid_user_ids =
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


def send_message(client, user_infos, text, next_account_info=None, project_name=None, proxy=None):
    max_account_retry_num = config.max_account_retry_num
    max_request_retry_num = config.max_request_retry_num
    request_retry_num = 0
    account_retry_num = 0

    ###next_account_info 가 없으면 계정을 가져오기 있으면 해당 계정을 사용한다.

    if not next_account_info:
        account_info = infinite_login(client, username=None, max_messages_per_day=max_messages_per_day, client_name=None,
                                      session_id=None, proxy=proxy)
    else:
        account_info = next_account_info

    user_ids = get_valid_user_ids_by_names(user_name_list=user_infos)
    if len(user_ids) == 0:
        logger.error(f"len(user_ids)==0//{user_ids}")
        return account_info

    ###dummy
    # user_ids = []
    # user_ids.append(33873703194)

    logger.info(f"get_valid_user_names:{user_infos}/{user_ids}")
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
                    raise

                client = Client()
                client.set_proxy(dsn=proxy)
                account_info = infinite_login(client, username=None, max_messages_per_day=max_messages_per_day, session_id=None)
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

                if e.__class__.__name__ == "ChallengeRequired":
                    INSTA_ACCOUNT_OBJ.account_collection.update_one({"username": account_info["username"]},
                                                                    {"$set": {"status": "unavailable"}})
                if account_retry_num >= max_account_retry_num:
                    raise AccountRetryExcessException

                client = Client()
                client.set_proxy(dsn=proxy)
                account_info = infinite_login(client, username=None, max_messages_per_day=max_messages_per_day, session_id=None)
                continue

            logger.error(f"client error:{response}, retry request // request_retry_num :{request_retry_num}")
            continue

        ###dm 발송 성공

        logger.info(
            f"디엠 발송 성공 username:{username} /password:{password}/ sessionid:{sessionid} -> user_info:{user_infos}")

        ###dm 발송량 +
        INSTA_ACCOUNT_OBJ.account_collection.update_one({"username": account_info["username"]},
                                                        {"$inc": {"usage.dm": 1}})
        account_info["usage"]["dm"] += len(user_ids)

        if account_info["usage"]["dm"] < max_messages_per_day:
            next_account_info = account_info
        else:
            INSTA_ACCOUNT_OBJ.account_collection.update_one({"username": account_info["username"]},
                                                            {"$set": {"status": "available"}})
            next_account_info = None

        ###
        completed_target_influencer.push_influencer_completed(project_name=project_name, start_date=project_start_date,
                                                              influencer_completed=user_ids)
        time.sleep(20)
        return next_account_info

def send_total_message(total_user_infos_group, text, project_name=None, proxy=None):
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
            next_account_info = send_message(client, user_infos=target_user_infos, text=text,
                                             next_account_info=next_account_info, project_name=project_name, proxy=proxy)
            count_send_message+=1
            logger.info(f"count_send_message: 총 {count_send_message}개의 DM 발송")

        except Exception as e:
            count_send_message += 1
            if e.__class__.__name__ == AccountException.__name__:
                logger.error(f"{e.__class__.__name__}")
                logger.error(f"simal")
                return
            if e.__class__.__name__ == AccountRetryExcessException.__name__:
                logger.error(f"{e.__class__.__name__}")
                logger.error(f"sibul")

                next_account_info = None
                continue
            else:
                logger.error(f"error:{e}, type(e): {type(e)}")

                next_account_info = None
                continue





if __name__ == "__main__":
    ##project 이름 과 제외할 프로젝트 이름
    project = "hclass_5"

    ##파일이름
    filename = "hclass"
    project_start_date = "2022-11-03"

    text = get_dm_source.get_source_message(f"{project}.txt")
    user_infos_list = user_split("""thedongan_clinic
candy_08240523
taggugsong4
dear.ys_
golf._.jiny
boseo_holic
billiysoo
gdr.academy.jungjastation
vividgolf.official
fairliar_official
joun2362
uppeach_market
tigervintagedm_women
maison_de_physio
over_themoon
mizqz_ceo
jjang6692
_lux__1004__clothes
seon2unni
2.__sarah
from.me_skin
you.you.jin
ji_woo__93
golf_jang.y.j
ok_unni.2014
nanan1717
witty_0.0
zum_3_
long_drive_hong
tori_oh
sarang2_golf
smile____phj
pdo_classic
jeongminjeong9380
suyeon.__.v
minsta__u
minseo_pro
muse_de_weekend
jjua._.ibeauty
thehitacc
lovable_rim
titleist_sinnonhyeon
ann_0_2_
zum._.golf
hahahohohu
hezns
k__e__j__
ririseu588
gotd.official
heez.e
_a_hyeong
sunn.iiiiii
_ji_yoon_
jeonhyojeong5
ubinss
princess._.woo
moniu75_off
156.bin
bboksikdang
hey__elin
s.re___mi
moadhfwiyefi
go_blin_g
itmarketer418
_znnam
ddcxgrd
soheegolfer
moreuneunsa_
eun__kkk
kang_k.k.r
k_seonmiiiiiii
heng2ya
swing_like_pro
rarra_aran
rehankhan2471
ggeul___
gimuju32
p_j.hwan
pui_joy
tell_me_2022
sjanrnl
leepro_golf_
isuhyeon4555
asd_dodo_12023
layla__avid_golfer
just_line_official
haluna._.log
euddeume_
inside_g1986
mknjew448
agsanho33
style119pick
golf_rini
duduunnii
hohane6175
ksae__k
uding_01
team_turtlelat_official
founfrz4
st.christopher_worldwide
again_20sal
pigjina___
sj___219
daonraon22
m_e____e
hyekyung8
luv_enmi
golf_bbu
wooyunheebom
jiyoon.love_you
sarange234
wonhee_hong
jj0303jj
yena0405
soniamitchell889
powergolf_p
som__pro
hyejin.k____0613
my_golf_diary
mimirang_official
miko__unni
bonbondivers_niya
h.naa.x_x
melheevv
te_doyeon
styleooo
yuta861030
vitamin.ssu
jjung_31
hada_sj
lovely_olivia00
jazzzzzeee
beanpole.golf
inaheeme
seo.eun.eee
_r_a_n
xelloss1096
inos.vip_kr
jenny_golf_life
sallychoi_golf
hye.__.luv
vintageby102
secondoor_official
mynameis_nari
realgolfcoach
nyang_lim
momob0125
1214_90
standrews.kr
swingbook_company
cherryhanee
daizy__o
iamkim_golf
black_gin___
fnlfm00
hhilwo
helloangelato
saranghye_bin
thesethbqo3
long_drive_hong
seung_chan_l
eung_1030
rammi_golf
irinayoga_
gdr_academy_hsnd
dubu_eumma
adelio.official_
blingyuri39
kimgolf_2022
zenihome
lizh36
poo_ung
yyongreen
nandananda82
yeonjin1983
_ss0yeon_
pippin_jelly
baghyeonggi418
eugenelee0313
libe_golf
vseoprov
golf.choe
senseissue
mluy_golf
aura_company_ceo
pearlp_art
rongcho_v
gdr_academy_wonju
seung.lee06
yyezzinni
lili.sjkwon
ahrum._.97
golf_jamjam2
kty567hgt
izakaya_writer
kate_daily_golf
anewgolf_aksuwon
jiangai_ii
j_east_jade
hyejune2
eoqkr1112
vkhdfd
sebin.bae77
gdr_academy_centerfield
youjin_happy_
5.14mm
shine_sooyeon
marry_h2h2
wonyoung102
bogey_parpar
daphne__song
2garden_
citeezon_jc
daeun7726
renoma_munjeong
angela_ko_ko
golf_nyong
woiaeuzvf_n
sssoyeon88
golf_c0uple_
birdinny_
95._.0202
golf_yuul
hyeseong_golf
yyuunn_p
oh_jt1111
challenger_korea
bibisister_j
welcome_hoem
luxsister_78
shunshun13yao88
j.tennis_
sjeuro
j__eun9
eunchae_yoon
shingle_bangle_s2
yoo_chang2
jiwon_u_
luv_jjang.s.k
eun.ouo
grace__hur
s_jiiiny
luv.__.erish
georyang_company
laboommup
duvik.official
richs_mol
kimhoiu88
aaaaaaam426
kcsi0508
busankl_23
luvjenniie
sul__________p
limvely_a
efcds_ef
moniquegolf_official
lydiaflower_cheongdam
h_golfcouple
yooniring_
ssaalove1219
golf_newg
yeon_long_e
songha.sky
daseul_ii
betty_lmh
sso_golf
gollovexxu
minj2_1114
__365__ing
rodellia.lee
k.river.j
asz_55t
theadress.co.kr
intodh
rara_m_00
michelle9161
briller_jh_
evendoz.kr
gimjeongnam167
1031oz
_wowju
attractionmy
gfdhgfb20
uriburijie
ran_core_
golf.latinjinny
danii_golf
ddongmini0409
prst_an155
lixiny0808
boo_and_boo__
forzadaisy
mypilapose
wjddk_s
hhh_llleee
jin_yeong_life
heohyebin920
muse_j
lady9_golf
jienie_pila
jajububu._.80
bijou_verte
seoanaseoana
blair.kim90
sirizzing_golf
do__00094
traveling_seu_l
yooju.choi
high_mood____
joyjoy.lee
golketer
hwangmijeong8436
madamegreen_golf
jjunpro15
leejieon79
sanami607
_luxwiz_jewelry
chaerinpark_
jlgolf_one
brandnew1004_
comfit_wo
pxm._.649
hfiewug8
dony_.kim
choijiwon83
pxg_ulsan
fabricwld
staypilates
yeruriii
_made.b
yejingolf
h_a__jjang
etuntune
d_du_9
heez.e
daily.caddie
wjdsud_53
jo_oyeon99
aldlwn1naver.com_
edfjdhgds52
bongseondaek
we.l0ve.golf
rrrrrrrrrrrhing
liberta_official.jp
junfur.official
100bum
dlttefvd
heemin1112
star.love.golf
gimseoa_
lllove._4
birdie_soyoon
jjuyerini
wonee_0610
wiisdom_sports
daniel_parkic_
dain__cha
iran77766
na_eun5555
eunjungram
pitch.and.run
store_monsterg
ddanggu._.sis_8
wjm0508
gearantan
gahui.kang
jennalovesgolf
jeonmarie_
heejung100986
truck_8989
yangyeseung
umost_l_u_x
yser_dur143
zzirong_g
rim2_golf
sellermill
sua__su
s_nnninn
umostlux54
sejin_golf_academy
u_most_lux__
17sunny17
kwakhamoly
fantom_sports
jhookim_
junkang0330
daepocha_9623_2266
s.insolence
dajeongmemory
hongsuyeon81
kkkkzhhhs
riwon.vely
shashot.official
oklm.golf
u_most_lux_
lydia_hwang_
sy_dazzle83
_fluke.j
luvbomiri
dfdef78787
healthboy53
theonly_____jy
mareqing3
am0102am
chaeha_kim_
bailywhite_golf
debelle_jihae
0310____eun
wonsiy_un
ateliermong
dong.baegwinnergolf
korea_lelsure_partners
cocoa__golf
_znnam
yerinl
eeez.l
winsome_hyun_
woonae_golf
zxzxhyn
recess.beauty
flowshopkr
luv.atti
leesuroom_golf
younbly_monica
shanghai_golfistar
_a_hyeong
qajdsgh0
dlstjd__7
pinkerbelle___
artttree97
yo_oy.j
_bailywhite
born_to_golf_
loving_catcat
ballic_annajo
anew_golf_
amazingcre____ulsan
eun_gongju
vv_lovemind_vv
jina_life__golf
dae6queen
anjian94___
dlstjd__2
90._.minju
lindachae.realtor
allysia_85
kossen_sou
hys_ny
jinddoing
dr_ko_eun_lee
lovely_golfer0321
anewgolf_cheonan
golf.fashion.sg
sunah_golf
umji_a
ohohgolf
lee_soso_11
gdr_academy_shsc
the_pianistmusic
coedonghan13
mareqing5
biniyang
luv_yoa.dnkg
myungjae.shin
since19820719
golfernamoni
hiitsselina
shu__jing_
hyosim7699
asd_asd1726
sssssswon
peachbong
gogaram41
chaee._.vely
parksuhyeon1028
s.m.s.c
yamcebol
jql_sports
imaginie__
claire___ciel_k
inside_g1986
gdr_academy_gsgy
jjunjjun_mommy
jjo_arrrra
dlstyjd__22
insung__700
seul0418
seo24__
hwang_bbong
golfrano
sj.workout_
lovely.___.su
_leeheeeee
ji_woo__93
tori_oh
gimyunyeong4236
yeji_jjiya
klpga_jisunday
tennis_nam_coach
yongseongho77
jun_xiang220
yughaejin96
ie4592500
about_minjii
lewon_won
calli_co.kr
ryu_jehee
eni_yyi
imkate_o_o
yesme_le.e
bagsuyeon7979
yae__02
ojh._.95
thejs_s2
hahahohohu
redtt_golf
polrina_beauty
spin_makers
feet_cookie
lhj09
golf.people
s.binii_
papajane__style
muse_de_weekend
bzsdbvs45
mayjiyeon
leepark76
namjieun589
go___ssa
vin_prime
says_profile
lio_glife
_ji_yoon_
namsun_golf
wanna_won_
muya_kkk
amazingcre_gangnam
solar._.health
florist.minji
156.bin
angelddanggu8
velyseoha
iva_destiny
zzozzoing
jihye_8350
eun_9277
cellvia_0.0
artcloud_life
golf__minn
didqhfk90
__pilahn
zzzzz0089
hellobirdie_official
golf___c
jjjjj___y92
kim_jeong_soo2
golfer_jju
monkeyluxury8888
gplf_wd202208
minimouse.k
yun_korea.klpga
ju_vell_
golf_ji_beginner
royal_azalea99
liilllillliill
_made.b
sweetyounjung
rani__0315
outsol__
awdascs2
ryujinsu57
mchangsook
olivia__vv
ann_0_2_
chltnel
nam.kaa
seol_sk
hyunjo_yeo
haereeryu
o.roraa
zzang_0401
oive.kr
dark_bunny1677
hyejin_7931
jeung_hoon
ray_lee_golf
miki80629
3.16_eunsunny
jennifer.sheen.home
songboram160
lnae__
justyoung__
cherry11jju
descentegolf_md
j_lppeu2
suprim_golf
ellie_keepfit
reformation_golf
golf_fashion_urban8
ladygolf__
qingqingcoco
younsunny
jjinn_xoxo
nadia0825
seongsoo.park
jin___iii
seo2._.s2
doapila
rafael_jcrt
2nrrrrr
hae_yuni
steady_sweet_spot
mjsjeong
sports_bong
hyundai_busan_anewgolf
pilates_bongbong
bongsoon0302
weee_star
sense__lim
pilates_seul
s_won777
ssomisomm
0530_yeon
oneing_sayyeah
jjunghun
happinee__s
jjong__ari
bhj_korea
thefairgolf
golf_kyoon
priveskin
isfriend_haha_
2ranni
gaaaaaaaaaahyun
gerifreki_official
the_momo_shop_
sunvely123
yoonboss_
___seong_mi___
eoqkr1112
joorgolf
boyoung333
raro97
seoyun_style
b1109k
golf_hani
srjoo.94
pognenne
kkyu_aa
goldnugetminho
cindy___golf
anjiisgood
golden_k_2022
newartme_
jiji.today
rue557_golf
nanii_mind
golf._.quokka
happyaudrey0070
hpcouple_
msdanilove
agency.universe
cutehyon_
hye_pro_
j_gool
latcbahhh
sdfg57ws
bu__reum
its_golf_
jiyoun.pilates
golf._.s2
hollymeister_korea
golgol414
hyo.box
htdfubhv
j_yul.inee
lovable_song_
2si_nae
courtandgreen
marigold_jj
avecbag_official
_yun_kyung__
___jinss
bijou_ssuny
chaavely
lovelyn210
jh_tennis_golf
golfitter_mz
u_most_lux
jyeon.ko
hyeoooong_ttt
__jj__lux__
jjinn_golf
hyangj__n
ifuhouse_me
yenaa_27
shinbiamakeup
seyon11200613
jun_bae___
_ddungmom_
hoo.epoch
brow_banhada
sweetb_db
maeve_j_j_a
161.7cm_sy
chaa_0729
lovely_won22
mongcho_._
the_vanhye__
xxrina_kim
ms3070
inpink_boutique
sub_hg_iii
yangjiye0n
yujin_2
comosn_callaway
c_o_vak
heap_studio.official
_jungmining
jinjin_golf
lovely_artist_ham
linda_lboo
hyoprodite_golf
con_vely
h._.raning
gdr_academy_jnghm
with.dew2
w.a.s_athleisure
yangbangno
sshin_style
rulruru____________
yullove_09
yena4879
lovesja81
jmuse.kr
935_jooo
sunin_inna
kohjingjing
golf18_yula
god_pro_nieta
heesun_0623
my_golf_diary
222nnnaaa
jangyeongjun98
miii_kikikikikik
hongji_rosie
quiltluv
jeong_____e
mimimimi__s
scottycameron_korea
_mon_choix
kang_mh212
taewoo_choi
golf_sra
ireenjey
golf_tweety
sujung.0124
crownhyj
delight.golf
danlyun
thepure_daldong
pingapparel_korea
chaebeen513
minyounq
siyeonhada
caucommando
lovely_wonny99
golf_sunyeon
hajongyeon9
heohaejin41
goldbeautydiary
hamjaeweon72
by_reume
rororomihari
daring_vely
mylifeis_reina
is2golf_
p.i.group_s2
eungyeongrog20
167cmmy
s2ilver.j
bijou_jhh
04_13_ssss
gyuni.b_mom
seulg.e
kawaii_hime33
bb_golf_offical
proproi_hnaree
ji_prrro
yoojewel
kimjy.0328
golic.official
lpga_5571
2_sunjoo
midoriii33
___myana
golf_lover_kyuri
high_teen88
iamjina_kim
ruth_tte_liyah
ha.park_golf
ya254yg
juuhyun
golf.queencard_offial
hyejin.k____0613
yul_ly_
hyejeong1416
hyune0507
sebi_yu
urjenny___
m.ming_golf
bboa0228
joasua1004
jjenny__lee
__yyoon_
bobo.amor
anewgolf_fashion
nihao_hoonstar
bonbondivers_niya
yeejinkim
sofit_korea
it.s__summer
ssun4ma_a
4somegolf_official
narae_gf
fit_somin
jidor_life
brillianteum
kkoooooook
______syyy.oo
joojis_
areum.zip
kwon_a____
carmila4000
yun.jj
rurumombiju
thedailyaugust
xoxo_zelia
ahyeon_0325
jinsil.love
habia.co
silver_golf_
flex_r_official
selfstorage_extraspace
seungeunchang
ey__golf
jieful__life
betty_lmh
kim__so_jeong
lovrainyy
teeup31_golf
snshelperkr.49
jihyun.chung1
nanasgolf
y_uxxn
aaatan317
hanewzzz
kyungha_happy
mingum80
pm.bomi
minseo_pro
eunji_r
ahaluvv
158_46kg
golf_newg
miss_hong88
after9hole
hermes__ermess
showneee_k
aube.rose_flower
eileen_golf_
twoyeons0320
ginger___c
longlongmj
teeoff_yeongjong
jiyoon.love_you
golfer_miin
oliviakim412
kimmijung0222
ji_yeon0108
jxx_85
narae__v
kylie__hee
hey_jin_e_
johnny_kslee
enbi_beauty
ssun.k__golf
1021j_y
jessi__fit
seohyunlov
anna.rima
nayoonie1209
citeezon_jc
olaola_711
golfmagazine_kr_fashion
hyemi.lovely
hello_birdie_golf
grace__hur
c_oooooling
seeu__seeu
luxpremium_golf.pila
miss.pyun
chries_life
kwakjieun2422
plabel_ch
im_solarc
i_amjini
rri._.naa
vv_vid
probar_golfwear
suh_j_h
jsuite_golf
golf_velyy
yehna_bynature
tone_a_manner_yujin
soojung0407
fabricwld
cheolsu83
jjua._.ibeauty
doolyben
golf.mins
julie_vely_
bsharp.official
glowandhappy_sso
emma_pilates_
janet_minjung
ho._nee
ttinker__bell
yeon__uuu
daeun7726
jung.ssuk
an.seo.in
golfer__i_want
golf_olive
s_yoon_golf
choi__yoojin
helloangelato
siyeon__2030
alwn2045
last_ganzi
dinggu.golf
ineninshop
lively_bennie
hyemida__a
voer_golf
radice_golf
p._.yoom
p._.yoom
sarang2_golf
haengeun11
spo.ground
golzzang_official
ryu_jehee
hello_birdie_golf
iwhdk_you
sense_bounce
rrrrrosedu_
eungpro
kkkkkk.mi
baribariyunbari
angelica_yum
hae_yuni
golf_mingming
_yun_kyung__
haduri_mom
miya1221_
joohee_golf
jihye.1211
ribbongirl_golflove
9olfree.e
7080golf
sunrise_won
julie_run
reformation_golf
hwayoung_77
pianist.ina
miracleyeonseo
wc__js
rangdesia_golf
soo_good__
golfholic17
zzzini28
ysjgolf
yesme_le.e
nooow_gnag2
_ming_o0o
joobgolfstudio
am_co2
yeah_joy_golf
dontcry79
jw_lppeu
jihee3024
powergolf_p
golf__h.____.y__
layla__avid_golfer
_sara.violet
kyungah_22
peach_blossom80
weee_star
workout_jjjj
jeonhyojeong5
_rosyu
_mon_choix
pink_swan80
toomuch_toolittle_
dongmigyeong5539
volvik_1
hobin_sun
niceshot_dr.kim
jolijana
nabi.nalssini
siyeon__2030
doolyben
wonee_0610
thegreatlife__
yemi_kim
kim_2seul._
judy_judy___
kkangeun_12
eileen_ug
ymhunique
urisword1453
ttottojiyu
thekoreangirl.travel
sycocosy
ss_young_a
sh.1109
sebi_yu
sbp_1230
round.s_official
rose122500
proacox
piece.of_time
ni._.kku
kigibe82
jihozero_golf
hxx_golf
gol_leenie
giantgolf_tour
farfalla_store_
balletfit_korea_claire
171_yeju
sayahiro1004
angelica_yum
bigbutt_luv
rikkiung
yeun90_____
sunnykim7
gangreunggolmaket
s.park_inos
misu.happy
hyuneegolfs
lyjoooooooo
bootyfull_golf
anewgolf_ilsan
segteuminji
lord_dregon_aaa
cccqqweqwss_dqwq
0305_dy
johnsancton
onyourmine
ammarkaddoura444
wideangle_hyundai_ulsan
mina__life_style
lhj5435
koongs_gf
kiyeonn
jmmusic_audie
jjinjin_golf
jinwoo_pro
jinseonmi45
jieun_amitie
hyewon_e8
gemma_0130
eunsoo_bro
eunchae_yoon
blooming.j_lee
_eom_seoyun
yujin289465
namyangjucc
susieq_golf
sonsoungtae
root8_kr
prooooo___j
ye_rin0207
yaho_ssun
whihyungpark
vyvygolf
mnmgolf4u
vision2pro
to_get_her_golf
mansunne
hyunjung_yoyo
ryungkim_golf
loveagness0211
choi_yea_di
roundofgolf_rina
jin_8208
charlotteji0732
rrrrrosedu_
one_ramii
na_j.s
my_oooo_
myeongjuoh
bboksil
moon.ah.ram
kimpro1010
_eunbij
keikim_0317
kang_k.k.r
jungmileejulie_huasasunday
jennifer_pila
j.e.park0106
isy3502
iamivyvy
daily_golf_hj
hobbylifeanything10
haduri_mom
golf_love80
fix.329
__hey___t
dalkkomi_
annajo_golf
ang_golf
04x06x00x2
angela_choi2425
_lululala_golf_
theplantbase_velma
sseoliiiii
x_x_gvely_
yooouzinieo
yjyeon1226
hana91park
wonpark1101
westocean_c.c
vsss.x
teni_teny
summer_golfer
suan_kim_love
dareplay_crew
ssssseozy
bodyon_golf
_superboyyyyy
ownhart1
mini_jeongmin
lovelyn_chu
limrachel65
lemon_junghwa
lee__ju__yeon
jstory7
jaem_golf
hyeonju7636
hyemi89
hahyeryoung
golf.hee
florist.minji
ezsun_520
euddeumlee.pro
coco_e.j
bin__mom
babes_golf
aeiouu_daily
aiming_golf
_j_hee__
__bycindy
2zabelle_
1min_golf_talk
zosrn369
yh051_6
yeonju8213
sujini318
ji_____n_
yee___ram
y__gym
zzang_0401
coconello7
miii_kikikikikik
thisismyswing
_pankyu_pro
kukhee0212
1121raina
jelly0629
haruakina
minyul_nayul
__eun_hyy__
sunzzang0822
ss.u___a
golfqueen_to_be
loveyoonsoo
go_cha_ssam
jion._.mom
passardi.shop
jihyun88
amazing_miza_
1.1.0.4_s2
hahadw04
jeonjeehee
golfer_kkang
golf_190823
eunseunglee""")
    user_infos_list = ['100bum', 'dlttefvd', 'heemin1112', 'star.love.golf', 'gimseoa_', 'lllove._4', 'birdie_soyoon', 'jjuyerini', 'wonee_0610', 'wiisdom_sports', 'daniel_parkic_', 'dain__cha', 'iran77766', 'na_eun5555', 'eunjungram', 'pitch.and.run', 'store_monsterg', 'ddanggu._.sis_8', 'wjm0508', 'gearantan', 'gahui.kang', 'jennalovesgolf', 'jeonmarie_', 'heejung100986', 'truck_8989', 'yangyeseung', 'umost_l_u_x', 'yser_dur143', 'zzirong_g', 'rim2_golf', 'sellermill', 'sua__su', 's_nnninn', 'umostlux54', 'sejin_golf_academy', 'u_most_lux__', '17sunny17', 'kwakhamoly', 'fantom_sports', 'jhookim_', 'junkang0330', 'daepocha_9623_2266', 's.insolence', 'dajeongmemory', 'hongsuyeon81', 'kkkkzhhhs', 'riwon.vely', 'shashot.official', 'oklm.golf', 'u_most_lux_', 'lydia_hwang_', 'sy_dazzle83', '_fluke.j', 'luvbomiri', 'dfdef78787', 'healthboy53', 'theonly_____jy', 'mareqing3', 'am0102am', 'chaeha_kim_', 'bailywhite_golf', 'debelle_jihae', '0310____eun', 'wonsiy_un', 'ateliermong', 'dong.baegwinnergolf', 'korea_lelsure_partners', 'cocoa__golf', '_znnam', 'yerinl', 'eeez.l', 'winsome_hyun_', 'woonae_golf', 'zxzxhyn', 'recess.beauty', 'flowshopkr', 'luv.atti', 'leesuroom_golf', 'younbly_monica', 'shanghai_golfistar', '_a_hyeong', 'qajdsgh0', 'dlstjd__7', 'pinkerbelle___', 'artttree97', 'yo_oy.j', '_bailywhite', 'born_to_golf_', 'loving_catcat', 'ballic_annajo', 'anew_golf_', 'amazingcre____ulsan', 'eun_gongju', 'vv_lovemind_vv', 'jina_life__golf', 'dae6queen', 'anjian94___', 'dlstjd__2', '90._.minju', 'lindachae.realtor', 'allysia_85', 'kossen_sou', 'hys_ny', 'jinddoing', 'dr_ko_eun_lee', 'lovely_golfer0321', 'anewgolf_cheonan', 'golf.fashion.sg', 'sunah_golf', 'umji_a', 'ohohgolf', 'lee_soso_11', 'gdr_academy_shsc', 'the_pianistmusic', 'coedonghan13', 'mareqing5', 'biniyang', 'luv_yoa.dnkg', 'myungjae.shin', 'since19820719', 'golfernamoni', 'hiitsselina', 'shu__jing_', 'hyosim7699', 'asd_asd1726', 'sssssswon', 'peachbong', 'gogaram41', 'chaee._.vely', 'parksuhyeon1028', 's.m.s.c', 'yamcebol', 'jql_sports', 'imaginie__', 'claire___ciel_k', 'inside_g1986', 'gdr_academy_gsgy', 'jjunjjun_mommy', 'jjo_arrrra', 'dlstyjd__22', 'insung__700', 'seul0418', 'seo24__', 'hwang_bbong', 'golfrano', 'sj.workout_', 'lovely.___.su', '_leeheeeee', 'ji_woo__93', 'tori_oh', 'gimyunyeong4236', 'yeji_jjiya', 'klpga_jisunday', 'tennis_nam_coach', 'yongseongho77', 'jun_xiang220', 'yughaejin96', 'ie4592500', 'about_minjii', 'lewon_won', 'calli_co.kr', 'ryu_jehee', 'eni_yyi', 'imkate_o_o', 'yesme_le.e', 'bagsuyeon7979', 'yae__02', 'ojh._.95', 'thejs_s2', 'hahahohohu', 'redtt_golf', 'polrina_beauty', 'spin_makers', 'feet_cookie', 'lhj09', 'golf.people', 's.binii_', 'papajane__style', 'muse_de_weekend', 'bzsdbvs45', 'mayjiyeon', 'leepark76', 'namjieun589', 'go___ssa', 'vin_prime', 'says_profile', 'lio_glife', '_ji_yoon_', 'namsun_golf', 'wanna_won_', 'muya_kkk', 'amazingcre_gangnam', 'solar._.health', 'florist.minji', '156.bin', 'angelddanggu8', 'velyseoha', 'iva_destiny', 'zzozzoing', 'jihye_8350', 'eun_9277', 'cellvia_0.0', 'artcloud_life', 'golf__minn', 'didqhfk90', '__pilahn', 'zzzzz0089', 'hellobirdie_official', 'golf___c', 'jjjjj___y92', 'kim_jeong_soo2', 'golfer_jju', 'monkeyluxury8888', 'gplf_wd202208', 'minimouse.k', 'yun_korea.klpga', 'ju_vell_', 'golf_ji_beginner', 'royal_azalea99', 'liilllillliill', '_made.b', 'sweetyounjung', 'rani__0315', 'outsol__', 'awdascs2', 'ryujinsu57', 'mchangsook', 'olivia__vv', 'ann_0_2_', 'chltnel', 'nam.kaa', 'seol_sk', 'hyunjo_yeo', 'haereeryu', 'o.roraa', 'zzang_0401', 'oive.kr', 'dark_bunny1677', 'hyejin_7931', 'jeung_hoon', 'ray_lee_golf', 'miki80629', '3.16_eunsunny', 'jennifer.sheen.home', 'songboram160', 'lnae__', 'justyoung__', 'cherry11jju', 'descentegolf_md', 'j_lppeu2', 'suprim_golf', 'ellie_keepfit', 'reformation_golf', 'golf_fashion_urban8', 'ladygolf__', 'qingqingcoco', 'younsunny', 'jjinn_xoxo', 'nadia0825', 'seongsoo.park', 'jin___iii', 'seo2._.s2', 'doapila', 'rafael_jcrt', '2nrrrrr', 'hae_yuni', 'steady_sweet_spot', 'mjsjeong', 'sports_bong', 'hyundai_busan_anewgolf', 'pilates_bongbong', 'bongsoon0302', 'weee_star', 'sense__lim', 'pilates_seul', 's_won777', 'ssomisomm', '0530_yeon', 'oneing_sayyeah', 'jjunghun', 'happinee__s', 'jjong__ari', 'bhj_korea', 'thefairgolf', 'golf_kyoon', 'priveskin', 'isfriend_haha_', '2ranni', 'gaaaaaaaaaahyun', 'gerifreki_official', 'the_momo_shop_', 'sunvely123', 'yoonboss_', '___seong_mi___', 'eoqkr1112', 'joorgolf', 'boyoung333', 'raro97', 'seoyun_style', 'b1109k', 'golf_hani', 'srjoo.94', 'pognenne', 'kkyu_aa', 'goldnugetminho', 'cindy___golf', 'anjiisgood', 'golden_k_2022', 'newartme_', 'jiji.today', 'rue557_golf', 'nanii_mind', 'golf._.quokka', 'happyaudrey0070', 'hpcouple_', 'msdanilove', 'agency.universe', 'cutehyon_', 'hye_pro_', 'j_gool', 'latcbahhh', 'sdfg57ws', 'bu__reum', 'its_golf_', 'jiyoun.pilates', 'golf._.s2', 'hollymeister_korea', 'golgol414', 'hyo.box', 'htdfubhv', 'j_yul.inee', 'lovable_song_', '2si_nae', 'courtandgreen', 'marigold_jj', 'avecbag_official', '_yun_kyung__', '___jinss', 'bijou_ssuny', 'chaavely', 'lovelyn210', 'jh_tennis_golf', 'golfitter_mz', 'u_most_lux', 'jyeon.ko', 'hyeoooong_ttt', '__jj__lux__', 'jjinn_golf', 'hyangj__n', 'ifuhouse_me', 'yenaa_27', 'shinbiamakeup', 'seyon11200613', 'jun_bae___', '_ddungmom_', 'hoo.epoch', 'brow_banhada', 'sweetb_db', 'maeve_j_j_a', '161.7cm_sy', 'chaa_0729', 'lovely_won22', 'mongcho_._', 'the_vanhye__', 'xxrina_kim', 'ms3070', 'inpink_boutique', 'sub_hg_iii', 'yangjiye0n', 'yujin_2', 'comosn_callaway', 'c_o_vak', 'heap_studio.official', '_jungmining', 'jinjin_golf', 'lovely_artist_ham', 'linda_lboo', 'hyoprodite_golf', 'con_vely', 'h._.raning', 'gdr_academy_jnghm', 'with.dew2', 'w.a.s_athleisure', 'yangbangno', 'sshin_style', 'rulruru____________', 'yullove_09', 'yena4879', 'lovesja81', 'jmuse.kr', '935_jooo', 'sunin_inna', 'kohjingjing', 'golf18_yula', 'god_pro_nieta', 'heesun_0623', 'my_golf_diary', '222nnnaaa', 'jangyeongjun98', 'miii_kikikikikik', 'hongji_rosie', 'quiltluv', 'jeong_____e', 'mimimimi__s', 'scottycameron_korea', '_mon_choix', 'kang_mh212', 'taewoo_choi', 'golf_sra', 'ireenjey', 'golf_tweety', 'sujung.0124', 'crownhyj', 'delight.golf', 'danlyun', 'thepure_daldong', 'pingapparel_korea', 'chaebeen513', 'minyounq', 'siyeonhada', 'caucommando', 'lovely_wonny99', 'golf_sunyeon', 'hajongyeon9', 'heohaejin41', 'goldbeautydiary', 'hamjaeweon72', 'by_reume', 'rororomihari', 'daring_vely', 'mylifeis_reina', 'is2golf_', 'p.i.group_s2', 'eungyeongrog20', '167cmmy', 's2ilver.j', 'bijou_jhh', '04_13_ssss', 'gyuni.b_mom', 'seulg.e', 'kawaii_hime33', 'bb_golf_offical', 'proproi_hnaree', 'ji_prrro', 'yoojewel', 'kimjy.0328', 'golic.official', 'lpga_5571', '2_sunjoo', 'midoriii33', '___myana', 'golf_lover_kyuri', 'high_teen88', 'iamjina_kim', 'ruth_tte_liyah', 'ha.park_golf', 'ya254yg', 'juuhyun', 'golf.queencard_offial', 'hyejin.k____0613', 'yul_ly_', 'hyejeong1416', 'hyune0507', 'sebi_yu', 'urjenny___', 'm.ming_golf', 'bboa0228', 'joasua1004', 'jjenny__lee', '__yyoon_', 'bobo.amor', 'anewgolf_fashion', 'nihao_hoonstar', 'bonbondivers_niya', 'yeejinkim', 'sofit_korea', 'it.s__summer', 'ssun4ma_a', '4somegolf_official', 'narae_gf', 'fit_somin', 'jidor_life', 'brillianteum', 'kkoooooook', '______syyy.oo', 'joojis_', 'areum.zip', 'kwon_a____', 'carmila4000', 'yun.jj', 'rurumombiju', 'thedailyaugust', 'xoxo_zelia', 'ahyeon_0325', 'jinsil.love', 'habia.co', 'silver_golf_', 'flex_r_official', 'selfstorage_extraspace', 'seungeunchang', 'ey__golf', 'jieful__life', 'betty_lmh', 'kim__so_jeong', 'lovrainyy', 'teeup31_golf', 'snshelperkr.49', 'jihyun.chung1', 'nanasgolf', 'y_uxxn', 'aaatan317', 'hanewzzz', 'kyungha_happy', 'mingum80', 'pm.bomi', 'minseo_pro', 'eunji_r', 'ahaluvv', '158_46kg', 'golf_newg', 'miss_hong88', 'after9hole', 'hermes__ermess', 'showneee_k', 'aube.rose_flower', 'eileen_golf_', 'twoyeons0320', 'ginger___c', 'longlongmj', 'teeoff_yeongjong', 'jiyoon.love_you', 'golfer_miin', 'oliviakim412', 'kimmijung0222', 'ji_yeon0108', 'jxx_85', 'narae__v', 'kylie__hee', 'hey_jin_e_', 'johnny_kslee', 'enbi_beauty', 'ssun.k__golf', '1021j_y', 'jessi__fit', 'seohyunlov', 'anna.rima', 'nayoonie1209', 'citeezon_jc', 'olaola_711', 'golfmagazine_kr_fashion', 'hyemi.lovely', 'hello_birdie_golf', 'grace__hur', 'c_oooooling', 'seeu__seeu', 'luxpremium_golf.pila', 'miss.pyun', 'chries_life', 'kwakjieun2422', 'plabel_ch', 'im_solarc', 'i_amjini', 'rri._.naa', 'vv_vid', 'probar_golfwear', 'suh_j_h', 'jsuite_golf', 'golf_velyy', 'yehna_bynature', 'tone_a_manner_yujin', 'soojung0407', 'fabricwld', 'cheolsu83', 'jjua._.ibeauty', 'doolyben', 'golf.mins', 'julie_vely_', 'bsharp.official', 'glowandhappy_sso', 'emma_pilates_', 'janet_minjung', 'ho._nee', 'ttinker__bell', 'yeon__uuu', 'daeun7726', 'jung.ssuk', 'an.seo.in', 'golfer__i_want', 'golf_olive', 's_yoon_golf', 'choi__yoojin', 'helloangelato', 'siyeon__2030', 'alwn2045', 'last_ganzi', 'dinggu.golf', 'ineninshop', 'lively_bennie', 'hyemida__a', 'voer_golf', 'radice_golf', 'p._.yoom', 'p._.yoom', 'sarang2_golf', 'haengeun11', 'spo.ground', 'golzzang_official', 'ryu_jehee', 'hello_birdie_golf', 'iwhdk_you', 'sense_bounce', 'rrrrrosedu_', 'eungpro', 'kkkkkk.mi', 'baribariyunbari', 'angelica_yum', 'hae_yuni', 'golf_mingming', '_yun_kyung__', 'haduri_mom', 'miya1221_', 'joohee_golf', 'jihye.1211', 'ribbongirl_golflove', '9olfree.e', '7080golf', 'sunrise_won', 'julie_run', 'reformation_golf', 'hwayoung_77', 'pianist.ina', 'miracleyeonseo', 'wc__js', 'rangdesia_golf', 'soo_good__', 'golfholic17', 'zzzini28', 'ysjgolf', 'yesme_le.e', 'nooow_gnag2', '_ming_o0o', 'joobgolfstudio', 'am_co2', 'yeah_joy_golf', 'dontcry79', 'jw_lppeu', 'jihee3024', 'powergolf_p', 'golf__h.____.y__', 'layla__avid_golfer', '_sara.violet', 'kyungah_22', 'peach_blossom80', 'weee_star', 'workout_jjjj', 'jeonhyojeong5', '_rosyu', '_mon_choix', 'pink_swan80', 'toomuch_toolittle_', 'dongmigyeong5539', 'volvik_1', 'hobin_sun', 'niceshot_dr.kim', 'jolijana', 'nabi.nalssini', 'siyeon__2030', 'doolyben', 'wonee_0610', 'thegreatlife__', 'yemi_kim', 'kim_2seul._', 'judy_judy___', 'kkangeun_12', 'eileen_ug', 'ymhunique', 'urisword1453', 'ttottojiyu', 'thekoreangirl.travel', 'sycocosy', 'ss_young_a', 'sh.1109', 'sebi_yu', 'sbp_1230', 'round.s_official', 'rose122500', 'proacox', 'piece.of_time', 'ni._.kku', 'kigibe82', 'jihozero_golf', 'hxx_golf', 'gol_leenie', 'giantgolf_tour', 'farfalla_store_', 'balletfit_korea_claire', '171_yeju', 'sayahiro1004', 'angelica_yum', 'bigbutt_luv', 'rikkiung', 'yeun90_____', 'sunnykim7', 'gangreunggolmaket', 's.park_inos', 'misu.happy', 'hyuneegolfs', 'lyjoooooooo', 'bootyfull_golf', 'anewgolf_ilsan', 'segteuminji', 'lord_dregon_aaa', 'cccqqweqwss_dqwq', '0305_dy', 'johnsancton', 'onyourmine', 'ammarkaddoura444', 'wideangle_hyundai_ulsan', 'mina__life_style', 'lhj5435', 'koongs_gf', 'kiyeonn', 'jmmusic_audie', 'jjinjin_golf', 'jinwoo_pro', 'jinseonmi45', 'jieun_amitie', 'hyewon_e8', 'gemma_0130', 'eunsoo_bro', 'eunchae_yoon', 'blooming.j_lee', '_eom_seoyun', 'yujin289465', 'namyangjucc', 'susieq_golf', 'sonsoungtae', 'root8_kr', 'prooooo___j', 'ye_rin0207', 'yaho_ssun', 'whihyungpark', 'vyvygolf', 'mnmgolf4u', 'vision2pro', 'to_get_her_golf', 'mansunne', 'hyunjung_yoyo', 'ryungkim_golf', 'loveagness0211', 'choi_yea_di', 'roundofgolf_rina', 'jin_8208', 'charlotteji0732', 'rrrrrosedu_', 'one_ramii', 'na_j.s', 'my_oooo_', 'myeongjuoh', 'bboksil', 'moon.ah.ram', 'kimpro1010', '_eunbij', 'keikim_0317', 'kang_k.k.r', 'jungmileejulie_huasasunday', 'jennifer_pila', 'j.e.park0106', 'isy3502', 'iamivyvy', 'daily_golf_hj', 'hobbylifeanything10', 'haduri_mom', 'golf_love80', 'fix.329', '__hey___t', 'dalkkomi_', 'annajo_golf', 'ang_golf', '04x06x00x2', 'angela_choi2425', '_lululala_golf_', 'theplantbase_velma', 'sseoliiiii', 'x_x_gvely_', 'yooouzinieo', 'yjyeon1226', 'hana91park', 'wonpark1101', 'westocean_c.c', 'vsss.x', 'teni_teny', 'summer_golfer', 'suan_kim_love', 'dareplay_crew', 'ssssseozy', 'bodyon_golf', '_superboyyyyy', 'ownhart1', 'mini_jeongmin', 'lovelyn_chu', 'limrachel65', 'lemon_junghwa', 'lee__ju__yeon', 'jstory7', 'jaem_golf', 'hyeonju7636', 'hyemi89', 'hahyeryoung', 'golf.hee', 'florist.minji', 'ezsun_520', 'euddeumlee.pro', 'coco_e.j', 'bin__mom', 'babes_golf', 'aeiouu_daily', 'aiming_golf', '_j_hee__', '__bycindy', '2zabelle_', '1min_golf_talk', 'zosrn369', 'yh051_6', 'yeonju8213', 'sujini318', 'ji_____n_', 'yee___ram', 'y__gym', 'zzang_0401', 'coconello7', 'miii_kikikikikik', 'thisismyswing', '_pankyu_pro', 'kukhee0212', '1121raina', 'jelly0629', 'haruakina', 'minyul_nayul', '__eun_hyy__', 'sunzzang0822', 'ss.u___a', 'golfqueen_to_be', 'loveyoonsoo', 'go_cha_ssam', 'jion._.mom', 'passardi.shop', 'jihyun88', 'amazing_miza_', '1.1.0.4_s2', 'hahadw04', 'jeonjeehee', 'golfer_kkang', 'golf_190823', 'eunseunglee']
    ##2. 유저 분할
    user_infos_list = user_infos_list[300:]
    total_user_infos_group = divide_user_infos_list(user_infos_list, group_size=1)
    print(len(total_user_infos_group))

    ##3. db 발송
    send_total_message(total_user_infos_group, text, project_name=project, proxy=proxy)
