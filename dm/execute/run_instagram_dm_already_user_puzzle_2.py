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
    project = "puzzle"
    start_date = "2022-05-16"
    project_info = {"project_name":project, "start_date": start_date}

    """ dm/source/message """
    text = get_dm_source.get_source_message(filename="puzzle_pet.txt")
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
    target_username_list = ['hongz_zi', 'eun_juya', 'drawingbutler_luna', 'dduk_ddak_oppa', 'congzzi_', 'cocobonohotel', 'cats._.cats._.cats._.u', 'b2ni2', '_firstcat', '__twinkle_.__', '__median', 'sunny_cattoon', 'rirang_onair', 'yubuzzang', 'winter___cat', 'vita_mujin', 'two_cut', 'sogeumtoon', 'siru.vely', 'seal059', 'sangw3', 'rara1733', 'qkrrwlrma', 'pillnaeng', 'momoh_mom', 'mojave_____', 'mandu__hobbang', 'luv_nan2', 'lesososo', 'leooo_paaard', 'jworld_1218', 'hanaduna', 'hailoo_cat', 'gozitive', 'goormmmm', 'fuchu.blackcat', 'dooboo0101', 'dolmaengyi_', 'dididodo_', 'conte_trentecinq', 'amyssunlove', '_son50_', 'leejusang_vallatto', '0nullnu0', 'sanhojeju', '_son50_', 'zzal_square', 'ezsafe_official', 'zminparkk', 'xoxo_neko_', 'vetainer', 'swim_0113', 'sonshine1010', 'sol_maru', 'official_teentop', 'muro__cat', 'lee_sion___', 'junyoung__c', 'halla_cat', 'gguya.lang', 'fitness_g_100', 'east.soo', 'du___cong', 'daldalcat', 'chiinose', 'cappycream', 'cat_anbbangpo', 'bidan.cat', 'bbongs_town', 'bangbang._.2', 'dgnn1112', 'zzooooopp', '924js', 'lx_xlllll', 'unicharmpet_kr', 'youn_ssso', 'x__i_na', 'superma_pet', 'sunny_n_cats', 'ruruyeori', 'rhamemu037', 'plz_no_rain', 'pennac2016', 'mori._.cat', 'motungi_cat', 'llkong.e_m.sll', 'kkam_show', 'jipsadiary', 'jazznpaul', 'hoochu_the_cat', 'happy_applec', 'guno9716', 'godsingo', 'dung2nara', 'colorofmori', 'bebe8cats', 'angun09', '_gamzadori_', '_bono_5', '_all.uring_', '____hyunkyung', '718cat', 'sssyj0420', 'leelee2756', 'yupsal', 'bongbongyang_', 'monthlydesign', 'peach2gold', 'yubeen___', 'yom.namoo', 'wearecutecute', 'uwon9305', 'star__dolls3', 'skysm1004', 'simjang', 'si_nunu', 'seonyudo.cat', 'saturday_jaemy', 'retrovintagejangbongseal', 'purplay', 'nyang_deng', 'norae_gang', 'now_afterbooks', 'neko.co.kr', 'mozzi_mogwa', 'mogaenyang', 'lawoori', 'kim_ssunny', 'kim._.kongprincess', 'jinams2w_1112', 'jin_oildrawing', 'jigucat', 'gold_0123', 'ggyu_l', 'flower_cat_road', 'euro_curry', 'eunyoungseoillustration', 'eu___ri', 'eunha0921official', 'cream._.gaeul', 'cocozaza_', 'citrus_sister', 'chasunjung22', 'cheezee', 'catrocks2018', 'banzzag__ee', 'banbbom', 'chaedaldal', 'jijin_humor', 'sunny___moment', 'iliallha', 'gatoperro.official', 'zzinnbbang_', 'yukidubu', 'yuhengsa_official', 'yomi_moonya', 'yemyo_man', 'with__0330', 'star__dolls2', 'soulmaker_official', 'song_chee_ke', 'skylove7192', 'signatureby_korea', 'seonu.___.lee', 'seoeune', 'sennybabby.171', 's.ham93', 'ruby_jade_mom', 'nekkomori', 'nanazzang0202', 'nabiya.2007', 'mugen_s', 'murmursroom', 'mumohan_home', 'minirmrm', 'm.gatoblanco.co.kr', 'lumi_luvely', 'lennnnnnnyyyyy', 'lala_c.a.t', 'koyoch', 'kim_yu315', 'juliejean6520', 'julielee_3131', 'jevely4860', 'iameolu', 'i_amcookie', 'happyhaejin', 'fataltalker', 'easyworld_2', 'david.youn', 'dalunacats', 'cka720', 'aria_devonrex', 'anncherrry', 'amy_kikida', 'ahl0910', '_mieumi', '_berry._.y', '2_duri__', 'kaka.only', 'mbcnews_official', 'rusime36', 'kim_ozzi', 'girls_likey', '__mimi_____', 'nana.gramm', '_mooki__', 'seoeune', 'starcat7942', 'zer0._.you', 'yun_lee_99', 'yeonnam_cat_popart', 'vanessa.c.sm', 'travelbin', 'tokkiya_nolja', 'tomotorileo_iloveu', 'themakers_cuma', 'sylvanian_korea', 'susan_kimm', 'streetcat_zoro', 'siyeon0622', 'seeyou_0421', 'savetheangel1004', 's2_jjuya', 'ran8870', 'ray_at_home', 'qyoungwoo', 'pikachu__raichu', 'naturesprotection', 'myo_hagae', 'mungugirl', 'monami_neko', 'mmmkitttyy', 'miyu.meyou', 'm_mi.so', 'ma.neul_', 'luhah1905', 'luna_is_l0ve', 'kyung_min_b', 'kookie_nyang', 'itsdesign_official_', 'imaggeee', 'im_ong_sim', 'im._.mi_ana', 'i_ryat', 'i._.morae', 'hyeoklee4242', 'hetbani', 'h.ju_he', 'ggomjijubu', 'gdppcat', 'dontbuyadopt', 'dodam_nyang', 'dobrotherandsister', 'dear.mycats', 'dango.zip', 'cho.co_ming', 'catpre_official', 'catfriends1004', 'cat_mayo_nez', 'bomgom.cat', 'blackrice_love', 'bebeneco', '_your_emily', '__simbalife', '__rimyy', '___moong_', '2bpet', 'girls_comecome', 'humor._.cat', 'yulee2329', 'allurekorea', '_____twinkle_j', 'so_nuu_', 'gooroomy_cloudy', 'myeongsu3508', '2yoonplus', 'blessed_life_230', '________abin_', 'xoxo_minju', 'sun8304young', 'sportage3375', '_bookcat', 'creamsugaa', 'kopc_adopt', 'kelly__holy', 'ari_russianblue', 'boggybok', 'plainn__', 'hi____gg', 'nu.heejin7', 'unni_mitji', 'mangobana__', 'tory_ne', 'homecooker87', 'remi_cat_0910', 'greem.is.life', 'muse.gee', 'khal22si', 'lifeissocool', 'aurora_kim00', 'muumeowmeow', 'haruwell_official', 'animal_kara', 'endypoly__ragdoll', 'lemon.berry.smoothie', 'cremamorbida', 'ohella.official', 'ing.guddn', 'hifive0301', 'd___b___l___m', 'enterdog', '59oh9', 'hyde_wolf', 'baaaaauri', 'eun_jin_93', 'meeeebum', 'chohyyeon', 'jrt_mark', 'realmusictap', 'im_min.vely', '_ppukku_', 'oopsie_daisyyyy', 'dingjya', 'yanni__90', 'jiisom', 'da.raae', 'kingchestnutbread', 'jjjangda', 'i_am_wooyoo', 'hera_grida', 'chihuahua.kobayashi', '__.mozzi', 'seonozzi', 'akdong2world', '26_yelim', 'honey_honeyfun', 'jground_official', 'dreaming.house', 'archi.natural', 'corgi_hun', 'lovehyunyoung', 'yurikhyuri', 'small.b_design', 'praise__healing', 'a.p.ricot', '2ppi', 'k_youtube_', 'oh.myluv', 'cing001', 'humor_lamo', 'helth_self_manager', 'whitepom_lu', 'paramount.kr', 'joohee1122', '_geumi__', 'team_bb_sangho_lee', 'sarang_luna_louis_love', 'mindyj1023', 'lalala_s2_', 'juw.han', 'ippngirl8', 'iibbeum', 'honeymon88', 'borinnike', 'awesome__living', '_tinaxoxo', '__kim.satto.bob', '___humor_king__', 'thisabled_inc', 'youth_jm', 'ordinary__weekend', 'lotteent.movie', 'kwonjian_81', 'jadore407', 'doopooding', 'dangdangfestival', 'cheolsoo_jindo', 'aromapooding', 'amylovespet_kr', 'bambi__jeju', 'kimkay0n', 'youbuchobob', 'sun0045', 'sonopetclubs_resorts', 'smile._.atom', 'mirada_day', 'like03062002', 'jjina__jjina', 'hotteok_s2', 'healing._.comedy', 'esther_smilepet', '05.27dm', '_vzl.zl', 'song4u', 'oliver_linzy', 'ha.kuna_ma.tata', 'jejutourpass_official', 'semicolon.books', 'discipline_4u', '__.eunji__', 'kind.dress', 'iampet25', 'ad_lab_official', 'stylepower__', 'khhh_i', 'humor_cok', 's_suzung_', 'kimjung9797', 'jungpr06', 'vx0f1wo', 'br75m3w', 'zoabc2020c', 'sobin4966', 'osungwoo68', 'kinuna201', 'dry2020ww', 'jinwoo8080', 's2020zz4', 'musubu.kr', 'hohohom11', 'o_o___0502', 'misspark_86', 'the_rosa1004', 'eunmishin0865', 'eunasing', 'luving_ji', 'shinjy_gram', 'popocopocos', 'nyongjjing_', 'nareu9', 'b_gureum', 'k_commu_archive', 'leewoobin89', 'shiba_mizz', 'olliexwestie', 'ozzozzoz', 'tantanxxi', 'ssuri0128', 'simapapa7', 'ji_hye_s_', 'donkey0213', 'coco_sandrine', 'issue_archive', 'meong.beach', 'madamharu_tattoo', 'k__8722', 'joeyandbailey', '3730sss', 'tedlove_ssow', 'supdog.hyunmi', 'lotte250dogs', 'hyezzi_han', 'dawon0908', 'chanho.park.3936', 'keumbi.neungkeum', 'sunzzing', 'lovelyeom86', 'jjaru815', 'evergreen_sol_', 'blingbling8582', 'only_jinly', 'tiger2013c', 'rachel_heee', 'petlawyer', 'parkhayi', 'hyein0622', 'coton_wooyoo', 'seoha_mom___', 'vintageamy0817', 'in__wang_san', 'humor_quack', 'osanholic', 'ding316317', '920_1024', 'sedenaz.official', 'hora_the_kitty', 'morement_official', 'kawa.hq', 'golden_british_l0ve', 'tom_and_pep', 'silvergun_96', 'soho_hello', 'jodiaarielle', 'siamesesclub', 'ordinaryflower_u', 'mumcatorg']
    black_list = completed_target_influencer.find_completed_influencer(project_name=project)
    target_username_list = list(set(target_username_list) - set(black_list))
    logger.info(f"총 {len(target_username_list)} 명에게 dm 발송 시작 target_username_list:{target_username_list}")
    while True:
        max_messages_per_day = 50
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

