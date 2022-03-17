import instaloader

bot = instaloader.Instaloader()
bot.login(user="sauprivesel19751974", passwd="ahfmsek2!")
for i in instaloader.Hashtag.from_name(context=bot.context, name="감자").get_posts():
    print(i.shortcode)
