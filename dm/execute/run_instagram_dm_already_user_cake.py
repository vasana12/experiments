import time

from db import m_instagram
from dm.engine import completed_target_influencer
from instamanager import Bot
import logging
from dm.prepare import get_dm_source, get_influencer

FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
if logger.hasHandlers():
    # Logger is already configured, remove all handlers
    logger.handlers = []
logger.setLevel(logging.INFO)



db_conn = m_instagram.InstaDB().conn
INSTA_ACCOUNT_OBJ = m_instagram.InstaAccount(channel_name="instagram")
INSTA_ACCOUNT_OBJ.client_name = "admin_test"



def select_user(username,max_messages_per_day):
    account_setting_info = INSTA_ACCOUNT_OBJ.select_cookie_user_v2(username=username, max_messages_per_day= max_messages_per_day)
    return account_setting_info
#
def run():

    ### 0. 세팅 : 프로젝트, 발송 텍스트, 프록시
    project = "cake"
    start_date = "2022-05-19"
    project_info = {"project_name":project, "start_date": start_date}

    """ dm/source/message """
    text = get_dm_source.get_source_message(filename="cake.txt")
    host,port, mobile_proxy_username,mobile_proxy_password = "residential.ipb.cloud", "7777", "customer-lsgr20040901-asn-12576-sessid-xnoa-sesstime-1", "UG2xaDXxC"
    proxy = f"http://{mobile_proxy_username}:{mobile_proxy_password}@{host}:{port}"
    #
    # proxy = None

    ### 1. 전송할 인플루언서 리스트 가져오기
    """ dm/source/hashtag """
    # search_hashtag = get_dm_source.get_source_hashtag("puzzle_pet.txt")
    # search_filter = {"$text": {"$search": search_hashtag}}
    # collection_name = "user_checkpoint"
    # file_name, skip, limit, only_username, = search_hashtag, 0, 100, False
    # target_username_list = get_influencer.main(search_filter=search_filter, file_name=file_name, skip=skip, limit=limit,
    #                                            only_username=only_username, collection_name=collection_name)
    # target_username_list = list(map(lambda x: x["username"], target_username_list))
    #

    ## 2. 이전 프로젝트 에서 진행한 인플루언서 제외하기
    target_username_list = ['latige_official', 'bir__rr', 'yes_party__topper_', 'yena_i1i2_', 'm_j._.98', 'grine_studio', 'mzoodaa', 'll_sv_', 'cake.hadong', 'jgwoony', 'morehug.cake', 'da_bin0722', 'nxxyxh_', 'recepti_inessa', '_solicake', 'ppo_pata', 'nicethings_cake', '_midnight__cake', 'gr.eat_cake', '_dang.do_', 'joowon____n', 'khjthecake', 'h_j_i_n_0', 'khj_the_cake', 'haveawesomeday', 'bite__the__sweet', 'cafe._.cream', '_onika_cake', 'then.dance', 'woo____e', 'guum_rinny', 'rose_cake_house_official', 'sojjing', 'aurevoir.cake', 'aurevoir.au.revoir', 'jjin.__.b', '_ycake', 'cake_itda', 'cake_by.mi', '_tae_hyeok', 'joliday_cake', 'caki_ron', 'gripping_cake', 'momento__cake', '1lxxmimixxl1', 'athird.flower.cake', 'munei_cafe', 'jiny_ricecake', '_annaga_grum', 'f9_arn', '11_x92', 'siwol_ondo', 'kei_ith', 'millcafe__', 'kiaku__', 'daenggul_x2', '92dong_theater_', 'dearkeki_design', 'alliswell_an', 'lafloraison_', 'yemo_jeomo', 'gowoolyeon_cake', 'dazzling_cake', 'sqngmqk', 'somacake_', 'dessert_kanghan', 'alittle_candle', 'mollang_sea', '30mfn', '_april.cake', 'cocoshop016', 'onggi.jonggi', '_melody_cake_', 'shoesking_mall08', 'moore_ssol', 'uneahn', 'chareum__', '321_day', 'amelia__cake', 'sosoroum_cake', 'arthur_96202', 'jdeling_sn', 'leafmoonharu', 'this_very_day_', '_cafe1_5', 'classy__studio_', 'dasonykeki', 'abientot_nyom', 'mik_bread', 'love_twinkle_sky', 'cafe7_7_7', 'abientot_nyom', 'torty_assel_makanchi', 'someones_cake', 'dango_cake', 'hi.vely_cake', 'matildacottagebakery', 'haruin__', 'vivifiant_cafe', 'flan.cakeshop', '_hapory', 'uri_bake', 'cake_inni', 'pilate____', 'ancomer_cake', 'cafe_owns', '_petitchose', 'sugarpartycake', 'jjang6692', '_bloom_bakery', 'ikik_cake.cafe', 'sweet_juarre', 'make_spring_', 'pie.allday', 'lal_roro', '1004jjang', 'jmk5.4', 'seoinguk_australia', 'bbdcake_', 'miii_11030', 'foil_196', 't.hyun_0830', 'ehdgks2ek', '12maum31', 'pongpong07_', 'cake_by.eondong', '__dear.myday', 'paris_b8204', 'nana_ysan', '_won_0__', 'cafe_october9', 'cafe_daldal_daegu', 'alokdalok_balloon_cake', 'dalcomhannal', 'ricecake_dajung', 'cakeshop_official_', 're970_bbang', 'sbmy__08', '__lucky_cake__', 'dorothycake', 'baegjuhyeong8', '2f_radio', 'fionahughes36', 'kounkounn', 'dongdong_candle', 'grangcandle', 'by.boramm', 'songhyojeong686', 'sugargreen_changwon', 'leeseungah.studio', 'baocake', 'sweetrose_sw', 'johnmetcalfe6', 'case.by.cake', 'bliss_cake6660', 'efrosiniiamaltseva', 'gardenonthecake', 'hm_ouo', 'forever_mall333', 'cestlasortie', 'wizgram_3005', 'wizgram_1_2', 'sheedesmhnf12', 'dianearnold387', 'geniegenie_2', 'songjunweon82', 'baegdohyeon73', 'wizgram_on_kk', 'wizgram_ad_1001', 'donnamackay456', 'doseongjin849', 'yeomboram82', 'thomasbailey5096', 'andrewcameron466', 'geumdaehun88', 'teenaezecoiy20', 'oliviaclarkson16', 'in___sharp___beu', 'abigailnolan272', 'baeggyeongmin95', 'owenjohnston745', 'sungsil_king', 'cake.catalpa', 'nathanpiper98', 'gimjunyeong7797', 'mcshatepgqm23', 'seoleunju35', 'evangill81', 'weondonghyeon407', 'nar.cake', 'yuunnzz', 'ovenery.cafe_', 'danhana._.cake', 'rani_bakingclass', 'dylanince5', 'virginiapeters9190', 'teddy_3aby', 'sinol_sinwol', 'rosemetcalferrq', 'nicholasclarkson6', 'gracespringer78', 'connorbuckland88', 'colinwilson49', 'andrewcameron466', 'jenniferbuckland762', 'yangyang_violet', 'rynicake', 'maumcake', 'click.with.cake', 'gooooom_day', 'duetmini.cake', 'bbojjak_cake', 'wizgram.02', 'josephhill5171', 'hwangjibi8', 'ceonseongceol19', 'hacanhyi30', 'bergervalencia87', 'uuram1', 'wizgram.dd', 'syeonkk', 'penthouse57234', 'naran.reoje', 'dianawallace291', 'herwigcameron44', 'ryugiseog37', 'herwaldcantu352', 'vilnarabmoasoco', 'trasiphfreechderliazin', 'spiridonelizavetin025336', 'cleopoole93', '501_party_room', 'isekeglushchenko', 'valimkarpachev19868109', 'sheldonlimon', 'langstoncrawford19', 'darieljoyce32', 'maxmay83', 'jiyoopapaya', 'royalcupcake.co.kr', 'rebeccarandall785', 'germirevstratov19895007', 'yeoeunju53', 'votre_cake', 'leas_macaron', 'hyunwoo.keem', 'reale_sns_', 'oh.soo', 'krhjy70', 'hajanghyeon52', 'snsmall_kr', 'byhwyh', 'orangecakemaker', 'nyun2ru91', 'instart_kr_h', 'morizeti318781', 'tipara457464', 'torterne521879', 'ceperspredunarif', 'orizeneu470261', 'samhemmings15', 'alexanderforsyth2', 'yejin_jjang', 'twojjbaking', 'thedameun_', 'songwoo.cookingart', 'risoybqn5', 'nathanpiper98', 'miel_dessert_', 'kkomi_lavu', 'ieul_ddukmaru', 'heatherellison178', 'cho_ively', 'boonhong_cakeshop', 'austinross785', 'angelahunter246', 'menwgirl', 'conradseoul', 'instart_kr_z', 'onemade.cake', 'mukgofood', 'zoneoutcafe', 'changsindangcake', 'nicolacarr619', 'fleurfleur_kr', 'seogwipean_official', 'instart_kr_o', 'instart_kr_15', 'lalashu_cake', 'seohyojeong68', 'ca.rolharris670', 'smosorfiw8', 'morebake.official', 'j_rice_cake', 'ingi__hyuk', 'gweoncangho80', 'seleathea155', 'lalabom_flowercake_', 'instart_kr_12', 'instart_kr_10', 'instart_kr_13', 'instart_kr_11', 'instart_kr_w', 'wake_a_cake', 'instart_kr_n', 'sxx__._hxx', 'instart_kr_a', 'k_______su1004', 'just___onebite', 'jacobbuckland37', 'happy_nhong', 'flower_tteok_cake', 'dorothyhunter168', 'blanc_atelier_', 'instart_kr_s', 'reale.sns', 'hako_cake', 'loliloli_cake', 'theohsroom', 'cake_raphah', 'daol__ricecake', 'sophia_3_24', 'miflrim_cake', 'guybjfi', 'rustag__', 'merryday_cake', 'giseonmi317', '_creamdiary', 'momocake79', 'kak00011', 'shethesmijcr1', 'mama_a_ri', 'irenebower91', 'tayshaezvhjif3', 'shesloufsoccc1', 'sebastianforsyth2', 'nakwon_dabang', 'gobakery1120', 'ellacake_91', 'dog_chopchop', 'daldaroocake', 'bb_berrybottle', 'amybailey653', '_sub_2__', '_cakechu', '_.rosiebrown._', '_0228_yool', 'cafe.eondong', 'fat.dog_fat.cat', 'merrier_cake', 'sinol_sinwol', 'hyun_a_22', 'nataliedyer8738', '_sun_cafe', 'dorothymathis1659', 'happybearday.cake', 'teedos_room', 'yellow_cake_nbj', 'cozy__domo', 'uniii5656', 'abo_dessert', 'cafe_usreumdal', 'usreumdal_dessert', 'ssoheemaru', 'mijak_baking_010_4002_3249', 'doong.d_de', 'cafe_sum_in', 'barista_jeong', '_butter_layer', '28_eun_j', 'kirakira_kitchen', 'jeonghwa90', 'cafe___foret', '6wol_uri', 'thankyou_today_', 'jomi.___.cake', 'vanhae_dessert.cafe', 'kekibox_', 'az_.queen', 'exciting.club.02', 'harugadalgona', 'atelier_eungi', 'bongqq', 'romantic.you.cake', 'thisisbxxm', 'suolnn', 'bliss_cake6660', 'blanc_b_cake', 'baejuhyeon1207', 'kak00015', 't_y__jihyo', 'leas_macaron', 'inearnest__', 'di1011on', 'caron_choi', 'abigailnolan272', 'sunnyplace_cake', 'flower_tteok_cake', 'atelier_eunhasu', 'daldaroocake', 'annantorte', 'brille_bijou', 'mama_a_ri', '_today.news_', 'gangjuhyeong349', 'gna_dessert', 'zoetbloem', 'yeonghangsang', 'thankyou_today_', 's_kelly62', 'pila_jiwon', 'oven__onii__', 'modudagatea', 'miu_world', 'minseo.kim.374', 'mayrose_cake', 'mcsesmeignb9', 'cake.d_', 'cafe.deep.dive', 'all_pretty.da', 'urbanartart', '_merryclay_', 'seol_mong_dang', 'chuuka.official', 'wandonesia2016', 'doyo_on0911', 'woori_place', 'macamong_official', 'korea_matzip._', 'haramkkk', 'daldal_chucheon', 'dal.b_cake', 'creammin_', 'yeongja7964', 'hwi__420_', 's_hy741_84', 'daks_baking', 's_weetdecember', 'ivy_cake_', 'sattangsiru_rice_cake_studio', 'royal.ltd', 'hotdeal_moa', 'kungsister', 'strawberrymoon___', 'roenne_cake', 'ok_dang_coffee', 'may_cake_tarte', 'luv.seojoon_mom', 'honne_baking_72', 'cafe_hansbakery', 'cake_pino', 'cafe_capernaum_', 'cafe_maybean', 'bo_ring_1215', 'anne_coffee._', 'gabongot', 'ssohee222', 'jerry_x_cafetour', 'ubooming', 'bella__mood_', 'all_good_tip', 'hyun._.g14', 'kkubeun_kkakka', 'petit_eunkyung82', 'eunhasu_sweets', 'cafe_howareyou', 'mayrabbit2017', 'ssssmmm090111', 'bredor.r', 'saerok_coffee', 'dohwazi_miryang', 'megafollow_korea', 'cafemoonight', 'hang.a_cake', 'gonggan.interior', 'patorong', 'leesj7292', 'do_ah0222', 'ancre_cake', 'moojinglog', 'torikeku', 'flowerlove_bora', 'snowdrop.korean', 'happy_molyday', 'quentabelog', 'joys_kitchen', 'cherry.oo.cherry', 'vanvan.cake', '7o1_zip', 'minimini0819', 'tama.s_hyeon', 'ssun.hye', 'huizcah', 'dorothy__ricecake', 'jinyzzac', 'mung_third', 'mongeegram', 'gimjeongsug6330', 'seojung__p']
    black_list = completed_target_influencer.find_completed_influencer(project_name=project)
    # target_username_list = list(set(target_username_list) - set(black_list))
    logger.info(f"총 {len(target_username_list)} 명에게 dm 발송 시작 target_username_list:{target_username_list}")
    while True:
        max_messages_per_day = 10
        account_setting_info = select_user(username=None, max_messages_per_day= max_messages_per_day)
        if not account_setting_info:
            logger.info("no account available")
            break
        username = account_setting_info["username"]
        password = account_setting_info["password"]
        logger.info(f"select - {username}:{password}")

        bot = Bot(db_conn=db_conn, max_messages_per_day=max_messages_per_day)
        bot.login(username=username, password=password, account_setting_info=account_setting_info, proxy=proxy, project_info =project_info)
        broken_items = bot.send_messages(text, target_username_list)
        target_username_list = broken_items
        logger.info(f"broken_target_username_list:{target_username_list[0:10]}")
        if not broken_items:
            logger.info(f"no target_username_list ")
            break

if __name__ == "__main__":
    run()

