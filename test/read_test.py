from datetime import datetime
from datetime import timedelta
import logging
from db import m_instagram
from session_save.util import generate_uuid

insta_db = m_instagram.InstaDB(db_name="account")
account_collection = insta_db.account_collection

logger = logging.getLogger(__name__)

# 로그의 출력 기준 설정
logger.setLevel(logging.DEBUG)

# log 출력 형식
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s %(funcName)s - %(message)s')

# log 출력
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

JIN_INSTAGRAM = m_instagram.InstaDB(db_name="instagram_analysis").db
JIN_ACCOUNT = JIN_INSTAGRAM["account"]

SERVICE_INSTAGRAM = m_instagram.InstaDB(db_name="service_instagram").db
INSTA_ACCOUNT_OBJ = m_instagram.InstaAccount(client_name="admin", channel_name="instagram").db
ACCOUNT_COLLECTION = INSTA_ACCOUNT_OBJ['account']
BAND_ACCOUNT, HASHTAG_AND_USER, PROJECT_COLLECTION, ITEM_HASHTAG_COLLECTION, ITEM_USER_COLLECTION, ITEM_LOCATION_COLLECTION, INFO_COLLECTION, TASK_COLLECTION, POST_COLLECTION, SEARCH_COLLECTION, SETTING_COLLECTION = \
    SERVICE_INSTAGRAM["account_instagram"], SERVICE_INSTAGRAM["hashtag_and_user"], SERVICE_INSTAGRAM["project"], SERVICE_INSTAGRAM["hashtag"], \
    SERVICE_INSTAGRAM["user"], SERVICE_INSTAGRAM["location"], SERVICE_INSTAGRAM["info"], SERVICE_INSTAGRAM["task"], \
    SERVICE_INSTAGRAM["post"], SERVICE_INSTAGRAM["search"], SERVICE_INSTAGRAM["setting"]


def read_account_setting_info_from_db(username, password):
    uuids = generate_uuid.generate_all_uuids(username, password)
    device_doc = SETTING_COLLECTION.find_one({"name":"base"})
    device_doc["uuids"] = uuids["uuids"]
    return device_doc

s = """
iam_beautifulstar
greedeat
inssa_elf
minahjjang
sh1016sh
_hyerim.2
lym1004567
blue8854
incheon_all
kingo1398
mhhan71
haebbang2
kimming_gu
jinyzzac
bijou_table_
insight_food
taki1471
dd__boon
lsb_9225
hanna199612
ram._.0203
toyluv_
sujung767676
se6323321
seraspia
heeya_xxi
gabriella_chae
love.1002
jjuaeng2
skyyouli23
s_euun_
khccsj1
haram2ne
lin________2
bomnal_hy
96_c.s
ssamji36
kwonhuira
fandatoy
nabong_cafe
myvely828
_yeolmae_
dxyxn___
hsw6767
lee_a.ra
hanaplusu
h.m_cooking_mom
anniemom89
wonderkkakka
yerim.jin
poodlegguggu_
gyungsss
haitai_co
bora.own
hi_ggung
water.eun
eh__kkk
yoons_eatrip
metal_kro
yulcongcong
star0k77
mirang_yerang
kyung_a_choi
jobsick_eat
dachshund_robin
2at_ing_k
ruiyan1024
dkfnsl1987
bbobbo.y
humor_lovely
han_rabongri
___cute._.cute___
woongjinfood
poorin_diary
star279600
bn_07.07
yoonminjeon
paldofood
nyxseren
yeminhye
mukmuk_ga
kimsumi35
im__eunsol
b3game5242
touslesjours_kr
hongz_zi
inssa_bro
dolmaengyi_
k___soo_ah
bbang0123_
milk_hodu
kim_____pink
peki_kkong
heeee.eee
davely1013
i._.morae
dogistar_jk
im.simba_nala
ziny_ee
h_gail95
likesugi
jeehyeounn
doctordog_korea
i_am_deoksun
mytinylittle_aari
kyung_hee2994
joohee0630
imall1028
do_boo_diary
_mieumi
nemo.tattoo
ji_jiji03
luie_petfood
meongdi_
soon.doong
the_jaehee
giant_baking
nachokancho
_yo_cook_
chulsoo_dog
"""
k = s.split("\n")
print(k)