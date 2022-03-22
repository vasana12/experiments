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
    account_setting_info = INSTA_ACCOUNT_OBJ.select_cookie_user_v1(username=username, max_messages_per_day= max_messages_per_day)
    return account_setting_info
#
def run():
    username, password = 'sp22064497', 'amdc2580!'
    proxy = f"http://user-{username}-sessionduration-1:{password}@kr.smartproxy.com:10000"
    # proxy = "http://5rfpjo4evhm0c8dx:ihzoneqam4p3vt2b@texas1.thesocialproxy.com:10000"

    ### 0. 세팅 : 프로젝트, 발송 텍스트, 프록시
    project = "taewha"
    start_date = "2022-03-18"
    project_info = {"project_name":project, "start_date": start_date}
    collection_name = "user_checkpoint"

    """ dm/source/message """
    text = get_dm_source.get_source_message(filename="taewha.txt")
    host,port, mobile_proxy_username,mobile_proxy_password = "residential.ipb.cloud", "7777", "customer-lsgr20040901-asn-20057-sessid-pCMf-sesstime-1", "UG2xaDXxC"
    proxy = f"http://{mobile_proxy_username}:{mobile_proxy_password}@{host}:{port}"
    # proxy = None
    #
    # proxy = None
    ### 1. 전송할 인플루언서 리스트 가져오기
    """ dm/source/hashtag """
    search_hashtag = get_dm_source.get_source_hashtag("taewha.txt")
    print(search_hashtag)
    if not search_hashtag == "":
        search_filter = {
            "user_followed_by": {"$gte": 4000},
            "$text": {"$search": search_hashtag}}
    else:
        search_filter = {"user_followed_by": {"$gte": 4000}}

    file_name, skip, limit, only_username,  =  search_hashtag, 0, 100000, False
    target_username_list = get_influencer.main(search_filter=search_filter, file_name=file_name, skip=skip, limit=limit, only_username=only_username,collection_name=collection_name )
    target_username_list = list(map(lambda x: x["username"], target_username_list))

    ## 2. 이전 프로젝트 에서 진행한 인플루언서 제외하기
    black_list = completed_target_influencer.find_completed_influencer(project_name=project)
    target_username_list = list(set(target_username_list) - set(black_list))
    target_username_list = ['californographer', 'sointotea', '9494_ho', 'threesunmami', 'soowainii', 'dsajkewklnk', 'thehyundaiculture', '_somodern_', 'won_umma_jb', 'o_o_kuza', 'hne._.yng', 'lalalabins', 'mippeuda15', 'stacey_by', 'mucksurun', 'yum._.piggy', 'moms_yomi', 'monthlydesign', 'oink.pick', 'yeonjinchu', 'think.daegu', 'heo.sudal', 'eunhyeee.__', 'masigetta', 'u_zingzing', 'minki_oo', 'look_at_hr', 'mi__eel_ceo', 'incheonlife1', 'rochae_unni', 'garami17', 'mingzpig', 'yammyomi', 'pt_storycafe', 'yulsister_1004', '_____network', 'pasteurkorea', 'bbang_casso', 'dauri_yangpyeong', 'youngsic.kim1004', 'violet_1025_', 'pinklemong', 'hamzy_1990', 'limmiae', 'pretty_good_tip', '_______hj___', 'jongran3405', 'parksuhran', 'hana.bi__', '_rami.mk', 'ksyou777', 'anesnam1', 'rang_x_bang', 'maison.danha', 'sujin.trip', 'mr_hwangdo', 'moonaoq', 'pro1909s', 'gayeonx_x', 'kim_miryong', 'zipbab_it', 'enjoy.suwon', 'hwang_stark_', 'isangmi420', 'cateyejh', '_pm.10__15', 'joniya423', 'hwang_celeb', '_ji.hong_', 'awesome_tat2', 'urawared', 'walkerhill_hotel', 'mudeng365', 'utaa_kim', 'pubone_', 'le_chamber', 'aekyunge', 'queen_helena_2013', 'goodlife_adventureclub', 'life4cut', 'ilovechampd', 'jungyun_diet', 'hadokwon2018', 'sunny_j.e.s', 'misspark_86', 'lawyeryuna', 'laurentallereau', 'merryzzy', 'god.oc', '_aplot_', '___ssena', 'busan_sources', 'yunho.lee', 'hwanggirl_', 'naobay_cosmetic', 'queenmun', 'happieststory', 'lemonadellen', 'k_jingu02.22', 'woongs.st', 'soi.soyyy', 'samyangfoods', 'bling_bling.shop', 'da._.jung96', 'bojoge79', 'haen.young', 'exnt.u', 'hryan_coldh', 'granolahouse_official', 'haram06200128', 'kim_mukbo', 's_minette', 'baek_mi_kyung_', 'soojin_p', 'angelstain', 'rohhccamp', 'hj__0628', 'koreanji', 'summerkitchen', 'yo_yo_seung', 'jihee335', 'kkkimej', 'jieun_0615', 'jungsik_inc', 'jungbokyoun', 'yousoon.k', 'nanasgolf', '___yura.___', 'alin_mom_jw', '_kook_ei', 'city_cut_', 'noon_ssup_bbal_4043', 'dusara_sinsa', 'reveyou_day', 'in.gwangju', 'layer1', 'tiger2013c', 'breeze__ri', 'jeehyun_2', 'sasumioppa', 'heelovelys', 'rogerrosales52', 'cowstory', 'bling_view', 'mong_nyang_cartoon', 'nailbar_thaodien', 'yurahee0205', 'foreverelt', 'xcara27x', 'moontommy', 'toto_aien4', 'momsstory', 'revewstory', '_bdplus', 'norupupa', 'sakenoueno_furachi', 'eat._.day', 'meju83', 'seoulhotple', 'angjjoo', 'myrimi', 'thinglead568773', 'choiquee', 'lys6613', 'kimancy_', 'icecreamcart1', 'yum___i', 'hissing860305', 'bodysoon', 'si_young_ha', 'zu.ma._.pic', 'all.about.incheon', 'videomug.vmg', 'yony_only', '_hye828', 'cherubchan0226', 'web_fooo', 'pdjin', 'suya.note', 'ipureumi', 'foodmin123', 'namoo_17', 'tvnmsg', 'iamssun__', 'farmfamfeed', 'pro_dj.lee', 'minish__master', 'fr6yyu7u', 'yu_s_k3155', 'ddddo.s', 'sunyoung__yoo', 'figoandfiga', 'ddabong_90', 'hani__koo', 'design_balkon', 'oro_ily', 'j_n_barbie_hj', 'yojung_dal', 'luii_xena', 'changeun9303', '_msgm', 'cafeartisee', 'solsol_home', 'jinheenn', 'hyo_ney.dd', 'kura_ming', 'n_eatchae', 'xxmidnight_', 'fatale_mauuu', 'healthy.ej', 'imsunni__', 'qlscmwlgp', 'bombom0322', 'jeung_hoon', 's00water', 'bookgoodcome', 'boogilc', 'nahoseyo', 'haneuline', 'available.90', 'dole.korea', 'haeum_choi', 'sweet.bebe_ayun', 'jenny___happy', 'budaejang_official', 'luvxvivi_', 'yorijori_ssaem', 'j_a_n723', 'nurii.94', 'cdw_k', 'seocheon_love', 'smilejjoo', 'thousandstone', 'mugunghwa1983_official', 'mingzzzu', 'good_tip_unni', 'sunsu_jiny', 'sinsun__fresh_', 'mirim_dh', 'rikunim', 'ashmemory', 'luna_unni_', 'muse_woo', 'blackbono_bonggil', 'stylist_hmm', 'ddomukzzi', 'kuk.u', 'jo.youngjun', '_joygift_', 'xunuxunuu', 'chicken_coke', 'j__mong', 'jaehak_seo', 'court_of_food', 'zzzbebemin', 'respond_daejeon', 'store_monsterg', 'ttinker__bell', 'velyrosy', 'songchelin_guide', 'sujanshakya3', 'lily_cocomong', 'mukbo_ssoom', 'keto__jay', 'browholicacademy', 'jungharu1988', 'ju__mee', 'yongwoop', 'hawhaw7', 'kingsbini', 'kkirrrrrri', 'kunny_k', 'havelyang', 'mom_house', 'jellyull', 'with.a_0823', 'mkhiya1', 'aiki_kr', 'simplay_golf', 'littlemiss_onew', 'madefannie', 'wawa.soul', 'sujung__s2', 'saphir__lee', 'bacchus_sister', 'napkinsmusic', 'heemee.tattoo', 'redpanda1423', 'ssunyjang', 'cheongdam_riho', 'bellissa79', 'ardeur._.13', 'bethejenny', 'jinvely0331', 'ln_brow', 'jy9389', 'gi_yoni', '0315__js', 'yooncarp', 'jasonisrabbit', 'jjoyonyy', 'lemonjiyoung', 'nyong_ssosso', 'popjangin', 'yumyum_brunch', 'eun._.z', 'lulurala_eunnara', 'bada_pinky', '_myownday', 'myforet', 'seulgi90__', 'sjwj0115', 'adela0818', 'eunsook716', 'ha_ruto99', 'u_jae.o', 'jinve1y_____', 'kid.moon', 'monguxx', 'pnlaeoinkz', 'camper_coba', 'sinbi_saju_tarot_', 'dxixeryom', '__haeun.lim__', 'sang_mukbang', 'genie_yoo', '_bebehouse', 'sjenapeian', 'baek.unni', 'masizzi_', 'travel_seasia', 'barudak_official', 'waikiki___', 'doong2_n_eruda', 'almong_cake', 'olivia_k__________', 'leovino_life', 'clownfish08', '_one_starrr', 'j0000d8', 'heeee.eee', 'anna.rima', 'nm01067732163', 'amiable_ssoyoung', 'sle__0220', 'nayul_bb', 'kkoma_yorisa', 'aurora_nail_1', 'song.2__', 'subeee.st', 'im_solarc', 'suumung', 'kkong_ji', 'jeju_bbo', 'digee904994', '00cook', '94__.hj', 'she.is.meringue', 'joliemaa', 'my.yugeon', 'hyebin.z', 'instiz', 'mjk228', 'halovely08', 'hyunju2469', 'choky333', 'here_whatwhat', 'eunaebae', 'matppu', '_linsun__', 'st__2005me', 'bambi_0428', 'shinjeo', 'on.__.on', 'annie.cong', 'meetingsue', 'myverygreen', 'reytry1100', 'lee_ssanghyun', 'byungtae810', '_bbmom_', 'k_da.eun__', '_cho.mmmax9', 'chaedaldal', 'hee_eun.y', 'hyejinan85', 'uk.ssung', 'lovecodyou_', 'the9_choi', 'simmukha_', '________abin_', '_____11k_____', 'yu.lim_v', 'yangsisters3133', 'ggoo_food', 'jian_damukga', 'twinkle_leeyeonhui', '_glamdew', 'hello_saige', 'yoonhyunsukzam', 'seung_hee.ee', 'jino_jjino_', 'hyuksour', 'akaraka00', 'minsungaid0827', 'jj_dragon', 'oct.15', 'luna_pic20', '_anothertime', '_hipzzi_s2', 'tasty_withessence', '_loveat', 'leeheejin_0_', 'needkss88', 'chefantoniopark', 'c._.love._.r', 'rebello_co', 'nudiblue', 'park.sju', 'doraemi30', 'blossomwendy', 'ji.h.y.e', 'mpbhong', 'sophie._.day', 'sj_parkzz', '_bornete_', 'a.m_11_00', 'hello___moonlight', 'miraeday_', 'housejihye', 'donghwan0510', 'travelmood.insta', 'j_mi_00', 'whd555', 'forest_korea', 'jjunimom_daily', 'thekitchen_dandy', 'stay_079', 'i_thi_el', 'mellifluous.food', 'thereportfactory', 'the.bestwang', 'cahiers_official', 'hwistory__', 'shj0154', 'withent77', 'hj____xx', 'siyoun_0428', 'seunghyeon2.lee', 'kkuni_mukzip', 'lacitpo_optical', 's.angsang', 'j_koo_foodie', 'wwywwn', 'meeso_da', 'molynmom', 'rina__maekawa', 'timmorrison715463', 'neoleo.j', 'grace_bbeum', 'ihyonam1271', 'young_a_world', 'candyminiatures', 'donghunchoi', 'm_a_s_s_o_c_e_o', 'ism_beauty_', 'balisuperstore', 'bambi_____i', 'jhyeon4423', 'sosodue', 'gamseonghanbok', 'adora37724808', 'milinilgi', 'woorizm', 'seouuun', 'i29i29', 'ox.dong', '______jung', 'gerrard_park', 'k1_linda', 'lovely_cmj', 'k_cene', 'diaryofpig_eo', 'manager_cha', 'rlqma5792', 'pu___reum', 'tamimamang', 'jayden_fafa', 'merebe_', 'ijs1909', 'jodaebi', 'malri__j', 'powerlife2021', 'luvhem_', 'jang_1211_', 'heart_caution', 'sc_choice_', 'heegela', 'olive_hyoju', 'ooh_jihee', 'happyssica', 'masahito.dai', 'hon_babgirl', 'emart_kyungsan', 'lyrical.98', 'studio_yeorang', 'elly_yun_kor', 'minnot_cw', 'deliciousjang', 'keunae.kim', 'ddok_market', 'seo_caso', 'call.you_mine', 'im_manttu', 'leaf._.j', 'glenda_mama', 'qkd258053', 'shlim204', 'hong_inn', 'geoje_story', 'ontamina', 'd0hye', 's2_barbielash', 'youmi_coco', 'wingeat', 'ji_hee1235', 'jun_sta9ram', 'traveladdiction_official', 'seoul_dental', 'mickeyjung79', 'wegonggam', 'dsg.market', 'indomie_kr', 'yjm7841', 'goodbam_scent', 'jisoyeong8320', 'salrim_e', 'samuel_smalls_', 'sangjung31', 'v_v.bbang2', 'joy_dreamseeds_ceo', 'nowon_nolja', 'k_ahyoon', 'ingenuehee', 'hannot_', 'gangneungpapa', 'a1_king_an', 'll__hana', 'jkeely_', 'joy_praise1004', 'girls_likey', 'withandbaby', 'jo_boo_04', 'baking__sy', 'xxbbom', 'eseoe242', 'ljh0226', 'safari_ian', 'yul_ove_me', 'viva_jei', 'foodcam_0_0', 'my_chanchan', 'noodle_gamblerz', 'j_songmi_', 'loveyoolucy', 'aria_35mm', 'yaru_yallu', 'ju_thanks_', 'the.potato.park', 'maisoncomms', 'wangyong_jeong', 'noma_cook', 'double_joo', 'jungnanggu_museum', 'lovejina12', 'yoon_sise', 'vivatravel7', 'eun_ha_81', 'namu_mama', 'j_twochan', 'i_kkum_', 'clubtsp_tuning', 'orbitbabykorea', 'very_good_tip', 'y__ulll', 'badain5653', 'ershovmsk', 'ulsan.hot', 'dalbitdaldal', 'fooddaegu', 'my_heedongee', 'thanks__yoon', '_w__style_', 'allways_b', 'jvivid_euna', 'se5.56', 'kjb05230523', 'saela1214', 'zuuulo', 'jj_howoo', 'j.ho.sung', 'cl__222', '__kar20', 'sungminhee', 'gwanwoo_guanu', 'songjiyeong3558', 'juno_youngin', 'ho__nong', 'jp.ring_studio', 'food._.diary_o', 'lhm.lll', 'kkomaeng0', 'ramis_home', 'guccim71', 'beomjumom', '__kkuna', 'dubai_lifestyle_x', 'k98728652', 'yoonsseya', 'landy_tree', 'olivia_huhoo', 'hwiviral', 'remyummy', 'frui_kr', 'hee_zomi', 'kyoulmna', 'doyunlove1004', 'pink.tape_', 'beccaworld_bhla', 'wongyo82', 'golf_doha', 'thefoody_room', 'haribo.sss', 'eunkim__', 'it__ti_mr', 'sotasty_workout', 'sutory84', 'instant_curation', '_abcdef_humor', 'riamom_2017', '97chan__', 'mukbini', 'sweet.jh', 'pmy9495', 'syjuknow', 'lliichachaiill', 'go_leo_kim', 'bae_unni', '6a.hot.place', 'you_gina', 'k.______.ss', 'gonzamorenegrin', 'vino____m', 'siktam_queen', 'unn.xp', 'mulbit_calli', 'dear_juha', 'view4two', 'ssggom2', 'ssoong__', 'hshs0327', 'kes8358', 'soluvluv', 'around_we', 'chu.roll', 'sosom_____', 'voguekorea', 'yunjeong_happy', 'siliconvalley.foodies', 'j_boboboa', 'ghj5034', '7days_beauty', 'babypastel_seongnam', 'on__gi___', 'yulrin__', 'lemonv33', 'swj80', 'xohaeni', 'nabi_sohyeon', 'littlebigmann', 'yonamja__iksan', 'coffeeafterbeer', '97crystalkiki', 'love_alice_210', 'seonu__mom', 'lia.umma', 'ddoddo191007', 'yoon_seo_mom_', '__hyelyn__', 'organicground', 'geety047', 'xxbuildingxx', '82review', '218_yh', 'bamtungi', 'htj3875', 'chloe._star', 'besty__harulab', 'mr.chalna', 'mihwa1127', 'jisoo_aru', 'gourmet.divino', 'young_sfarm', 'hyoju_9210', 'lim_pplove', 'vark_sh', 'sexyhonga', 'amberoguzofficial', 'weourus_wou', 'hyon_kitchen_', 'aileen21257', 'linen_table', 'dessert39_official', 'rapaelaena', 'honey_tae', 'kmaansur', 'jbirkin_', 'kkyu__peach', 'bebevely_', 'derama_clinic', 'chl_at', 'diondelphi', 'lec844.85', 'attorney_kim', 'sulo_gram', 'minyful', 'instafood_korea', 'hayjooo', 'yeelrin', 'leeminjoo5088', 'mine.d_1sik', 'catterjug', 'pbysj', 'jiwony_gourmet', 'tobecontinued90', 'deagul_deagul', 'mostasty', 'minibrow.kr', 'muksta_mxxmx', 'yeongweonhanhaebyeong2', 'ottina0915', 'olivia__diary', 'hansalim_official', '_hj1114', 'ma_bef', 'keixx_re', 'yiseo_luv', 'zipbanchan', 'y_ulll', 'winevling', 'gillie_0906', 'jjin0896', 'minz.love', 'jm.hwoo', 'followjof', 'whitestitch', 'ygeun0716', 'hyesuk.go', 'han.sang.o', 'to.mia_', 'sejun1035', '88_seongyong', 'yamyamchompchomp', 'dk_jj', '__rinnie', 'jmt_zero', 'man_fuku', 'rani_1027', 'arongmama', 'min_y707', 'millie_sy', 'netrefresh', 'on_july_11', 'agata0710', 'urban__nail', 'ziminews_table', 'motiple_min.a', 'ssodooi', 'neuf.f', 'standingegg', 'soonkkul', 'jjokkomi1002', 'sojin_mun', 'xxramxe', 'the_hyundai_cheonho', 'lka8822', '__seeyoutomorrow__', 'j__camper', 'momvely_class', 'sssoonma', 'stlong18', 'minjung44', 'pdh6182', 'food__rocket', 'alryob', 'kcc_egis', 'shinsekaids', 'bunnychamp_', 'kimseokbinn', 'gogiri.gram_chef', 'i_na0912', 'singni_asmr', 'themini_like', 'po.q.o', 'kwonmina_pilates', 'i_____k7', 'papa_gumpa', '_yeshard', 'wooill_kwon', '_4__fe', 'chonhill_shin', 'yoonaaaa.p', 'moonth_pro', 'koreafishing', 'miree_kk', 'copinso', 'onmoon']
    logger.info(f"총 {len(target_username_list)} 명에게 dm 발송 시작 target_username_list:{target_username_list}")
    if len(target_username_list) == 0:
        logger.info(f"인플루언서가 존재하지 않습니다.")
        return

    while True:
        max_messages_per_day = 5
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

