from instagrapi import Client
cl = Client()
# cl.login("bandntest", "ahfmsek9413!")
host, port, mobile_proxy_username, mobile_proxy_password = "residential.ipb.cloud", "7777", "customer-lsgr20040901-cc-US-sessid-oBGP-sesstime-1", "UG2xaDXxC"
proxy = f"http://{mobile_proxy_username}:{mobile_proxy_password}@{host}:{port}"

username_list = ['tlftls82', 'dnjswhnaegelo', 'yangwoogym', 'yahmuchi2000', 'the_special_tkd', 'sualike_vlog', 'sst5747', 'song_am_tkd', 'seungri_tkd', 'segyerohyo', 'ropeholic', 'niceharamdad', 'mijoung0508', 'miisok_', 'ljm_zumba_jumpwingsdongho', 'lee_hwa_jung', 'jung_ddami', 'jumpwings_jinju', 'jmt_baekseok_6', 'jessica_oh_sunmin', 'iplay_official_', 'hoxy_jjine2478', 'hanarin_tkd', 'gieun0606', 'fun_ping_jumprope', 'diet_mk_goal', 'ddodine_', 'dan_taekwondo', 'a8621661', '_rara_mom_', '93life_tkd', 'moonhappy1111', 'angela.lee.8023', 'n__a____j__i_', 'hg4019', 'psw1256', 'hermomunt', 'powerjumping_jinju', 'psw1256', 'worldtkd701', 'wt_tkd1113', 'ujeong._.tkd', 'tizzy0577', 'sung_hyun.choi', 'sunae.noh', 'review12020', 'pdohee', 'no33_seo_jin', 'msangeui', 'maxmara1790', 'maindress_jieun', 'kmj6001', 'k.yongyong', 'jump_school400', 'jjoo_hang_out', 'jhjh0904', 'hyekyung_go', 'holic_luv', 'hj07070318', 'hawan06', 'hanine_living_store', 'gidal83', 'eunjinpyun', 'dahee__h', 'captainkids_playgym', 'c_dragon.1', 'a85458546', 'hi__rami_', 'hyemin_1030', 'hhjjmm1052', 'yuai_sj', 'yjchoi1416', 'suny6253', 'sujung2v', 'segyetaekwondo', 's_suwoo', 'ranny6187', 'myongji._.5', 'kkimmingg', 'jujuhee0628', 'jinju3766', 'jin_a1977', 'jh_tkd_jumprope', 'jeong_dong_jin', 'hwayoung8901', 'dongki_tkd', 'busan_jfrope', 'bonsoir_23', 'bd_tkd', 'ajejek86', 'jjiyang88', 'jeju_yun_yang', 'hn121020', 'kyungae5525', 'jumpwings_hayang', 'an2seul_', 'lazy_wjy', 'fhakd1221', 'frist3333', 'o.vebe', '_growth_story', 'ralra_ralran', 'dawoori0329', 'ihaemin5056', 'jangbongho', 'hi_bomnal.tkd', 'k.sik_h', 'happyhaguna', 'goldentaekwondo']

for idx, username in enumerate(username_list):
    cl.set_proxy(dsn=proxy)
    try:
        userinfo = cl.user_info_by_username(username=username)
        print(idx, userinfo)
    except Exception as e:
        print(f"error occured:{e}/{idx}/{username}")
        continue
