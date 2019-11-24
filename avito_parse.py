import re
import time
import csv

import requests
from bs4 import BeautifulSoup as bs

headers = {'accept': '*/*',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Safari/537.36'}

base_url = 'https://www.avito.ru/neryungri/kvartiry/prodam/1-komnatnye?p=1&cd=1&f=59_0b0.496_0b0.497_0b0'

def sub(str):
    str = re.sub(r'\n|\s+', ' ', str).strip()
    return (str)

def parse(base_url, headers):
    apartments = []
    urls = []
    urls.append(base_url)
    session = requests.session()
    request = session.get(base_url, headers=headers)
    if request.status_code == 200:
        start = time.time()
        soup = bs(request.content, 'lxml')
        try:
            pagination = soup.find_all('a', attrs={'class': 'pagination-page'})
            count = int(pagination[-2].text)
            for i in range(count):
                url = f'https://www.avito.ru/neryungri/kvartiry/prodam/1-komnatnye?p={i+1}&cd=1&f=59_0b0.496_0b0.497_0b0'

                if url not in urls:
                    urls.append(url)
        except:
            pass
        for url in urls:
            request = session.get(url, headers=headers)
            soup = bs(request.content, 'lxml')
            divs = soup.find_all('div', attrs={'class': 'item_table'})
            for div in divs:
                date = sub(div.find('div', attrs={'data-marker': 'item-date'}).text)
                title = div.find('span', attrs={'itemprop': 'name'}).text
                price = div.find('span', attrs={'class': 'price price_highlight'})
                address = div.find('span', attrs={'class': 'item-address__string'}).text
                href = 'https://www.avito.ru' + div.find('a', attrs={'class': 'item-description-title-link'})['href']

                apartments.append({
                    'date': date,
                    'title': title,
                    'price': price,
                    'address': address,
                    'href': href
                    #'company': company,
                    # 'city': city,
                    # 'salary': salary,
                    # 'content': content,
                    # 'href': href
                })
        finish = time.time()

        print('Спарсено ' + str(len(apartments)) + ' позиции за ' + str(finish - start))
        #print(apartments)
        # a_pen = open('index.html', 'w')
        # a_pen.write(str(soup))
        # a_pen.close()
    else:
        print('ERROR')
    return apartments

def writer_csv(apartments):
    with open('parse_avito.csv', 'w', encoding='utf8') as file:
        a_pen = csv.writer(file)
        a_pen.writerow(('Дата', 'Название объявления', 'Цена', 'Адрес', 'Ссылка'))
        for apartment in apartments:
            a_pen.writerow((apartment['date'], apartment['title'], apartment['price'], apartment['address'], apartment['href']))

apartments = parse(base_url,headers)
writer_csv(apartments)