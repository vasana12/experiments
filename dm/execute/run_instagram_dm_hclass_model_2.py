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
    project = "hclass_model_2"
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
    # black_list = completed_target_influencer.find_completed_influencer(project_name=project)
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
    target_username_list = ['_il.sang', '__1umin0o0us__', '4.23.db', '4_9ie', '2oojnuyh', '1jinoh', '187._.lkm', '186_02', '0__aria_', '07closet_', 'nyhflax', 'xxmxunnn', 'zanzanss', 'zi_chuuxa', 'yuniejk', 'ysw_gaeun', 'yoshizawamiyu_104', 'yoon.__.west', 'ye_won_reo', 'y__brr', 'woo__easy', 'woon___2', 'wonb1n', 'wonzin.a', 'wioutme', 'un__________jae', 'twoshot.photo', 'tpgnsld', 'tobehappyok', 'tabemacle', 'sxu_xinnn', 'sunny._.z', 'sunjuseongg', 'su._.v2', 'ssoyear', 'sso_tury', 'soyeony_04', 'sopyunakim', 'somiiiiiii1', 'smozzzi', 'slow_flow__', 'sfan_0913', 'senzpic', 'sehee_bia', 'se0._.nn', 'salon_de_ian_', 'sang_a_lo02', 's_dongle_e', 's.min.p', 'ryu._.xin', 'ryuccl', 'ru_u_1215', 'qlsslq', 'pkiklklk', 'peaceoffclub.official', 'parkjunwoo97', 'ouni_9', 'otorxdl', 'onesttone', 'nowtimepark', 'new.h.i___8', 'nadia_yj', 'na_ashine', 'mxnzxoo', 'mustbejason25', 'model_david718', 'mirumaru___', 'mingtori_286', 'min____97', 'mim9__', 'milksuha', 'mi_n_w0o', 'melt_wither', 'luv.me.forever_', 'loystue_02', 'limjvx_', 'lillllycode', 'light_me__up___', 'lilian__yw', 'leehanna______', 'leeds_mustang', 'l_s_k_05', 'ky_u._', 'kwan_g6', 'kiwicigar', 'kinnkahyun', 'kimgreennnn', 'kim.joker', 'kim.__.yebin', 'kate.lee.lee', 'katamoto_yuzuha', 'k_came_ra', 'jusolha', 'jud.y_01', 'jo_ye_on__', 'jom_bb', 'jme.kwn', 'jjaeb_221', 'jisuuu__ym', 'jinhyeo_n', 'jingunkim', 'jihoooo0619', 'jih__nij', 'jeongan____', 'jane.nini.jane', 'j_hyun3802', 'j.w.__.lee', 'iwasntyourocean', 'in0429', 'imtokoh', 'iamchaaeung', 'hyunzuny', 'hyeong_i_da', 'hxxsolmin', 'hnh9257', 'holo.snap', 'hj_hj.o', 'hey.muggsy', 'hansun_official', 'haha44991', 'haley.amaliaa', 'h.o.o.n_', 'gyu__ri4', 'gwangju0o0', 'gvel_y', 'gster_p', 'gukseong_k', 'giaxxberry', 'from_yeju', 'eundong0121', 'emo_grapher', 'emi_sakurai1231', 'ella_tt.x', 'eh.film_', 'eastern.warrior', 'doo0o0ssun', 'december_i205', 'ddnn_.0o', 'da_woii', 'daichinagata_1999', 'd_hyun.23', 'chxxnu_', 'choueo_', 'chebcheb_', 'c_jungwoooo', 'bynanclee', 'c.inceol', 'c__g.s', 'bokili__', 'bella_colorstyles', 'beliefjuu', 'bambi._.ju', 'ayoung__s2__fanpage', 'artificial__moon', 'aris__tata', 'argento_seok', 'amane.yugi_', 'aitanameis', '_yeon_photo', '_wins0me', '_limel__art_', '_junbo', '_hyeonjuvaugh', '__sjoey', '___eee.j', '9___a._eun', '98x05', '7.04._', '37.25_', '3thwater', '2ccis', '2jhee_', '22.8h_', '2._.tae_z', '1ikeavirgin', '18oioi18', '04_o1', '0_5.6mm', '__recordtoday__', 'limjvx_', 'yurixjanx', 'yujin.kiim', 'yua_dokzon', 'yeoda_foto', 'y_rich01', 'xrainxism', 'woo_wee006', 'wong._.23', 'wndyddn', 'wo___oing', 'voiceactor_sw', 'vvvaleria___xx', 'u.hafilm', 'txaoerk', 'this_is_mingky', 'terryxkim', 'ssung_a', 'ssm_m22', 'soyeon___03', 'soorincess', 'sooohui', 'so_ozing', 'sky_o_oii', 'sing_a_song_0', 'sincerity__u', 'signature.minu', 'seraphic__ju_01', 'sehee_o_o', 'samiraisshe', 's_hyun__o3', 's2_____hari', 's___y_0118', 'ryoma__h', 'ryuuuun_', 'roh_judy', 'push_number', 'pur_viox_xi', 'poshshopposh', 'pang._.hwi', 'p_kabooo', 'ovlboy', 'oosolleb_91', 'oneoffbody', 'oliver12107', 'oblique.b', 'nuricolors', 'njltheawesome', 'nnnooya_', 'myu49_insta', 'minmin__0_', 'melon_water527', 'mi_980831', 'mdoubleon__', 'maybe.en', 'luculent_anna', 'lizzyeye', 'little__jo_', 'liebe.jh_', 'lengray_', 'leeminwoo.95', 'kwonnzzi', 'kyb_2000s_', 'kgh_8.26', 'kevin_artm', 'juuuuuye', 'juneyoo_dailystory', 'jun_.5.11', 'joon.181', 'jm_lee2oo1', 'jjjjjy0404', 'jeonchangha_cute', 'jdchoi0522', 'j_h.jin99', 'j__miim', 'izmailyan_polina_', 'j.c_h00', 'iris_film__', 'isdeep_', 'im.kmwwkd', 'ikbk___', 'idayeong890', 'hyunjin__18', 'hyo_hyuck', 'hy_e0n2', 'hjchulllll', 'heoguacamole', 'heeisadreamer', 'hanyul.e', 'ha_jin0.0', 'h.notye', 'grow_teeth', 'geo_n_ho', 'em1l2_s', 'ehyunfilm', 'dooduring_', 'dokgo__hwang', 'deogun.snap', 'ddambbang._.51', 'damian_life88', 'd0nghaaa', 'ck_xlilx_', 'chann.est', 'cha_._cha', 'born.skinny_', 'brianberry_official', 'boo_bo__ra03', 'bodyprofile_expert', 'bini_beauty__', 'birthday21girl', 'bibinuee', 'badtthang', 'alstjd_x.x', 'ahyoung_p126', 'ad_picture7', '_leearim', '_ldaeyeon', '_juuddi_03', '_lovely_hari_', '__yoon_suh__', '__kimdaeyeon', '___hx_xs', '___.doreya', '9xleee', '8._.0k', '30.8m_', '2c_hee', '24.yu_', '167slc', '182.6_01', '11_natali_', '07_o_.__._o_30', 'bo._.bless', 'gowoooooon_', 'jo_a.0', 'yoonwnsyeopz', 'mar.__ww', 'zzuru__', 'zoon__pic', 'zerotomin', 'yoon_00_hb', 'yeo.n_ks', 'yangnam_0', 'y_dh18', 'y_ddo.ri', 'woooliver', 'weti_lab', 'vivalaviva_o1', 'usuneda3', 'ui_ui_jin', 'tom_my_1202', 'tkfkdtm121212', 'tjrwls_02', 'timidboy_', 'taeim_03', 'sun_n222', 'sung__yoon_', 'studiogoat_official', 'storm.nf', 'stacyhwang_331', 'ssgyun', 'seruru_il', 'seoon_aa', 'seo2hi', 'se_giii', 'rui_77_', 'py.0.4', 'priiimarie_', 'ppangi_1212', 'prsoi5_xue', 'opizd', 'ok_zuno', 'nueawh', 'nouonon', 'ne.ta.li', 'naomi_o_s2', 'namkyung.min', 'nallyjelly', 'muuuule_j', 'mrmr_hwan', 'monkarma_', 'modeljade', 'modelingleia', 'minday_o_o_', 'miamor_hj', 'mignon___kim', 'mi_ni_rami', 'melodie_from_france', 'maryrin._', 'majunhee', 'm8n_.32', 'm_jii__', 'lxnguxr_', 'lua_comi', 'lobster85mm', 'lara_origin', 'l__hun', 'kuuk_pic', 'kki_muna_', 'kixs_uck', 'kill_j00ng', 'juuuhana', 'jsyov', 'jjang._.seo', 'jjin_187', 'jjhyo24', 'jisooee', 'jini_cute_04', 'jin_o6.3o_a', 'ji.mee', 'jae_seong_00', 'j_n_h_01', 'iridiscente_mylife', 'is.that.true.yoh', 'io_oing', 'imgonnabewhatiwant_', 'iluvbeef_', 'iananwarv', 'igluesxx', 'hyunseok_jung0125', 'hyo___nee', 'hyeziiiiin_', 'huk_0619', 'h_ye_jun_g', 'h_poey23', 'h__jun.s21', 'h0n9_se0k___03', 'h_in_in', 'h_eeminiiii', 'gurgood13', 'gwak_dsd', 'gimeunnam1', 'fujitaayumi_ph', 'euns_73', 'es_0116', 'dwkk___', 'doyaa_jian', 'dnrwo0510', 'co.ccoi', 'chong_a_design', 'chltjrdud0918', 'chae.aah', 'chaaeng.00', 'been_0212', 'bad._.ay', 'b_abybae', 'b.nani_710.s2', 'arthur.hauser', 'aribari777', 'albertimstein.ko', 'ahjh__v', '_x1iara', '_onlyrosebaby__', '_kimjinyoung_', '_min_j_s', '_gnuoynim', '__jzero', '____yoonjiseop', '__5silver__', '_0_4_0_3.__', '9woo.___.9', '9._.narong', '246437_x', '22.1_jj', '20100_6', '170k.c', '181.9__mg', '0805studio', 'jo0ong_9', '_nataliomeli_', 'du_ggie', 'jae_hyun_69', 'zzzxhyun_makeup', 'zero.o_m__hyeokk', 'zhex2o_o', 'yu_.__._uy', 'youth_fw_film', 'yo0oji', 'xx97_18xx', 'x_anouk_xb', 'x__moment', 'whole.paper', 'vriuni', 'w_of.flower', 'vit_vivi_', 'unis_xx', 'un_burden', 'twoyeji', 'u.uzzzz', 'truffles_catstory', 'tomi_model', 'togeti.c', 'tintone_taeyoung', 'tgt_thumb', 'talentreetdotcom', 'taeri_cherry', 'sweetyasu_cosplay', 'sunsuung', 'sveta_lightland', 'sunriming', 'sum_in__', 'stylist_beneficial', 'strawberry_0520', 'sss.uy', 'st2am_up', 'springines', 'soyuuuni', 'snortingkuromi', 'sinb.km', 'see.nyong', 'say__ho___', 's__waltz', 'rrvngvvv', 'riskygirl_ps', 'rawimage_studio', 'real.diel', 'qna1s__', 'qkrgyq', 'prx.nstia', 'prome_theus_1023', 'polinlovv', 'pinky._.juju', 'panda_9805', 'outline25images', 'onlee.official', 'onthesamepagee', 'on.zz_3', 'onebravely', 'olol_ya', 'olgasofrik', 'ogawa_mirai_', 'oesmim', 'o3o9ram', 'nusgnuoymik', 'noxxl_15', 'nireamk', 'nexticonworldwide', 'naturalkahlomoon', 'nata_stepko', 'natsumi_ibuki', 'nani_0607', 'mxxnseong', 'minitaum', 'minju.__.668', 'minjju_21', 'mimimimimimi.__', 'miduki___f1012', 'miaeiw', 'mellifluousyj', 'melitaos', 'lux_ooon', 'lucy.picos', 'luna_sunn2', 'lridescent_s', 'ljh__0720', 'limjongseong_', 'lev2osa', 'kristina.poradun', 'klerkerero', 'kkunn_a', 'kim_hyyy', 'kimbeom_02', 'kidsmonde_', 'ka_gentlesilver_e', 'k_soo_x', 'jxnrain', 'jueeery', 'juhyi7662', 'joonhee_.1211']
    logger.info(f"총 {len(target_username_list)} 명에게 dm 발송 시작 target_username_list:{target_username_list}")
    while True:
        max_messages_per_day = 10
        account_setting_info = select_user(username=None, max_messages_per_day=max_messages_per_day)
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