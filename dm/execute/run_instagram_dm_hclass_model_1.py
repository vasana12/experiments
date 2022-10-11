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
    account_setting_info = INSTA_ACCOUNT_OBJ.select_and_update_user(username=username, max_messages_per_day= max_messages_per_day)
    return account_setting_info

#
def run():
    ### 0. 세팅 : 프로젝트, 발송 텍스트, 프록시
    project = "hclass_model_1"
    start_date = "2022-09-04"
    project_info = {"project_name": project, "start_date": start_date}
    collection_name = "user_checkpoint"

    """ dm/source/message """
    text = get_dm_source.get_source_message(filename=f"{project}.txt")
    host, port, mobile_proxy_username, mobile_proxy_password = "resi3.ipb.cloud", "9000", "MrIlCvzYImHc0I3t", "wifi;us;;;;"
    proxy = f"http://{mobile_proxy_username}:{mobile_proxy_password}@{host}:{port}"

    # proxy = None
    ### 1. 전송할 인플루언서 리스트 가져오기
    """ dm/source/hashtag """
    # search_hashtag = get_dm_source.get_source_hashtag(f"{project}.txt")
    # search_hashtag = "식단 다이어트 헬스 웰빙 먹방 운동 푸드 건강 뷰티 간식 디저트 공구 맛집 그릭 요거트"

    black_list = []
    # search_filter = {
    #                     "user_followed_by":
    #                 {
    #                     "$gte": 100, "$lte": 20000
    #                 },
    #                     "$text":
    #                         {
    #                             "$search": search_hashtag
    #                         },
    #                     "username":
    #                 {
    #                         "$nin": black_list
    #                 }
    # }

    # file_name, skip, limit, only_username,  =  search_hashtag, 0, 1000, False
    # target_username_list = get_influencer.main(search_filter=search_filter, file_name=file_name, skip=skip, limit=limit, only_username=only_username, collection_name=collection_name)

    # target_username_list = list(map(lambda x: x["username"], target_username_list))
    target_username_list = ['flower_hana.kim', 'florescence_915', 'fleurbiin', 'fabrizios_carelli', 'fillitfeelit', 'february_12_film', 'fang_jins', 'ezgiiparlar', 'fafa.styl2', 'fay_walson', 'eveningjun', 'eunjeongwon', 'estephkim', 'enjjo0203', 'energy_sim', 'em_02_ily', 'ellgi_kr', 'elhrk99', 'eldalotegram', 'el_seraphic', 'ehdud_c', 'ekologinya', 'ekiel.xxi', 'ecegizzem', 'edyna_lee', 'e_minjisarea', 'dsjke612', 'dxng_h.x.n_', 'dovvivi', 'dpflal0', 'dorrimur', 'dongnesamchon', 'dodbdus', 'dohyunmt', 'domnguye', 'djwjfdjwjfdyh', 'dll_0_0_lb', 'divl.m', 'dlstod3', 'diffracted_world', 'dekadantz', 'deemaazar1', 'deellesl', 'db_tldms', 'ddoomlovesyou', 'dawo.o_n', 'dara_dawson', 'dan_2l', 'dalnara2021', 'dalgona.a', 'daexkwn', 'dadabiin', 'da_riia6368', 'daehanmingugceobageunju', 'dabingloriason', 'daegu.boss', 'd.rinkss', 'd.haae', 'crazy_art_kr', 'considiration', 'cocoyeun', 'coffeedvein', 'chun_liiil', 'cjtygirll', 'chohyehee', 'cherry_vroong', 'cheon_ill', 'cheniii____', 'champian_woo', 'chaerini_kim', 'chaedaming', 'chaeyeon_oni', 'ceoinceo', 'cc_rivera12', 'casmika_', 'caratmom_', 'carthe_garden', 'casa.snap', 'carvalhotay_', 'callmemicsi', 'call.ray', 'c.keem.c', 'bxeoki', 'bul_meshhhka', 'bpbom_', 'brendentheguy', 'brililili', 'bonaguure', 'bombi_.529', 'bloom_by.bloomy', 'bn_sg2021', 'blackcastle1102', 'beomsu_kim1021', 'bible_hyeon', 'benneirret', 'bdayjulyfifth', 'bagcaerin394', 'babyseungji', 'bae_ze_ro', 'bae_si_jun', 'b_nabii', 'b_b_o______', 'azaliya_sultanova_', 'aygunaml', 'arminnan02', 'arina.chzhen', 'areumyul', 'anndiiina', 'anxlvnne', 'anya_klsv', 'aramdowm', 'annaaldobaeva', 'antiqami', 'anna.sharapova_of', 'ansley_gs', 'ar.iiiina', 'anelia_yang', 'angelaaa_n', 'ammodel_mgmt', 'akakwldrk156', 'ajh__1114', 'aj_niel1153', 'alina.one', 'allisyeli', 'akraynya', 'akiinela', 'ahkha_nguyen', 'aenfia', 'acemi.shop', 'addtask112211', 'aandre1j', 'aakarukukagayaku', 'act__ssang', 'a.yxuna', '_zvkii', 'a.ninditaa', 'a_s2sirok', 'a._.hyeoni_ya____', '_yh_lim', '_starlikegold_', '_yasminato', '_sun.e22', '_y.hxx_o._', '_uzzang._.boys._', '_redpoem', '_seongjae_', '_nata.l1', '_se_lee', '_my_l__', '_oct27th', '_marilvs', '_kam_arr_', '_meen9_', '_im_your_muse', '_im_liza__', '_homa.na_', '_jahajh', '_girl_evdokia_', '_dostoevskay_', '_dlskarud', '_dillsm', '_bbibbi0', '_aross.s', '_aniretake_f', '__jiwoong__jiung', '__sxx_y', '__diljon', '___j_won', '____l.e.a', '____hyeok___', '__.tra__gedi__enne.__', '_4.29kg', '_._marinb_._', '9wol___', '888noeyos', '7ven_star28', '5k12d', '50yeon', '7cxss', '6bad_ass9', '4co.photo', '305.lv', '38kwangtae', '2_u.m_0', '2jun._h', '2j_pic', '2525lol2525', '2018.12.29_hong', '27della', '1_chu__', '1kimvika', '177_dangh', '173.2_seul', '193cm_kbs', '172.2_', '1012_._h', '0h.j', '0x1magic', '02gy_.uri', '0716_sh', '0413zz', '01h.pdf', '0320______', 'uliana_shastovsk', 'loen__snap', 'jiminz_girl', 'official_vchan', 'kfashion_kim', 'myhappyjb', 'model__j_heekwang', 'changha_fan_robi_chanwoo_', 'annwi.1', 'veravonmonika.hyungjun', 'hamsu_graph', 'dany_amso', 'yunonah.p', 'youngju0319', 'yesoling_', 'xu._.nsxo04', 'worldmodelskorea', 'waaleryy', 'vseik', 'ui_o4xz', 'tove4dead', 'soom__da', 'sicaaaa___', 'shasyahwang', 'separk_', 'resiancious', 'pramecomix', 'poliaaaaa.m', 'photo_lim.hj', 'parkha.mint', 'parkyium', 'o_eun___172_', 'nohyungang', 'neverpatheticeveraesthetic', 'muertreza', 'min.ah05', 'mdi_models_official', 'loveyou__korea', 'lucasj11200', 'louis_leem', 'lim_shyn', 'lindsay031900', 'lilynah.star', 'lila_agrestee', 'lil.hyee', 'lfinoke_insta', 'juno_jeongwon', 'jung__hyun03', 'ji_hwan_c', 'ji.missss', 'jane_is_loved', 'iuhgnakeel', 'ironrri', 'instacool_nancy', 'indahsariahsan', 'if.pic', 'i.ran.g', 'hy.portrait', 'hecado12', 'hadilusaf', 'gweonyeongjin4217', 'gtforadia', 'geraldinemateos_', 'eun.______.xx0', 'elizavatocka', 'duduka_q', 'drow_on', 'daily_hyun1024', 'codycheeseman_', 'chenjianstudio', 'cha_moonwhan', 'bunnyyyyyyyyyy_0911', 'bw_geony', '_isophiech_', '7._.lei._.7', '79_11_18', '18ee.oo', '13__green_eyed_13', 'x._.0m9', 'winsome_hyunny', 'taeseop84', 't_wnim', 'star_like_h_t', 'sekusi2', 'saradcamp', 'qo_op___jj', 'o_jin.n_', 'model___izil', 'miss___lady___93', 'mirjalolovv', 'leralii_', 'kvr_namu', 'korea_visa_consultant', 'kdk_0422', 'joonhwan0l', 'jeong_se_il', 'dong_gun_young20', 'doffy_fb', '_silver_daughter', '175_ryn', 'yunpppal', 'yeo_n_hun2', 'xae.hu_n', 'rora_sa_y', 'miziphoto', 'minjjilash', 'mine_manju_', 'mango_ringo05', 'leejsk_0418', 'le_e_ho', 'kkim__han', 'hayan_yance', 'g_a_y_o_u_n_g_01', 'fashion__mon', 'e_nah_410', 'cat._.shampoo', '_real__._.o', 'ssong__0122', 'se_ah_kim', 'photo__unba', 'parkseungje93', 'mine_manju', 'ijiaagimodel', 'hojung080312', 'gabin_0712', 'dodam.snap', 'al_official.p', '_tti._.amo', 'shiny_life1204', 'pum.seongmi1233', 'mj_seungbin', 'bubbly__jumi', '_1hyol._v', 'hj_daily_', 'aoi.gongjooneem', 'anlook_jho', 'juniwoni_1', 'dante_magolden', 'k._.delay_', 'whotdw', 'dfghj043', 'photographer_ena', 'zzv_zl', 'yullla_j', 'ysestemban', 'youxeun', 'yoonsoota', 'yeunseon_', 'yardenau_', 'xx_xibacw', 'wktn_02', 'wercegtty', 'wanna_buy_fuji', 'vinterglitter', 'v__miumiu', 'u.baeck.ha', 'u_vely_._', 'test_dr1v3', 'tarzzan_wony', 'ssongkeem_', 'ss__09.06', 'so2pearl', 'shu_a_lo', 'seo_ngmin', 'royo0n', 'rimi.1011', 'ptrungan', 'prudencedestailleur', 'pchanikk', 'painxflower', 'opallios_jin_', 'nusxxeuy', 'npin_9', 'nana_j95', 'mspurplehippo', 'mome_official__', 'mmlll.vll.llvl', 'minhyeok471', 'mimi_33t', 'miii.___.nii', 'maryleaves', 'mallanghari_', 'm_i_2__', 'lyj0206', 'llllonaaxoxx', 'littlemischievousdoll', 'literally_uno', 'linnku', 'lewis.chia', 'lbyvet', 'kwon_kkum_kk', 'kisha__kim', 'kimyedo', 'kc_6668', 'junhee._.421', 'juliayeji', 'jooeun.2', 'jo.yeon.gyeong', 'jinsmotivation', 'jinhun_760', 'jh___hyng', 'jeedonjira', 'its.alexgl', 'imo_okk', 'igeonyong61', 'hyeonparks', 'hyeo_ni_187_', 'hyeo_____n', 'hyejin_____n', 'hye_ya_s2', 'hui_s2_ye', 'httpslxz', 'hongxxerin', 'hjsngm', 'hmmm_pic', 'hi_nya117', 'hawxjin', 'halfmoonest', 'gnuoygnodl', 'godblessxy', 'ggup_soo', 'gam_og', 'faithlailin', 'eunzinius', 'ekater.meee_', 'e_b.__0507', 'donggyu_king', 'dianacoreofficial', 'db_rl_gus', 'darlig_spk', 'clearmarin', 'ci_cci__', 'chae.__h', 'bymoodstudio', 'bottlesue_', 'be._.en_i', 'b_xmimjux', 'arcadi_a_', 'aoyamayujp', 'alyona.weys', 'alicerosegrd', '_ssseoyun__', '_s.e.0', '_artack', '_____kady', '4_lo_vely', '2m.gg', '2k_eklee', '2.azy', '2._.29kg', '169_sin', 'zzilookbook', 'yxoxsxxk', 'yung_baexx', 'yun_ju2321', 'yourgirlaria__', 'youna_chang._.afan_girl', 'yewelsol', 'yeonhee_off', 'xxsknd_', 'xinook_', 'xmmmmm1x', 'xaeux3921', 'xae__xin', 'winf_0', 'wbeltm_20', 'vvvv_01v', 'un__.0915', 'tong_pix', 'thurs_dayclub', 'takeafancy', 'tae_in_20', 'tae_su99', 'tak_bomin', 'sy___e2', 'sumikonoie', 'sopi_comfy', 'soo.___.h', 'snap_tiamo', 'siri._.kong', 'shushua_aa', 'shin0heo', 'sh_y.oon', 'sg__3_1', 'sejin_kim__', 'sarli_baba', 'sambalakhchyan', 's_jinn01', 's0.__.m', 'rudy_yuseong', 'river_kite.arc', 'ro_ser_n', 'rlawogus_4981', 'plzcallmevic_', 'pokemwan_hand', 'peach_._.oh', 'passioncreare', 'ohpickk', 'o.jeongyoon', 'nzksjzx', 'o._.pio', 'nrim.kr', 'nkw__no', 'niizipiink', 'moonstrucxxove.pic', 'mirme_bundo', 'minkimxhappy', 'merida.kr', 'me.in.jeong_', 'ma.di.99', 'luvur_xu', 'lee_jongho_99', 'le_model_kat', 'lamnhung_', 'l__eonidas']
    black_list = completed_target_influencer.find_completed_influencer(project_name=project)
    target_username_list = list(set(target_username_list) - set(black_list))
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