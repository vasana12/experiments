import re
from bs4 import BeautifulSoup
import requests
from datetime import datetime

def cleanse(text) :
    text = re.sub(u"[^\x20-\x7E가-힣]"," ",text)
    text = re.sub(u"\\s+", " ", text)
    return text.strip()

def get_voices():
    page = 1
    while True:
        try:
            domain = "https://www.consumernews.co.kr"
            path = f"/bbs/list.html?page={page}&table=report&sc_category=&sc_area=&sc_word=&sc_word2=&sc_andor=&term_start=&term_end=&goso_pid=&goso_pid2=&ref="
            target_page_url = f"{domain}{path}"

            response = requests.get(target_page_url)
            soup = BeautifulSoup(response.text, "lxml")
            table = soup.find("table", {"class": "hover unstriped report-table"})
            body = table.find("tbody")
            voice_list = body.find_all("tr")

            for idx, voice in enumerate(voice_list):
                voice:BeautifulSoup
                summary = voice.find("span", {"class": "summary"}).text
                summary = cleanse(summary)
                post_date = voice.find_all("td", {"class": "text-center show-for-large"})[1].text
                post_date = datetime.strptime(post_date, "%Y-%m-%d %H:%M ")
                post_date = post_date.date()
                yield {"content": summary, "post_date": post_date}
        except Exception as e:
            print(f"error:{e}")
        else:
            print(f"target_page_url:{target_page_url} ,response:200")
            page += 1

if __name__ == "__main__":
    for item in get_voices():
        print(item)