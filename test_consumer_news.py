import snscrape.modules.twitter as sntwitter


# 키워드로 크롤링
def get_by_keyword(keyword, since, until, location= None):
    if location:
        location = f"near:{location}"
    else:
        location = ""
    query = f'{keyword} {location} since:{since} until:{until}'
    print(query)
    for i, tweet in enumerate(
            sntwitter.TwitterSearchScraper(query).get_items()):
        if i > 5000:
            break
        print(tweet.date, tweet.content, tweet.username, tweet.id, tweet.url)

# 유저 이름으로 크롤링
def get_by_username(username):
    for i, tweet in enumerate(sntwitter.TwitterSearchScraper(f'from:{username}').get_items()):
        print(tweet.date, tweet.id, tweet.content, tweet.username)

keyword = "아이폰"
since = "2022-01-01"
until = "2022-04-25"
location = None
get_by_keyword(keyword, since, until,location)
