
import re
import time
import csv
import pymysql
import requests
from bs4 import BeautifulSoup as bs
import yaml
import datetime

def load_config(config_file):
    with open(config_file, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

config = load_config('config.yml')

host = config['db']['host']
user = config['db']['user']
passwd = config['db']['pass']
db = config['db']['db']
table = config['db']['table']

headers = {'accept': '*/*',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Safari/537.36'}

base_url = 'https://www.avito.ru/neryungri/kvartiry/prodam?p=1&cd=1&f=549_5696-5697'

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
                url = f'https://www.avito.ru/neryungri/kvartiry/prodam?p={i+1}&cd=1&f=549_5696-5697'
                
                if url not in urls:
                    urls.append(url)
        except:
            pass
        for url in urls:
            request = session.get(url, headers=headers)
            soup = bs(request.content, 'lxml')
            divs = soup.find_all('div', attrs={'class': 'item_table'})
            for div in divs:
                item_id =  div.find('button', attrs={'class': 'js-item-extended-contacts'})['data-item-id']
                date =  div.find('div', attrs={'class': 'js-item-date'})['data-absolute-date']
                title = sub(div.find('span', attrs={'itemprop': 'name'}).text)
                price = div.find('span', attrs={'itemprop': 'price'}).text
                address = div.find('span', attrs={'class': 'item-address__string'}).text
                href = 'https://www.avito.ru' + div.find('a', attrs={'class': 'item-description-title-link'})['href']

                apartments.append({
                    'item_id': item_id,
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
                #print(apartments)
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
        a_pen.writerow(('item_id', 'Дата', 'Название объявления', 'Цена', 'Адрес', 'Ссылка'))
        for apartment in apartments:
            a_pen.writerow((apartment['item_id'], apartment['date'], apartment['title'], apartment['price'], apartment['address'], apartment['href']))
            #print(apartment)

def add_item(apartments):
    connection = pymysql.connect(
    host=host,
    user=user,
    password=passwd,
    db=db,
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
    )

    sql_search = "SELECT item_id FROM " + table + " WHERE item_id = %s"
    sql_add = "INSERT INTO "+ table + "(`item_id`, `date`, `name`, `price`, `address`, `link`) VALUES (%s, %s, %s, %s, %s, %s)"

    try:
         with connection.cursor() as cursor:
            for apartment in apartments:
                item_id = int(apartment['item_id'])
                date = datetime.datetime.today()
                name = apartment['title']
                price = int(re.sub('\D+','',  apartment['price']))
                address = apartment['address']
                link = apartment['href']
                cursor.execute(sql_search, (item_id, ))
                # gets the number of rows affected by the command executed
                rows=cursor.rowcount
                if rows == 0:
                    cursor.execute(sql_add, (item_id, date, name, price, address, link))
                    print ("Новое объявление ---> ",  item_id, date, name, price, address)
                else:
                    print ("Есть запись")

                # Create a new record
                #cursor.execute(sql_add, (item_id, date, name, price, address, link))
            connection.commit()

    # with connection.cursor() as cursor:
    #     # Read a single record
    #     sql = "SELECT `item_id`, `date` FROM `one_room` WHERE `link`=%s"
    #     cursor.execute(sql, ('link',))
    #     result = cursor.fetchone()
    #     print(result)
    finally:
        cursor.close()
        connection.close()

apartments = parse(base_url,headers)
#writer_csv(apartments)
add_item(apartments)