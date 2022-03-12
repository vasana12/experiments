from db import m_instagram
from instamanager import Bot
import logging

FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
if logger.hasHandlers():
    # Logger is already configured, remove all handlers
    logger.handlers = []
logger.setLevel(logging.INFO)


text = """
    안녕하세요?! 🥰
    소비자 체험단을 만드는
    🧩퍼즐 코퍼레이션 입니다.

    제품 체험단 정보가 있어
    다음과 같이 참여 안내 드립니다.

    퍼즐코퍼레이션 <틱톡> 체험단 모집

    ● 브랜드 : 선정 후 안내
    ● 체험단 : 틱톡 체험단
    ● 원고료 : 5만원

    <👇체험단 신청👇>
    https://forms.gle/XkuLbcXktDrRmccH9
    -
    -
    궁금한 내용이나 문의는
    📧이메일 : ugc_team@puzl.co.kr
    💬카카오톡 : puzl_ugc

    감사합니다 :D
    """
db_conn = m_instagram.InstaDB().conn
INSTA_ACCOUNT_OBJ = m_instagram.InstaAccount(channel_name="instagram")
INSTA_ACCOUNT_OBJ.client_name = "admin_test"



# # username = 'sp22064497'
# # password = 'amdc2580!'
# # proxy = f"http://user-{username}-sessionduration-10:{password}@gate.smartproxy.com:10000"


def select_user(username):
    account_setting_info = INSTA_ACCOUNT_OBJ.select_cookie_user_v1(username=username)
    return account_setting_info

def main():
    host = "residential.ipb.cloud"
    port = "7777"
    mobile_proxy_username = "customer-lsgr20040901-asn-22394-sessid-zmmT-sesstime-1"
    mobile_proxy_password = "UG2xaDXxC"
    proxy = f"http://{mobile_proxy_username}:{mobile_proxy_password}@{host}:{port}"

    # username, password = 'sp22064497', 'amdc2580!'
    # proxy = f"http://user-{username}-sessionduration-1:{password}@us.smartproxy.com:10000"
    # proxy = None
    # target_username_1 = ['happy____sunsun', 'elle.jung.violet', '99uks_official', '2daleeda', '21____mini', 'yujin_2', 'sayonara_dy', 'portrait_hyubi', 'hanga102', 'from_eunji_', 'enerjiny31', '_im_soo_', '8ugust_j', 'yye84', 'ssuna_s', 'o_esi_fit', 'maeum.story', 'lovee_ha', 'leerisa24', 'jini_kkyu', 'hprt4p8p', 'eun__ddo__', 'deepny_official', 'da_yeon_flower', 'ajinlee_', '44.abel', 'travel_riha', 'triviani__', 'th_m_oong', 'tako_warigari', 'sua_jio_love', 'ssszin', 'ra.y__n', 'nsugh19', 'luv_jayna', 'lovely0811', 'juhee3912', 'ji0gram', 'guswnguddn', 'fitvely_lee', 'do__do_mom', 'dddorlll', 'chan_hy2', 'abk0430', '_go.ing_', '8652love', 'yeowon0112_', 'teung.ha', 'sung_in_kor', 'r_o_s_e_hyeya', 'lin_du__', 'leesle', 'komoreb_hanab', 'ivory.73', 'ilovemay___', 'gidwjd1471', 'fit_somin', 'daegu__ya', 'cc_oi_1', 'bling_sso_', '_still.your', '_stella_0222', '_luvly_lily_', '1004_binvelyyy', 'whatever_yul_do', 'ssonggram', 'sina_virus', 'sanjunghogirl_', 'rosepiece_', 'ra__hui_', 'pskypearl', 'p_sj_92', 'neul_pureum', 'miss.jobin', 'mi_ririi', 'luv_momo_c', 'jin2_0v0', 'jin.young.kim', 'hyunjin810510', 'hey_mimii', 'h_adorably', 'do_your_best247', 'chu.roll', '_ji_s2', 'yelimetic_', 'w___eunhee', 'le_ash_beauty', 'kwon_star_', 'keh850730', 'jae_hee__91', 'han_jian_jia', 'daily._won_', 'applestar6354', 'hyenze', 'flexmatch.kr', 'jjii_0102', 'gaily.__', 'kkyunis_', 'lemon_madeleine_7', 'kkyunis_', 'cmycmy4457', 'todor____m', '_kang_0_o', 'baebbo_v', 'dooboo_bichonfrise', 'd_a._.hyun', '8x10__', 'westhyuneast', 'ryn.se', 'mono_daily', 'min_0115', 'manze.co.kr', 'jinryangkr', 'ji_seonhee', '45__47yy', '0315__js', 'yeon.dy', 'y_sigi', 'technist', 'roh_mi_jung', 'jazzy_in_korea', 'art.oceann_95', 'alsa_on2', '95_hsj_06', 'today_star1', 'sowedance_', 'shoemarker_basic', 'sbj9891', 'park_brother', 'maybe.jj', 'ktw3371', 'hy__xmx', 'honey__ddanzi', 'aga___mer', '_shindongin', '2eun.k', 'yuminyu.h', 'xxingyeo', 'w.o0ng_2', 'syk8999', 'sonyezzi', 'roi.hwang_', 'kmodel_story', 'kalnal58', 'he.n_n.y', 'gih__yeon', 'downzero__', 'b__boni', 'attractive_031', 'anseojin7058', '_lee__iy', 'yeonjichoigo', 'sukuluba', 'sonya.kuzminova', 'seukhoonkim', 'parkman18', 'o1ssl', 'munji_34', 'mellitulus_', 'jangjina_', 'j01o01_', 'iwwi_lens', 'hyeonjin._.54', 'humorfeed007', 'hj__0628', 'geonho.gong', 'bs_sketch1', '_junseocloset_', '188.1cm_', '10mag', '1000nim_', 'p__h__mi', 'niong_dg', 'minagram______', 'mh.2.5', 'ljh2daa', 'johnson1__________', 'i_m_fe', 'hayoon_1985', 'geonzzzang_daily', 'eautiful_bb6', 'bom___eeeee', '168cm_0kg', '1004hyun_ah', 'zini.b', 'seoul_mangnani', 's_hj705', 'p._.jamong', 'niver2087', 'naya_kiri', 'lapinluna_x', 'hayoung_v', 'gusaguchi', 'allonmine_e', '_soonstagram_', '1_0yh0_1', 'yyesbebe', 'yspadgqwe', 'yg0402_ifbbpro', 'locking_koi', 'jangso469', 'j1nmai', 'goodgirl0073_', 'da_yonxxi', 'cho.mmm', 'c.cha____', 'bloom_35', 'audgiegee', '__yu__95', 'zminparkk', 'u_u_50', 'shoopen_official', 'shanna_luv', 'seungsse2', 'sebi_yu', 'saejeeyou', 'queen_jihyun0417', 'lovelymihee_', 'lim_mh86', 'lee_da_ggggggg', 'kz1__', 'keemdaengman_', 'ju____20', 'dull_ouuo', 'yisoly', 'yang_goon_2013', 'west_jade_ms', 'veryday_', 's2.aram', 'realsdoy_', 'mabbley', 'lovehyunyoung', 'ljd2995', 'jeongjeongine', 'jayla_yeon', 'j.w.luv', 'huhggi.q', 'hae.nah', 'cute._.vini', 'by.ha_2un', 'bora.331_kk', 'blue_cham', 'bar_bie_yuni', 'a.__.in', '_jwmom', '03.girl03', 'two_one22', 'the_name_ernie', 'taetae.k92', 'sunxone', 'soim_korea', 'ojiri12', 'mer.mj', 'maemoo_sae', 'loveannadress', 'koo_jg', 'jinvely_0501', 'eung_l', 'byyeong02', 'boonja_6.9', 'angelasua', 'a.k.a_baby_g', '161aa_xx', '007s_b', 'yun_jaegeun_86', 'velysu123', 'v_v_kim_love', 'tiamo_doha', 'tessunnie', 'tennis_joon_', 'sujin_k.dia', 'su_mimni_', 'souri.xx', 'rani__0315', 'park.sju', 'mi.yol_', 'maemmi_abuzy', 'k_duck_99', 'jungyonii', 'jjoming_kitchen', 'i.y0u_jj25', 'ddddo.s', '_mygyeol', '__.eunji__', '_00_yumin', 'ooojujuooo', 'yy__wever', 'yumyum___2', 'yuhee.lee.3', 'surfyy.roppy', 'ssun_nii', 'somi0531', 's.__.cook', 'rollmin2', 'orararababy', 'morae_o', 'mo__k_s_', 'mk89.eat', 'mimi_ibeauty', 'lov_so', 'lily_amstrong', 'jackki_me', 'irx.e_', 'dailylike_official', 'daily__yun', 'barista_kurt', '_yum.fit', '0_0bob2', 'isometric_wonjae', 'yebinnnny', 'wjdminnie', 'lodeur05', 'hj_daily_', 'jysoodain', 'blasting_deejay', 'chu.a_a', 'chnjnz', 'jjjjjjjjjmc', 'trouba_dour_life', 'dao.o2', 'yamgeepunch', 'taboutg', 'mjkang_pic', 'jini_lo_ve', 'jeong_jeong_03', 'haaaaa.v', 'diab_leeman', 'dann.medeiros', 'crewgubi', 'ccchawonnn', 'bangkey_rr.bv', 'all.aboutbling', 'yeonji_yoo', 'treinadorfelipe1', 'seda.ai', 'rara___vely', 'o_obarbie', 'neo521_', 'nana_auau', 'nagimon0517', 'lir.xa', 'leejunghyuck_', 'jjung_0527', 'hyo_stone', 'hayeon_98k', 'haily.daily_', 'dudrnfl21', 'devfash', 'coco_marant', '17.6k_', 'yschoi0821', 'young1012o', 'xanadu_jm', 'tang.whistle', 'sithle011', 'sinincess', 'rlaalsxor', 'one.s.fit', 'o_wwin', 'nkus1323', 'lseung__mini', 'london.hara', 'lilabrisa', 'leanavvab', 'eunji_2001', 'beomi._.joa', 'asparagus.k', 'anastasiaart07', 'about_yoon', '__jung__autumn__2', '2ky.98', 'woomng0401', 'tyongeee', 'superpapa_jin', 'sojoooong', 'sohee_oo', 'rjko524au2', 'nam.__.su', 'mimi.3214', 'lipgnuyk', 'li1ac1', 'jeromeyu80', 'im.kwanny', 'hyeo__neee', 'hae.__.won', 'h_dailyfit', 'h._.h1130', 'etoile_0721', 'dj_bigster', 'angyeongjab2', 'agit_jack', '8pr75t1l0', 'xnxn0xmxm1', 'whatevertheycall_me', 'u.hye.s', 'sun_bung_', 'ssssuji_0208', 'sha_naaa_', 's_jan_1004', 'rimi_kim', 'moonlight.untold', 'md._.0513', 'itssudeh', 'gg17_m', 'doubl2_s', 'bsj2580', 'bisque.gy', 'bijou_lm', '_myeonghui', '1page__', 'ishyevely', 'w_onl89', 'u.uzoo', 's_u1014', 's_bomii_0310', 'nyang___ee', 'nanicho_official', 'litsi_k', 'k.ssun_8', 'jang.yukyoung', 'haoke13pr', 'haeun.emo__', 'frogdok', 'bora.__.mi', 'baba_road', '09women_official', 'w_oo__gram', 'teddy_dal', 'sumisuwan_closet', 'seowlsl', 'og79th_', 'k_hahaa', 'ga_eun_160', 'eomjiiiii_', 'danmiiiy', 'c.l__woo', 'annyallyoung', 'aileen_012', 'ahhhyuna', '_peach__a__', '_______min.a', '_158.42kg', '_07.10__', '7__ku._._', '6na6na', '365.season', 'amy_ej_', 'u.zzam', 'sum_inq', 'snow_white__sh', 'roain.x', 'redrabbit_973', 'r.___.ay', 'prpyqcx', 'poo__ruby', 'ma._.monde_', 'love___ring', 'j_yummy.in.the.tummy', 'housejuice', 'heexoxo_', 'goo.jinseo', 'god.mario', 'boutique_j_j', 'bae__bro', '_____network', '406moon_', '2014yool', '0.banana', 'unicorn_ppul', 'seungri.98', 'rang_b.b', 'k_gh._e', 'iamsongjour', 'i_can_do_young', 'dddamchae', 'dai_n0320', 'choi_1988', 'beebee_457', 'a_.grace', '_someshop', '_bom0518', '91__xx.hyun', 'kootamin__c', 'yy_in96', 'yang_yang85.05.11', 'ssunhye_y67', 'se_bong_e', 'sdiary_92', 'pellucid__', 'mocow_daddy', 'luv__haram', 'j.s.eon.m', 'ihyejin617', 'hw_1102', 'guijung13', 'gangwon__a', 'deer._.soooo', 'cosmopolitanjuly', 'bottletaste_tv', 'angmondxx', '_yu_bin._.163', '_juuuuuuun_s', '__oliviax4', '95soye', 'sh_91.p', 'zzoo.hhh', 'you_hye_rim', 'y_y__mom', 'y_ibin', 'vin_life87', 'twobellsilver', 'suhyuk565', 'styleshare_kr', 'stagram_haeju', 'rlcksk1', 'ptgr._.y0j4', 'okhyun1218', 'nowwannee', 'nibo0o0', 'min._.juicy', 'lovechoijm_eat', 'kwangmin.cho', 'kongssoya', 'ke_____kk_____i', 'jun_su_1004', 'iwedding_official', 'illillillillllll', 'honey._.ss', 'heartycrush66', 'glory___e', 'girl_like_insta', 'ejejrgns', 'by._.ul', 'aangellamike', '_clothes_me_', '___sshini', '_____da.da', 'ys0616', 'yoniship', 'yeseul_cygnus', 'xoiox_02', 'wonny11_11', 'u_ooni', 'tpal777777', 'taem_0324', 'ssuny.0129', 'sooyoung_choi_stylist', 'someday.fit', 'solmup', 'she_tasteslikehappiness', 'sejin__in', 'rou._.jing', 'reum0928', 'odw_00', 'nyang_lim', 'muk_jeong_won', 'mirimini0531', 'louimin', 'kyungmin_bae_', 'kko_raz', 'joyujin5248', 'ja8218', 'i_na0912', 'hyunnn__o', 'hyekyoung0722', 'hiy5102', 'helena_0916', 'happyaejin', 'g.yeong__', 'flashe_narae_ing', 'dodoglass_workshop', 'almi6634', '_vvely2', '_ljs_00', '__kiboy', '428lim', 'inheekim87', 'zayson__zl', 'yutiti_08', 'soo_ah.soonsoo', 'solsol_ssi', 'snowwhite.by', 'second___night', 'ruvdsharp', 'raquel.baek', 'ranggg__313', 'pingu_love_eat', 'mc_choiga', 'mango_dang96', 'leejaeheee', 'isoyun1843', 'injustagram', 'hy0._.genie_', 'hana01071228', 'hana.wwang', 'gimsihyun7286', 'funspinning.jerry', 'eibbni12', 'bongsister_headshop', 'bbo_00', 'aaoioo', '_e1ly_', '__si.a_', 'yujuuuuun', 'weeny_insta', 'two_andthej', 'soo_lee100108', 'seoul__a1', 'seo.yona', 'ru_bin0608', 'riwon_002', 'puella_babi', 'oliveami_beauty', 'm._kloset', 'leaf_mi', 'kinghoon__v', 'junghae_woo', 'jjoo83', 'jinnam_j', 'healingeeee', 'creampoo._.sanggu', 'centheal_official', '99__nami', 'lucy_lusia1213', 'banana__ms', 'la_soo_min', 'jw_kkkkk', 'juandavidod19', 'felicity_h0j', 'blankasebestyen', '_100_88_180_', '19.95kg_', 'st__bysso', 'dais2_', 'da_happy__', '_early_spring', 'miring_23', 'yum_yum_yojung', 'nariabeklevic', 'myungmozz_i', 'model.choa1', 'kellyhasaninstagram', 'eyeobud', 'baker__louie', 'chole_xp', 'yeee114257', 'seoul__a2', 'namina0104', 'jennypick_official', 'y.__.hye0n', 'wooriseoa', 's2_sooss', 'maria.lix']
    target_username_2 = ['send_direct_items']

    while True:

        account_setting_info = select_user(username="s9kennethevans2010")

        if not account_setting_info:
            logger.info("no account available")
            break

        username = account_setting_info["username"]
        password = account_setting_info["password"]
        print(f"username:{username}/password:{password}")
        input()
        # username = "azbrrilmxobchnevul"
        # password = "g7jlI5h"

        logger.info(f"{username}:{password}")

        bot = Bot(db_conn=db_conn, max_messages_per_day=5)
        bot.login(username=username, password=password, account_setting_info=account_setting_info, proxy=proxy)
        broken_items = bot.send_messages(text, target_username_2)
        target_username_2 = broken_items
        # print(f"broken_target_users:{target_username}")
        if not broken_items:
            break
main()
