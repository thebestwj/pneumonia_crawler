# coding:utf-8
"""
Name : pneumonia_push.py
Author : thebestwj
Time : 2020/1/22
"""
import requests
import schedule
from bs4 import BeautifulSoup
import pickle
import time
import datetime
import re
import csv

from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr

import smtplib

baseurl = 'https://3g.dxy.cn/newh5/view/pneumonia'
user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.163 " \
             "Safari/535.1 "
headers = {'User-Agent': user_agent}
path = 'pneumonia_data.dat'
logpath = 'pneumonia_log.csv'


def get_news_list():
    url = ''

    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        r.encoding = 'utf-8'

    soup = BeautifulSoup(r.text, 'html.parser')
    timestamps = []
    news_titles = []
    links = []
    # print(soup.find('ul',class_='cg-pic-news-list').find_all('li'))
    for s in soup.find_all('span', class_='art-dateee'):
        timestamps.append(s.get_text())
    for s in soup.find_all('h3'):
        news_titles.append(s.find_all('a')[1]['title'])
        links.append(baseurl + s.find_all('a')[1]['href'])
    return [news_titles, links, timestamps]


def analyzer(soup):
    national = news_context = soup.find('span', class_='content___2hIPS').get_text()
    provincials = []
    temp = soup.find('script', id='getAreaStat').get_text()
    # print(temp)
    provincials = re.findall(
        '"provinceName":".{,5}","provinceShortName":".{,5}","confirmedCount":[\d]+,"suspectedCount":\d+,"curedCount":\d+,"deadCount":\d+',
        temp)
    # print(provincials)
    # print(len(provincials))
    # for provincial in temp:
    #     provincials.append(provincial.get_text()+provincial.next_sibling.next_sibling.get_text())
    realtime_news = []
    # for realtime_new in soup.find_all('p', class_='topicTitle___2ovVO'):
    #     realtime_news.append(realtime_new.get_text())
    time_stamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    return [time_stamp, national, provincials, realtime_news]


def data_processor(mix):
    time_stamp, national, provincials, realtime_news = mix
    temp = re.findall('\d+', national)
    determined = temp[0]
    prob = temp[1]
    cured = temp[2]
    death = temp[3]
    prov_determined_count = 0
    prov_death_count = 0
    prov_prob_count = 0
    zj_determined = 0
    for provincial in provincials:
        prov_determined = 0
        prov_prob = 0
        prov_death = 0
        prov_cured = 0
        temp_list = []
        temp_list = re.findall('\d+', provincial)
        prov_determined = int(temp_list[0])
        prov_prob = int(temp_list[1])
        prov_cured = int(temp_list[2])
        prov_death = int(temp_list[3])
        if prov_determined > 0:
            prov_determined_count = prov_determined_count + 1
        if prov_death > 0:
            prov_death_count = prov_death_count + 1
        if prov_prob > 0:
            prov_prob_count = prov_prob_count + 1
        if re.search('浙江', provincial) is not None:
            temp = re.findall('\d+', provincial)
            zj_determined = temp[0]
    ts_h = time.localtime().tm_hour
    ts_d = time.localtime().tm_mday
    ts_m = time.localtime().tm_mon
    csv_row = [time_stamp, ts_h, ts_d, ts_m, determined, prob, cured, death, prov_determined_count, prov_prob_count,
               prov_death_count, zj_determined, mix]
    return csv_row


def get_number(url):
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        r.encoding = 'utf-8'
    news_soup = BeautifulSoup(r.text, 'html.parser')
    return news_soup


def save(news_pack):
    # with open(path, 'wb') as f:
    #     pickle.dump(news_packs, f)

    with open(logpath, 'a', newline='') as f:
        f_csv = csv.writer(f)
        f_csv.writerow(news_pack)


def load():
    try:
        with open(path, 'rb') as f:
            temp = pickle.load(f)
        return temp
    except IOError:
        print('Error:没有找到文件或读取文件失败')
        return []


def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))


def news_job():
    print('is time to do job! %s' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    news_pack = data_processor(analyzer(get_number(baseurl)))
    save(news_pack)
    print('job done!')
    
	
def record():
    pass


if __name__ == '__main__':
    news_job()
    schedule.every(1).hours.do(news_job)
    print('job scheduled!')
    while True:
        time.sleep(60)
        schedule.run_pending()
