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
    project = "kasino"
    start_date = "2022-07-04"
    project_info = {"project_name": project, "start_date": start_date}
    collection_name = "user_checkpoint"

    """ dm/source/message """
    text = get_dm_source.get_source_message(filename=f"{project}_2.txt")
    host, port, mobile_proxy_username, mobile_proxy_password = "residential.ipb.cloud", "7777", "customer-lsgr20040901-cc-US-sessid-oBGP-sesstime-1", "UG2xaDXxC"
    proxy = f"http://{mobile_proxy_username}:{mobile_proxy_password}@{host}:{port}"

    # proxy = None
    ### 1. 전송할 인플루언서 리스트 가져오기
    """ dm/source/hashtag """
    search_hashtag = get_dm_source.get_source_hashtag(f"{project}.txt")
    black_list = completed_target_influencer.find_completed_influencer(project_name=project)
    black_list.extend(['dong_ta_ni_1995', 'shewweerds_', 'hoo_n_mom', 'y__lovey', '3you65', 'doiioe2321', 'ds6457', 'kih0ng2', 'mohsinalisagheer', 'jx.___.xxhxx', 'nara_ss8989', 'momizi_0826', 's_usqhdhdh', '4bool__', 'pepp__eroni', 'gimjunyeong1925', '__asdfg2__', 'kimjangood', 'rarasa_ra', 'wngus_34', 'wonchonkim7', 'dduwinkle', 'cuuty36', '72fdsfds', 'shortcut_jy', 'yang8653', 'ggyu_wf', 'love01_baek', 'floow7121', 'nieve__j', 'saku03nao', 'haha.hwa', 'sanghyi4162', 'insta_s_h0054', 'dro.pin90', 'kangdric10', 'donggeun265', 'hyo._.rim_', 'z_o.o_h', 'gg_mm_ii95', '55cscs447', 'q__real0315', 'chacha_qwer', 'tifi.fiti0', 'zzzzll_90', 'werhureckm', 'thetroreds', 'in_water_92', 'moon.ji_ho', 'spsp00998', 'poto_cheolung', 'doui.iuob', 'zczc8800', '1996.6855', 'uimran59', 'park_yonghoon', 'b.d_checking', '981031_archive', 'lymhcr', 'joonsub123', 'seuk_0617', 'qiwu789', 'tggg_tt', 'k_joon_2', 'yeinejilong', 'seoye0n._', 'yujinaa_._', 'all_rounder_st', 'going.dd', 'myeongjun9611', 'heesuk9597', 'baek0404_pal', 'ii22i.ii', 'jjjjomimom', 'miumiu.0099', '6754.aqsw', 'iii_back37', 'boardpaik', 'ii.yy.ss', 'kimkorea09', 'allday_park10', 'tartesos24', '99__seohee', 'hyer2m__', 'darem_korea', 'pictorym', 'rang_eorange', 'kim_hyo_jun.1976', '14alansmith', 'tarrazu2', '1994_729', 'wahee5904__', 'saboten_0130', 'jay_jbfc', 'parksoowhan', 'gyo_dami0419', 'sh.__.0331', 's____oobsoob', 'eden_04.27', 'rado.ma', 'god7son', 'jiae_08_11', 'ultari_company', 'o_in_jeong', 'duck_mi0', 'maideuts', 'limhwan85', 'bacon_di_26', '__ryjuuu', 'im_am0443', 'shine_he_jae', 'cs_5118', 'mino02250731', 'songpongdyu', 'chengna_jjanggu', 'gold_won', 'hgyeong2', 'th___89', 'ghyog_75', 'seonghwanlee800428', 'dubai_car_vip', 'jonggeun78', '_hai.mom', 'songg4', 'yewphur_', 'greatraul', 'k.___.06_7', 'k_dhh_', 'kwang_hyo2', 'dd_yeon11', 'ebbuda_nail', 'jsilvereun', 'restore_1969', '000___yyy', 'a_zzzero', 'm5_jun', 'iji__kim', 'qyqyqy1133', 'hamyang_sports_', 'ip_78989', 'ar_han_0709', 'luv.hai', 'xriverrxx', 'joyjoy6696', 'sandy_danby', 'the_ig_areum', 'sikdorak.gram', 'honeybeeneedsflower', 'ims_0330', 'jhyuklove._.1031', 'lami_77r', 'trainer_monster', 'normal_shinmina', 'cfcf7942', 'ya_kim166', 'ddddd_030', 'hyeongu_park', 'jeonghwan3493', 'xodn5665xodn', 'ryeon.t', 'jang_seoyeon77', 'rijamong94', 'nu_gu_488', 'cpt123123', 'ssuni1107', 'yongmin_zz', '9vo._.ov9', 'oh_sumi12', 'bidadari0822', 'seo.___.a', 'tkddus1557', 'swhan30733', 'nariyu_sinu', 'lucky_pear1', '_90.10.18', 'haktae_e', 'jwoota', 'youngsunny83', 'myungsu.kim00', '__kimyang_', 'junghoons_', 'jwoong28', 'two_bom', 'babypori', 'id050505', 'knana7573', 'jung_hyuk88', 'jeon._____.10', 'hyeongsub_94', 'hyejin96_o_o', 'chaeuny_b', 'pig4233', 'ria_yeji', 'hayeoni8653', 'tomato_325', 'mingyeong_seo1', 'secondtree_2ndtree', 'taeseul__mom', 'sugja8718', 'shanghai.angel', 'sweatlife_jungmin', 'junhyeonheo6853', 'seolbin90', 'hyuksu', 'rachel.idea0217', 'hyehyuniii__', 'dadam0723', 'jiseon_jinny', 'bella.c_910', 'you_genieee', 'cn__papa111', 'sorrow8302', 'journey___a', 'dhkimmmmm', 'hantaegseog9', 'hae_s000', 'y.j.0109', 'sam_enfj', 'yangmuccu', 'wnsgh8605', 'nuclear_jaehyeon', 'rkawk4520', 'gnana7828', 'gaae_k_1210', 'mytem_space4919', 'hypark0915', 'b__suny', 'minseop1294', '04_wlgh', 'ssun___v', 'naturalbox_1st', 'lee_hy_tazo', 'ilhyeokim', 'loidy7749', 'jiani0702', 'yyyyeong29', 'kaenghwa_', 'wiryong1925', 'jocungyeon', 'lee___jongh2', 'fresh_hye', 'kek.0828', 'leestar5959', 'fita_joy.j', 'fita_soo', 'beom_ori88', 'kej_0414', 'd2._.silver', 'inaxtti', 'yoonjae_emoo', '26_hye1', '0.1.s.y', 'sejin0619', 'haenique', 'hobbang1013', 'jinnnn__2', 'tosaloveyun', 'happyhaweon88', 'jeagillee', 'paul.im', 'chanhwangbo', 'diver.junchi', '_taegorism_kang', 'ghdwogus00', 'rkdalswjd07', 'kwakyoungil', 'namgwangmin81', 'doodoo0210', 'ms_yumosa', 'kkeuntae', 'seo_chaeeun88', 'ryessi59', 'jiji_jh84', 'jjae_jjae._.88', 'skoorie', 'eunjisla', 'power_star1697', 'mono.7182', 'yorinee.han', 'choi.jihye3', 'enfenftpt223', 'smile.__.jei', 'kyeongkeun.pak', 'dear.moon.sj', 'j.h_hwang_1984', 'hyemi.l.kim', 'dnfwlq2328', 'mmxmee', 'oguning', 'poseuteumaendibi', 'bitget_official__', 'zzang_ddeok', '03.17m', 'bitcoinlove1', 'aguas_de_marc0', 'onmoon', 'kirovaada', 'sidirkevictdyafc', 'open_portfolio_92', 'wd_stock7', 'stock_jumsang', 'jjiwoo__', 'stocklightshadow', 'finance_delivery', 'ha5_stock', 'coinoon', 'imtaeho11', '____jin83', 'bogomom', 'appss.004', 'mentalisall', 'e_trend_', 'lifeisgambling_', 'nodefeat88', 'serendi_pity0109', 'hi_semari', 'norenja153', 'wealthcat_', 'eroomgroup', 'gimminseog1398', 'samkim333', '0909_ssola', 'ilpyung', 'ugiii_iii', 'korea_giga', 'build_up_l_b_l', 'mns.k_', 'whyrisingstock', 'alphasquare_official', 'designgmkr', 'bb1_o1', 'love_joosi', 'min_woo1984', 'wikistock_', 'wzzi41', 'toou704', 'kopop002', 'annkp001', 'beauty_ccuu.03', 'betget.coinku', 'rich_j_h98', 'kim.nietzsche', 'stock.toon', 'fxrich_banpo', 'buja0127', 'fxbt2020', 'goodstock123', 'minimax.youngandrich', 'finance_2030', 'mutantgyoju', 'nonstop_investment', 'sarang839405', 'bangtan_stocknews', 'plz.what0011', 'heo1.01', 'gopeun', 'ezzi914', 'roou200', 'bestcoinlab', 'invoik', '4ang_d5', 'k_12_b_s', '9.cavani_', 'novarealinvest', 'wannabe_leader_', 'people.on.bridge.investment', 'hsasset_official', 'hwang_hyun_hee', 'yuyu999680', 'asset0901', 'pailateawl', 'no1hts', 'solution_jpro', 'soonsal.brief', 'good___hts', 'official.muto', 'hjk11136', 'jkl79094', 'marydecker481.10', 'hee_won86', 'ileesa1224', 'doll9_minsub', 'ohturtle', 'oyonghwan123', 'postshare_official', 'ddon_guri', 'seongtaek.lee', 'jilradcam', 'gej5558', 'bcoinbot', 'sangsoo_86', 'upseedmoney', 'trader_stonewhale_', 'choisun_academy', 'bagjihun498', 'ssong.2721', 'harry_seokbonghan', 'cooksta_gram', 'jinzza36', 'zzl_psa', 'kk._.3636', 'coin__1144', 'ki.lol2', 'wirye.29.9', 'lynoss1021', 'lgtooza', 'maniemboy', 'leash.official', 'koeran_business_association', 'bitget____coinbit', 'freesia_hs83', 'c_doosik', 'kim.pearl._.a', '__.min.happy', 'apex_official_korea', 'gag_seung_woo', 'ultimate_plan_b', 'nostalgieboisart', 'lya.0714', 'weather_stock', 'coinman627', 'woo_2062', 'e_tomato_kdh', 'trlink03', 'hyundai_motor_securities', 'udyr_stock', 'jis_iki_nn', '3x_people', 'chu_rini', 'stock.golf.si', 'best911015', 'kuma_jcy', '_an_anteater', 'skywpans', 'sejin_delight', 'dicjensiu672', 'modu__park', '220221doklip', 'lion_camping', 'faststocknews', 'vip_haejin', 'antua_com', 'lomon0191', 'soonsutti', 'redzacal', 'psj1190', 'coin_doctorbtc', 'suhyun078', 'seok_hwan720', 'dream_come_true_noh', 'wise.pill', 'hyun_ju1985', 'kangcfa', 'danta_sh', '_investor24', 'jumeokdal', 'stock_sngnoopy', 'coinhouse.official', 'mit__zziyoon_7', '_j_oo_ah_', 'wd_cointrader', 'park_seong_keun', 'hotaru_gumi', '_whereorwhen', 'hey_jayday', 'papadal_insta', 'co_yo_nam', 'ddd_royce', 'bul_gae_mi', 'yu_templeton', 'lucky___eun', 'l_daeyoung_kim', 'pocket_kr', 'saint_way_token', 'dongastock_com', 'navibook9', 'zotooth', 'ming0_0h', '_jeonpro', 'high_one_best', 'study_4days', 'leekyubong_', 'kangmang612', 'dajung_book_', 'stockjeonsa', 'happyhunt53', 'jager_bokmb', 'nana_salon_stockinvestment', 'kim.kwansik89', 'jj_dragon', 'yong_stock_', '__yyuuzzuu__', 'namdukwoo', 'teacher.tigerbtc', 'tmrw_sunshine', 'bujaumma24', 'yemunbook', 'donjoha_invest', 'angelasim2020', 'goodmorning_bae_pro'])
    search_filter = {
        "user_followed_by":
            {
                "$gte": 100
            },
        "avg_like":
            {
                "$gte": 20
            },
        "$text":
            {
                "$search": search_hashtag
            },
        "username":
            {
                "$nin": black_list
            }
    }

    file_name, skip, limit, only_username,  =  search_hashtag, 0, 500, False
    target_username_list = get_influencer.main(search_filter=search_filter, file_name=file_name, skip=skip, limit=limit, only_username=only_username, collection_name=collection_name)
    target_username_list = list(map(lambda x: x["username"], target_username_list))


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

