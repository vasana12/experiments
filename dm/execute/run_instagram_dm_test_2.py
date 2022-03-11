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
안녕하세요, 주식회사 미트런랩의 콘텐츠 마케팅 담당자 허은경입니다 🙏

인스타그램에 업로드 하신 게시물 중 좋은 퀄리티의 요리 콘텐츠를 보고 연락드렸습니다.

‘모두의미트’는 육류를 사용한 레시피를 공유하고 사람들과 소통하는 레시피 SNS입니다. 현재 팔로우 & 레시피 업로드 이벤트 중이며 레시피로 재테크까지 할 수 있는 SNS를 만들고자 개발중입니다.

이번 3월 한 달간 레시피를 올려주신 모든 분들에게 스타벅스 기프티콘을 증정하고 있으며, 올려주신 레시피가 이달의 레시피로 선정되면 6개월간 매월 고기를 무료로 보내드리고 있습니다.

또한, 나의 레시피가 이달의 레시피로 선정되어 상품으로 출시되면 매월 매출액의 3%를 현금으로 지급하고 있습니다.

저희가 개별적으로 연락드린분들에게 드릴 추가 혜택도 논의 중이니 많은 관심과 참여 부탁드립니다.

감사합니다 좋은 하루되세요 :)

🤳 모두의 미트 사이트
https://modoomeat.co.kr/recipe

🤳이벤트 내용 자세히 보기
https://www.instagram.com/p/Ca07p50Jzjp/
"""

db_conn = m_instagram.InstaDB().conn
INSTA_ACCOUNT_OBJ = m_instagram.InstaAccount(channel_name="instagram")
INSTA_ACCOUNT_OBJ.client_name = "admin_test"





def select_user(username):
    account_setting_info = INSTA_ACCOUNT_OBJ.select_cookie_user(username=username)
    return account_setting_info

def run():

    host = "residential.ipb.cloud"
    port = "7777"
    mobile_proxy_username = "customer-yxha19913701-asn-9158-sessid-TnHj-sesstime-30"
    mobile_proxy_password = "ywiB*20dC"

    username = 'sp22064497'
    password = 'amdc2580!'
    proxy = f"http://{username}:{password}@gate.smartproxy.com:7000"
    #
    # proxy = f"http://{mobile_proxy_username}:{mobile_proxy_password}@{host}:{port}"
    # proxy = None
    target_username = ['naipo000', 'lovetogapyjs', 'moonsungsil', 'haesoo7666', 'cio629', 'yjk535', 'madamivory', '3mamma', 'flavor', 'recipebook', 'lookmom', 'jye0624', 'museok27', 'is6867', 'nkh9475', 'yoririm', 'rony', 'yomidongyi52', 'joop1258', 'se6323321', 'bsy615', 'fop7', 'cshee32', 'chmstyle', 'choco135kr', 'ssssuck1357', 'fruit528', 'loveiskook', 'wtiger5v', 'food', 'sun2hwa', 'wy5493', 'kykkklove', 'ttutte', 'ttea_an', 'bbhomecook', 'jietable', 'ejs2122', 'wkaud1102', 'cookingclaire', 'chicmama', 'baby_bbo', 'cookcook', 'siamsun44', 'tayang1029', 'ju33423', 'sunshine_table', 'ceawoo', 'narawh', 'minimalcook', 'beluga11', 'yja305', 'sunjjin', 'hyang-yi', 'yka2872', 'pinkmay12', 'dals', 'dungyi', 'kyoungmik', 'loveme90000', 'tastylife', 'hitomi1228', 'bongja', 'llzzinll', 'purity_k', 'euneuntwin0506', 'spoonb', 'dhdmsdo79', 'dasomammy', 'agi0975', 'md0922', 'orange_black_box', 'hanle0618', '0813dcba', 'pinkcats', 'cookinglife', 'chain', 'zipbab1004', 'ujung._', 'thatstar', 'jeje9909', 'skckzo83', 'mhhan71', 'mag01', 'salee7908', 'yoritime', 'hwa202', 'kyss7700', 'sunsun1890', 'hubbyscuisine', 'forest0405', 'hobak2ne', 'romantic_mimi', 'sweetbe', 'heidirang_cooks', 'kies84']

    # target_username_2 =  ['jxxhxju', 'julia_barcons', 'eooongram', 'c__alex.s', 'sinartt_', 'saaaya0414', 'mj851030', 'min2ymin', 'massoblee___', '21_k_8.45', 'thoriqhafidz.kjh', 'ilaayyda_', 'gabrielrbmodel', 'bonimonii', '67__1004', '2.h.e.1', 'zenta__', 'yourbomi_', 'uuuu_we__o', 'pic_hyun__', 'maria_koiwai', 'hyunv2ly', 'f.eat__', 'dlebora_01', 'balamonika', '__hxx._.wltn', '68._.dt', '173.01', 'theyoona530', 'shining_h.j', 'ser0aw', 'rea1.rubi2red', 'r0_jin2', 'namaste_somi', 'kyunghwan_j', 'koyanalee', 'june6lee', 'jonggug.mun', 'jasminekim__', 'isori.93', 'hx__wx', 'h__08._.n', 'green_flower_garden', 'gigi.phares', 'anstlgk', '_xijeong', '_queenraam_', '_jiyeon_0331', '_is.al', 'buy_jeong', 'younn.haa', 'w0n_vely', 'rlaxogmlrldyal', 'rairai_97', 'one_ki_29', 'olaf_yj', 'mayonnaiiiiise', 'm99.n', 'm2njiya', 'lottealuminium', 'kwon_sum', 'jyh_a', 'jiyeonn_a', 'inschigram_', 'hyein2_', 'highest_____', 'happymech', 'gwihaera', 'giri_choice', 'dandell_e', 'c_hui___', 'blooming_beeflower', 'apple_favotie', 'anne851230', 'ambition_jo', '_hnk.baby_', '94sjh', '9.5mg', '2x_xs2', '11_12ju', 'whereyeobi', 'style____mag', 'soobeen_n', 'scout_ham.maltipom', 'ryu_lily', 'rrin_2', 'oioi_qr', 'mosama0124', 'mikireechan', 'lee___j2', 'ld.0.g', 'lb9706', 'jooah.look', 'iam_ari_00', 'ha__rom', 'gyeongjun_2', 'gy_ha_04', 'fiixii', 'choi_hs93', 'charm_jin1218', 'airlinesandme', '_sorable_', '_jinni_lee', '_b._gyutaeda._', 'theway_tasha', 'yxxhzzi', 'yoonmijinmakeup', 'yim.ssou', 'yewonderwoman', 'ye._.ji_n', 'wlrsb', 'tae._.ny', 'ssongc_', 'sol__08.3', 'sohyun._.s2', 'sen_zzang._', 'rjswls2', 'realjosun', 'real_bon_official', 'othsns', 'only_jiny', 'monicaaa__j', 'luvso_sta', 'jxxsm', 'john.l1l', 'j_hoj1n', 'h._.z_172', 'eunhasoo_', 'do_yoon_e', 'dhrdud123', 'booo_gyeong', '9bi_ni', '925silver_chrome', '22._.nes', '146.5cm', 'jjuvely_0806', 'yonge2853', 'xia__156', 'uzinkk__', 'un2z_i', 'the_matw621', 'qianqianworld', 'q6663849', 'prcpyx449', 'ooh_hye', 'lssunii', 'kwan2s', 'jxx_h5', 'ju_u960', 'jj._.heo', 'h.zunn', 'gugu_studio', 'e__s89', 'day_jun_o', 'dalkom.day', 'crush__x_x', 'choi_hh5212', 'berryzzin', 'bejoon0', 'b.g.t_4u', '_beloco_', '37____s2', '165_yang', 'yelinyyy', 'y_je_', 'y_hun87', 'xiaorang___', 'tantan_moonho', 'susuxxiii', 'ssunrish', 'sjxgift', 'phd.note', 'mrs.btissame', 'mr.yeowoo', 'mingoo9', 'maegi__', 'london.sta', 'leehy0624', 'lee_bom_huw', 'jisu_613', 'hyungsuk1', 'hmbeom', 'gweonsarang5', 'gwanyoungv', 'g_purey', 'dabagirl_kr', 'chae_seung_ha', 'attoro_', 'angel_linas2', 'a_unxa', '___1017', '92.06_', 'jjewelry__market1277', 'jj1277_', 'sjp8221', 's.228_', 'pelota.fit', 'ocean_berry_', 'nana__0.0', 'namgigon', 'me_bambbi', 'kimcacao', 'kang__ann', 'jakeeee_3_kateeee', 'hyun_jungie', 'h____nim', 'gyu_zzz', 'go.ya_', 'eun_zz___', 'dong__grii', 'dh.k1m', 'dear__smin', 'dailyfarm_official', 'bora_yeom_', 'bbb._.e_', 'aromarosee_gj', 'amy_09.28', '_yunmistar', '_youis', '_ram_0824', '__c__j__h__', '0.9x2.6', 'yung___w', 'yamchigi', 'xlxlghd', 'wussup.ty86', 'wsh_0707', 'traveler_yoondal', 'tae2tae2', 'ssoll_v', 'seo__ji1', 'rnldyal_10', 'n.e.u.l_2', 'my_todays_outfit', 'my_name_is_ssong', 'lee_ssanghyun', 'joo_da_0', 'jihyang0014', 'jhhhh._.98', 'her_0o0', 'hanna_ilj', 'h___delight', 'eun___ssng', 'dan_b513', 'chuunim', 'bunny101352', 'beom.c0m', 'bemysun0', 'addvendor', '_s2_hyun_', '_5e0k_', 'yo_yo_seung', 'yeong_crush', 'wooahan_angela', 'wo_ri_', 'wj_0502', 'vvsn_sh', 'ug._yong', 'ss__u0425', 'soxunie', 'sosweet_glory', 'seungmiseyo', 'sanghyukkwon', 'okjulee2021', 'me._.r_you', 'matisse_leather', 'm.m_jyori', 'lovely__jungyi', 'ladolce_vita_a', 'jinheeshop', 'jenny__im__s2', 'hovely_1991', 'hanensoo', 'haebiniy', 'global_manna', 'dong___sic', 'cho__ann', 'cafe_o_dodo_c', 'asemom_00', 'achamtae', 'a_ryeomii', 'a.m_2l2', '_yooni_yooni', '_100chelly_', 'vallatto_jangdia', 'yeorin.a', 'xx__yuna91', 'xjiyoung', 'wo_oriiiii', 'style__sun', 'ssong_ssong0311', 'sona_korea', 'so_hyun28', 'skinfood_official', 'seooo.o0', 'sangmi0312', 'parkminnnnng', 'ongi_cosplay', 'o31o.ceh', 'monobold_', 'minjung1211', 'midnight_blanc', 'mialove1004', 'marantdeblanc', 'luv._.daily3', 'lezo1004', 'le_song06', 'kimj899789', 'illun._xx', 'hwani_jj', 'hunilaundry', 'hung._.joon', 'hanor_0', 'ga.eun__jj', 'e_nol2', 'coffee_k.h.u', 'cha_ni_kku_0120', 'bsmsluv', '_gracy_official', '0.805_', 'tamnatamnanail', 'yummi_kong', 'yoon.1', 'yoga_chocho', 'yeppeugo', 'yeonsoorrr', 'ye_rin0207', 'x.x__seul', 'wooel_e', 'stylish._lady', 'snoww_daily', 'seung_ock', 'seo0vely', 's_b_131', 's2ung_joo', 'roseiriss', 'ringaring_es', 'raniet_94', 'namsuk80', 'mwms0728', 'monkey841008', 'mayholicc', 'maeng2015', 'lovemam486', 'lovelymimimi1114', 'lovable_rim', 'lovable0112', 'leehwan_', 'kimsoojin870906', 'jung_staas', 'jsra0813', 'j.j_lovewon', 'iam_vivistar', 'hwashin58', 'helloromance', 'haneul8982', 'goni.fit', 'gilllmin', 'fivezer_.otwo', 'eunasing', 'ddxhx.e_', 'c.minjeong_2818', 'bymin_m', 'bestjinaever', 'beautiful_ming', 'bang_outfit', 'bam___bi__', 'b_b_brr', 'avocad0_cos', 'april_____j', 'aaaamij', '__miri_0o0', '991124sun', '98hs.k', '1.agada', '0_0neul', 'sohot_jjun', 'zzia.co', 'youbyeolna_yunmi', 'yoobeen', 'u_zzuzzu', 'styleonme_official', 'sssssssssson.star', 'si_u08', 'ruenne_yh', 'positive_uji', 'no.1_815', 'mukgil_road', 'miya2coco', 'mini.m.i.n', 'maksimous_', 'lal_laaa', 'lakaikr_official', 'jungkooks____', 'jjuni_2016', 'jina_yap', 'jelita_soo', 'jaehyeon4887', 'irub.lab', 'ink_boss_art', 'im_junmin', 'hyorin2021', 'hxxnseo_.ly', 'heejin._.lim', 'gorgeous_sunnylol', 'eungmijjing33', 'edaily_friends', 'dbs.ycaa', 'aaaaajeong', '_khk2277', '_eroexx', '___yeony___yeony', '7845_mj', '173.47', '1004__dooboo', '0619uniskoal', 'yundayom', 'workout_j_min', 'sun120209', 'su._.pi', 'sench_luv', 's.h.y.j', 'oz_woo', 'oh_dya', 'mooods_motd', 'mariangplus', 'makeup_sua', 'lucky_eunhyuk', 'kim.jin.sik', 'jung_baechu', 'js_s201', 'jjjjay_4', 'its.joeykim', 'im_mintb', 'haru_881015', 'haengzassi', 'barber_ra0n', '_seominjung', '_romlll', '0ohanumano0', '0__jinni', 'wasabicocaine', 'saarakim_', 'ming.99__', 'mie._.ko', 'le.af0_', 'kyuuu905', 'kittens_cycle', 'kimlayan', 'jun2._', 'hyejida__', 'hi.davidkim', 'funnyjoyday', 'antonio.joon', '4.2nana._y', '1fairy__8', '11.6__hm_', '9_kang_7', 'junojune', 'inheekim87', 'haaannah26', 'gayeonxa', 'achievementt_', '27__gram_', 'welcometothepanoptico', 'sungin_ji1424', 'sakuracm_', 'priority_entrepreneur', 'jihan.weeeklys', 'dooooooongcheolllllll', 'chorong_commer', 'yujunlee', 'yq05511', 'oru.house', 'oesy_', 'ennnnnnnnnnn_', 'chae_ah_sta', 'belugabelungayo_', '_makeup.atelier', '_alenagonzalez', 'camiu_lady', 'sh_91.p', 'taeyoseph_el', 's2eun_e', 'o_oi.deil', 'j_j_o__27', 'byeol_ve_ly', '_kkangminchaechae', '0ryy0', 'zzoomakeup', 'ys_ee2', 'swshop_wholesale', 'soll2ya', 'seungju.0825', 'qi_lan_sha', 'psu._loveya', 'neutralmood_mj', 'lovececeliamoon', 'hyexll', 'gg__clark', 'dailyjou_official', 'balibiki', '_call_me_marie_', '__z___top__', '78_fox_78', 'ha_ruto99', 'tirano_yan', 'sse_hyuk', 'sofiachoi', 'pimpadja', 'mnsso0_', 'minkyungie', 'g_yeojin_05', 'freeboo_kr', 'eung_kun', 'coyababe', '_iamsuicidsworld_', '___1.28', '185.9cc', 'zzzs2z', 'yumtagram', 'sh_01_06', 'sana__sana37', 'samantha_mlr', 's___0h', 'onesto2023', 'oh_mila_', 'mariko_yata_', 'lswjayou', 'kyr_service', 'kurte_lism', 'juhee__03', 'jimin_0670', 'ji.yeon_1', 'im_sovely', 'fairyesther', 'ddong_hunne', 'dassuniee_', 'alba_actress', 'fight_gugu', 'ye._.velyluv', 'y_seooo_', 'y.l___1016', 'taehee_06', 'sunnn__y', 'soricuti', 'sandy_joung023', 'sakapon_2000', 'rxxixn', 'rheesujin_', 'r._.r_716', 'ohlaurenxx', 'lbd_0411', 'ko_kyung_04', 'k.th125', 'jonyeji__', 'jj_mini96', 'jessie_k_beauty', 'j___hwan', 'itsjinakim', 'injun1992.39', 'hoon_pro', 'harooaebi', 'en.l.j', 'ekvktm', 'dhitapedhe', 'codibook', 'cobicobi1129', '_chaifla', '__niiioo', '___hyooo.jin', 'x___ri_no', 'tokki.im', 'sy_ticho', 'suelle_official', 's__h__0808', 'ryusanggu_seoul', 'ragstoriches9001', 'oyse_h', 'o_ovvly', 'ninez_official', 'new.wave0304', 'nastya.jung', 'movemotion_official', 'minji._luv', 'kbr1208', 'julieyours_', 'jsgoodgirl', 'jeongyewoon', 'jellying_hee', 'jaden_jun', 'jace_cream', 'j.minx', 'in.0.a', 'hyony05_28', 'hy_0397', 'hunje_', 'heyju_korea', 'halo__hyuni', 'gxinxoo', 'grit_feynman', 'goonho_33', 'glofoson', 'e__jiyeons', 'ddong_6666', 'daronghada', 'chom_2', 'chansu_6262', 'chae._.ah_g', 'chaam___i', 'bk_jiho', 'bitter__sweet__', 'bibidi_danbidiboo', 'beii_a', 'andy_tattooist', 'amane_bsgirls_356', 'a_mi_da', '_sdholiday', '_gulbies', '__gahyeon__', '_010826', '98_suhyun62', '16.8sol', '_____luvbbora.s2____', 'zi_u_rr', 'yun_more_', 'yujin_made', 'youvely._.3', 'thegymkorea', 'sum_mny0831', 'sooz1n_w_', 'shinrai_', 's_kpiii', 'rui_s_closet', 'room_0118', 'rina_katsui_official', 'raffine_rin', 'pyj40_1', 'petracandy', 'owlstreet_shop', 'momo_lhj', 'moimoln', 'minn__vely_', 'minji99_k', 'mickelson_izback', 'mcgeonha', 'lyn____i', 'lsj___love', 'kuririn0704', 'knockdown_z', 'kimchanee_', 'kaiser_lk', 'judybootykim', 'ju_u_photo', 'jooya.__.baking', 'jeaaa0208', 'imonceleo', 'imchaejeong', 'i__am__kyo', 'hyozung_gemini', 'hotgirl_kk', 'highoffblair', 'ele.gggance', 'donggu_official', 'dong_wook_g', 'doll1221', 'david_w_champagne', 'dan2su', 'cornchipslove', 'bostontailor_golf', 'blackthefit', 'bjlwjd', 'amy_sunset96', 'alahunova_', 'aki_m00n', '_kiiyoming_', '_hyu__ni', '_____rani', '167.619_']
    while True:
        account_setting_info = select_user(username=None)
        if not account_setting_info:
            logger.info("no account available")
            break

        username = account_setting_info["username"]
        password = account_setting_info["password"]
        logger.info(f"select - {username}:{password}")

        bot = Bot(db_conn=db_conn, max_messages_per_day=5)
        bot.login(username=username, password=password, account_setting_info=account_setting_info, proxy=proxy)
        broken_items = bot.send_messages(text, target_username)
        target_username = broken_items
        # print(f"broken_target_users:{target_username}")
        if not broken_items:
            break
if __name__ == "__main__":
    run()


