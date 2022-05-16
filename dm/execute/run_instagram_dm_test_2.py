from db import m_instagram
from instamanager import Bot
import logging


# get_dm_source.util_get_source_message("meat_run_lab_message.txt")
FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
if logger.hasHandlers():
    # Logger is already configured, remove all handlers
    logger.handlers = []
logger.setLevel(logging.INFO)


text = """
안녕하세요. 
따뜻한 봄이 왔지만!! 
오미크론에 엄청난 확산세로.
봄나들이 다니기 겁나시고 뭘할까
고민이시죠? 

전 현제 확진으로 인해 나가지 못하는 상황에서도 
집에서 할수 있는 것을 찾아 고민해결 하였습니다. 

- SBS biz, 매일경제TV 방영 
- 1:1멘토, 팀과 함께하는 
팀빌딩 시스템
- 가입비 없음, 유지비 없음, 초보자 가능
- 폰만 있음 나도 성공

저희 시스템 영상 시간되실때 꼭 한번 봐주시고 제 개인플랫폼으로 무료체험 해보세요.

https://www.fcsmartsystem.com/business/allMasterPlanWeekList.do
"""

db_conn = m_instagram.InstaDB().conn
INSTA_ACCOUNT_OBJ = m_instagram.InstaAccount(channel_name="instagram")
INSTA_ACCOUNT_OBJ.client_name = "admin_test"





def select_user(username):
    account_setting_info = INSTA_ACCOUNT_OBJ.select_cookie_user_v2(username=username)
    return account_setting_info

def run():
    project = "test"
    start_date = "2022-04-08"
    project_info = {"project_name": project, "start_date": start_date}

    username, password = 'datacast4', 'amdc2580!'
    proxy = f"http://user-{username}-sessionduration-1:{password}@us.smartproxy.com:10001"

    target_username = ['tae_yeon_zero', 'minxbbang_', 'realreal_i', 'byeole_88', 'foresian88', 'dewdrop_dakku', 'isdouner', 'k86______', 'serendifity4', 'ssoo_ool', 'lsb0414', 'makeyou_lash', 'arum.0220', 'ammu_choi', 'rachelgn81', 'ha.and.yoom', 'won_yajin801', 'yeon_ream', 'gre.en63', 'fat200511', 'proeatjunho', 'someone_choi', 'jungstagram81', '0_gun_96', 'todaki_co', 'yul_9002', 'ggilb_o', 'daonheesm', 'allllla__official', 'hyeonjeong1760', 'rahyeon_hospital', 'lucifer9624', 'baek__stagram', 'hye_jin_1020', 'shinhospital1', 'bosco._.131', 'hvacbank', 'tjh1117', 'bodyprofile_100days', 'leemingkee', 'benz_polarbear', 'ukaly5357', 'jjjbaking', 'seolgi_ssam_coaching', 'jooshinpark1', 'ilun0527', '_sangma325_', 'hal_joo', 'kkwaksj', 'momoroni_market', 'aiheroes.ai', 'sunape0', 'eungdi03', 'soojii_yul', 'anlaghn', 'tripple11', 'taehoon_1013', 'justwannafree2022', 'pami_lounge', 'jongho_0313', 'yolorimboogie', '_jjjmaria_', 'greenbee07', 'onpoint_lit', 'flex_2022', 'gusam0guegong', 'just1dayusual', 'laon.life', 'hg_twomin1318', 'hh._.ddo', 'splash._.17', 'cathysui7', 'suni0528', 'sanghyeon1441', 'stapler.girl_officer', 'afg_centum_ap_.ksj', 'jangbong99', 'kyoungmin_kim_01', 'stbt_doong', '_yeonkot', 'sinbi622', 'nam_dy1215', 'e.hyuk213', 'jieum0905', 'luv_171225', 'hey_sunny_itsgonnabeok', 'ddo_nyoung', 'shmk_sk', 'yosebigim', 'insoo.son', 'sookhyun1102', 'pawpaw_lism', 'kimsujin1004', 'young.ran.park', 'lovedaeunyou', 'munmyeongji', 'hyunjun0815', 'nayoosw', 'bitbyeol.mom', 'shinjungmin412', '71yeok', 'sing_and_laugh', 'local_passion', 'wandering_star79', 'jddie48', 'kimdobin_0824', 'eun2__', 'piggy_nami', '_seoyunmom', 'jji_yul.mom', 'haevery_dain', 'wooyung_jung', 'bomnal_eun', 'jeju_bubu', 'kuno.um', 'elrxls96', 'munababo', 'heesun_park78', 'hanseunghyi5', 'jibangtoon', 'chan2____food', 'so__0_____', 'sy_kim73', 'iamkeumju', 'ai.osonegro', 'labom.ps', 'lemon_luv_hk', 'karabajos', 'by_monnan2', 'hahahoho22222222', 'pjs.ldh', 'misun_1982', 'creart_daebang_themcity', 'ansjdhkd', 'minsoo___p', 'seonghojwa', 'sisqozang', 'mr.j_0308', 'hyunju5875', 'nani_mang', 'yooahyooah', 'jjjjjmasy', 'ddingsun83', 'choi_isollll', 'devil._.mango', '161921_mom', 'mtsun_ny', 'cry.whenyouwant', 'ssjin03', 'aran_snow', 'na0_2ya', 'hyunyi_2', 'kimhalim_kimtaehyun', 'hee_a0416', 'yr_0714', 'kyoh1215', 'huni9125', 'eunmin_mini', 'bagyeongju8798', 'junijjuni', 'yu_say_hay', 'inddong_yoon', 'usfestool', 'ten_ianpark', 'sowon_papa', 'youngjaekim_', 'noljak_cheongju', 'gaeuni_bogo', 'minjo7288', 'soonmi6035', 'hyeobively', 'e74_n80_f51_p63', 'my_s2_jy', 'kimbbo_0', 'hshyun13', 'ethan_0407_', 'purejohn84', 'yoohyeran_0730', 'hosu_131111', 'kwala_soolmate', 'ordinary_korean_family', 'bora._.choco', 'nayoungae_freedom', 'jwooks_lee', '01_31yun', 'ieunhwa447', 'seoha_0618', 'maemea111', 'hwajin1985', 'annai19821207', 'jaejin_1123', 'hyunbin1', 'seohyeonjju', '_soeul.a', 'my.neuliii', 'kkyumm__', 'dudi_themole', 'royand_roym', 'mi_sunny_an', 'youra1210', 'jace_hobby', 'yangdongoh', '__diary.choi', 'kktaegeon', 'alswjd8409', 'younae_park', 'man_darin0214', 'beauty____fall', 'suzzlnx', 'pinksnow716', 'kangi_0911', 'coesua8253', 'flatishop', 'yoonhee8357', 'palrau1', 'jjoung1213', 'lee_ati_08', 'j_wh422', '________yaaho', 'tangkyul.22', 'victorytiger_', 'afterrain82', 'tjfl2357', 'dbsdudal02', 'charles_h.202', 'tiger_one_0820', 'jong___yuna', 'mingming9ming', 'junehyeup_j', 'flyfam2015', 'haehae_mama', 'dodamjiwoo', 'b01b11', '__soomin0409', 'yu_jung_happy', 'esther0164', 'seon_liz_park', 'sunyeongc973', 'miyaliove', 'ypumpin', 'wooga_studio', 'aki_jihyun', 'miriming84', 'jjomaenanippeuni', 'beomx22', 'miru_lovers', 'junsuyon', 'adieumom', 'ssongmj89', 'goran_yoo', 'heylim_1028', '22h._.m01', 'byungho725', 'mash.5555', 'nyamnyamjjupjjup', 'ri_won_0905', 'lovelybaby_fullmoon', 'unee_minee', 'yunny.home', 'junwoodr', 'ys.sejin', 'lovelyeon0227', 'luv_chuss', 'kja847762', 'miseon__ko', 'dylee67', 'lemonia_82', 'jeongah324', 'bestdal834', 'hye_mi_sin', 'luv_sia_com', 'playcook_', 'insideangle', 'jdy0604', 'coehyeonmi54', 'migang_89', 'hyerangju', 'gamidoni_mom', 'soo_travelwith', 'kimhana0601', 'joyyoom', 'short_track_fan.page', 'hyun.jmx', 'kisqueen7979', 'dongah1001', 'do_stock_go', '__orim__', 'som_bling_', 'kwakyoungchae', 'kingttoe_', 'hye_jin.jo', 'w.ssu__1583', 'ar_vneld486', 'younghee_yang', 'kang_jua_mom', 'twins_yeonseojunseo', 'dexter_new_home', 'lovely_leeyj', 'an_yul_0108', 'shinehaniwon', 'ohym562', 'kjkim999', 'carrot_.ts', 'dahyeyaho', 'jubong5763', 'm_y__0101', 'onyou_mom_daily', 'najochi', 'swing_ssam', 'thensummercametous', 'hajun_1014', '_hwangjian_', 'yeenalui', 'jeongsohyeon39', 'traveler0532', 'sisively__mom', 'kjs_jennifer', 'enfant_riant', 'minse741', '___geumhwa', 'samnazzang', 'j.___sa', 'cooking_life0', 'eunice_moment', 'jae_eui_', 'dongshili_', 'ddovely88888888', 'minse147', 'sungeun.bong', 'hrgoodjob', 'life_of__flowers', 'j__thinking', 'osyth55300', 'zionmom1004', 'romiicafe', 'lalime_kim', '100il_mom', 'jujulily_', 'sijjin_532', 'helen_wonhee.j', 'leehaeok7225', 'alicefriend79', 'gimhyeonjeong247', 'dw897700', 'han5183', '88iron_mist', 'd_park_bjj', 'seowoo_m0m', 'jinil_kumdo_lee', 'beautyin_87', 'star_ha_0704', 'hangsangsyalrom', 'sharabloom', 'applez_9963', 'jun_ho1126', 'ssh_sunny', 'wizardoori_22', 'yongseon0613', 'suna.yoon', 'limnon', 'mjmh0919', 'jung_sunh', 'sweetie_kkokkomom', 'heounboy', 'beau_fly_', 'imchristyw', 'daan_yoga_pilates_', 'sinjiyeon80', 'hwangeunkyung82', 'kysreds', 'dreamer_tory', 'serendipity_sun_young', 'sun_woo_1004', 'luv_wooubebe', 'haaanaaa84', 'letitflowlucy', 'ssongssong0630', 'hwang.deokju', 'nicolekim22', 'suyeon_wg', 'hoilove07aa', 'the.ban.ha.da', 'kosim_nyang', 'soeunjung_', 'kimcory3693', 'babmi1052', 'aelove_health', 'youri_1123', 'jongin7010', 'ah_choo1009', 'with_flower72', 'ihan.bae', 'ju___y88', 'seongeun_yah', 'bless_ing.b', 'ejyh1999', 'haihueho2002', 'jaei.jun_mom', 'jinwon_yuha', 'pangbong_ma', 'jjoung7436', 'kimm027', 'kyungminly', 'jyj282400', 'luceteyoung_', 'kong_e1001', 'parksd_1226', 'hyih_o', 'ssugi0508', 'grine_yon', 'id._hana', 'realman_donggu_mom', 'j_y_i_an', 'rachel_vivian_27', 'hmijin', 'ciy10210', 'jak3513', 'jieun_jjunmam', 'shleebk', 'sso02_0218', 'yesmile_ovo', 'jhsy_0415', 'cheer_va_starz', 'triplets_taejiseo', 'limchaein', 'showcase_82', 'powamung0921', 'hahapa45917', 'shoon_and_wood', 'luminous0418', 'ddoyeseul', 'hera_ayo', 'wldpqkqh2002', 'au_rang_', 'jisuk_bae_', 'hyelimseon', 'hyejin_0821', 'the.b_the.m', 'jyuny0121', 'leehyosoo77', 'jucciccom', 'ryeons2', 'diaryh_k', '9209_lim', 'boyeonlim0122', 'xoxo_dami0_0', 'happymin_jang', 'd_mi__', 'princess_yj26', 'siwoo___mom', 'yuls_momma', 'keunyoung7872', 'hyojooagnes_sookie', 'othoven', 'jme_muhhmuhh', 'kweonji_0512', 'ding_dong_s2', 'ggubam_x2', 'euna1979', 'donggu_bap', 'zeny_coodymin0', 'juhee_jung_daeun', 'psy_eun', 'yun_ha_86', 'soobin_sarang', 'on_yul_', 'gomidami', 'dramatic82', 'minae_1224', 'ssam.ne', 'wnsgml97', 'rena_yu486', 'oribangbang', 'shjy0729', 'wella_crownsunny', 'misuk_90', 'kong_nammae', 'reum0529', 'cheasomom', 'do_ha_0823', 'clemence_daybyday', 'k____nusia', 'iam___bbom', 'lovely_seohae', 'doobu0708', 'beardbear_illustration', 'weongyo10', 'sophia_5795', 'angelo_park_mokwon', 'rohee2019', 'lovelyzzmom', 'othinkman', 'jhsuk9147', 'hyunjung0718', 'bona_lii', 'yeonwoo___mom', 'jaeijkim', 'ddakgi02', '402_nayoung', 'lkhhwa0227']

    while True:
        account_setting_info = select_user(username=None)
        if not account_setting_info:
            logger.info("no account available")
            break

        username = account_setting_info["username"]
        password = account_setting_info["password"]
        logger.info(f"select - {username}:{password}")
        max_messages_per_day = 5
        bot = Bot(db_conn=db_conn, account_obj=INSTA_ACCOUNT_OBJ, max_messages_per_day=max_messages_per_day)
        bot.login(username=username, password=password, account_setting_info=account_setting_info, proxy=proxy, project_info=project_info)
        broken_items = bot.send_messages(text, target_username)
        target_username = broken_items
        # print(f"broken_target_users:{target_username}")
        if not broken_items:
            break
if __name__ == "__main__":
    run()


