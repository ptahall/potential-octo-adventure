import time
import threading
import requests
from bs4 import BeautifulSoup
import json
import socket
import datetime

# session = requests.Session()
# session.headers['User-Agent'] = 'Opera/9.80 (Windows NT 6.1; U; en-GB) Presto/2.7.62 Version/11.00'


def add_catalog(cat, href, n=0):
    if href[n] not in cat:
        cat.append(href[n])
        if len(href) == n + 1:
            cat.append({})
            return cat
        else:
            cat.append([])
            cat[len(cat) - 1] = add_catalog(cat[len(cat) - 1], href, n + 1)
    else:
        if len(href) == n + 1:
            return cat
        i = cat.index(href[n])
        if type(cat[i + 1]) is dict:
            cat[i + 1] = []
        cat[i + 1] = add_catalog(cat[i + 1], href, n + 1)
    return cat


def find_category(s, url):
    if not url.startswith('https'):
        url = 'https://www.wildberries.ru/' + url
    r = s.get(url)
    # print(r.url)
    soup = BeautifulSoup(r.text, 'html.parser')
    div = soup.find('div', class_='left')
    hrefs = []
    if div is None:
        div = soup.find('ul', class_='sidemenu').find('ul')
        if div is None:
            div = soup.find('ul', class_='sidemenu')
    for li in div.findAll('li'):
        a = li.find('a')
        if a is not None:
            h = a.get('href')
            if 'https://www.wildberries.ru' + h == r.url:
                return [h]
            hrefs += find_category(s, 'https://www.wildberries.ru' + h)
    return hrefs


def save_catalog(cat):
    with open('pars.json', 'w') as f:
        json.dump(cat, f)


def load_catalog():
    with open('pars.json', 'r') as f:
        return json.load(f)


def save_products(pr):
    with open('product.json', 'w') as f:
        json.dump(pr, f)


def load_products():
    with open('product.json', 'r') as f:
        return json.load(f)


def old_parse_catalog(cat, url='', s=None, cl=None):
    # print(cl)
    if type(cat) is dict:
        i = 1
        print(url)
        while True:
            print(i)
            r = s.get(f'https://www.wildberries.ru/catalog{url}?page={i}')
            # print(r.url)
            if r.status_code == 404:
                break
            if r.status_code != 200:
                i += 1
                continue
            id_ = []
            soup = BeautifulSoup(r.text, 'html.parser')
            for div in soup.findAll('div', class_='dtList i-dtList j-card-item'):
                id_.append(div.get('data-popup-nm-id'))
            r = s.get(f'https://nm-2-card.wildberries.ru/enrichment/v1/api?spp=0&regions=69,33,68,75,63,64,48,40,30,'
                      f'1,4,31,71,22,38,65,66,70&nm={";".join(id_)}')
            if r.status_code != 200:
                i += 1
                continue
            data = r.json()['data']['products']
            for d in data:
                otv = None
                if str(d['id']) in cat:
                    if 'extended' not in d:
                        if d['price'] > 50:
                            cat.pop(d['id'])
                            continue
                        elif d['price'] <= 50:
                            c_price = cat[str(d['id'])]['price']
                            if d['price'] != c_price:
                                cat[str(d['id'])]['price'] = d['price']
                                otv = {'id': d['id'], 'name': cat[str(d['id'])]['name'], 'price': d['price']}
                    else:
                        price = get_price(d['extended'])
                        c_price = cat[str(d['id'])]['price']
                        if price is None:
                            continue
                        if price > 1000:
                            cat.pop(d['id'])
                            continue
                        if price != c_price:
                            sail = round(100 - (price / d['price']) * 100)
                            if sail >= 80:
                                # print(sail)
                                cat[str(d['id'])]['price'] = price
                                otv = {'id': d['id'], 'name': cat[str(d['id'])]['name'], 'ex_price': price,
                                       'price': d['price']}
                            else:
                                cat.pop(d['id'])
                                continue
                        else:
                            continue
                else:
                    if 'extended' not in d:
                        if d['price'] <= 50:
                            cat[d['id']] = {'name': d['name'], 'price': d['price']}
                            otv = {'id': d['id'], 'name': cat[str(d['id'])]['name'], 'price': d['price']}
                        else:
                            continue
                    else:
                        price = get_price(d['extended'])
                        if price is None:
                            continue
                        if price <= 1000:
                            sail = round(100 - (price / d['price']) * 100)
                            # print(type(d['id']))
                            if sail >= 80:
                                # print(sail)
                                cat[d['id']] = {'name': d['name'], 'price': price}
                                otv = {'id': d['id'], 'name': d['name'], 'ex_price': price, 'price': d['price']}
                        else:
                            continue
                if otv is None:
                    continue
                # otv = json.dumps(otv)
                # # print(otv)
                # cl.send(bytes(otv, encoding='utf-8'))
                # rec = cl.recv(512)
                # rec = rec.decode('utf-8')
                # print(rec)
                # print(type(rec))
            i += 1
            # break
        return cat
    else:
        for i in range(len(cat) - 1):
            if type(cat[i]) is str:
                cat[i + 1] = old_parse_catalog(cat[i + 1], url + f"/{cat[i]}", s, cl=cl)
    return cat


def get_price(extended):
    if 'promoPrice' in extended:
        return extended['promoPrice']
    elif 'basicPrice' in extended:
        return extended['basicPrice']


# if __name__ == '__main__':
#     # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     # sock.bind(('127.0.0.1', 8888))
#     # sock.listen(1)
#     try:
#         # client, adr = sock.accept()
#
#         session = requests.Session()
#         session.headers['User-Agent'] = 'Opera/9.80 (Windows NT 6.1; U; en-GB) Presto/2.7.62 Version/11.00'
#         i = 0
#         while i <= 0:
#             catalog = load_catalog()
#             save_catalog(parse_catalog(catalog, s=session, cl=None))
#             print('yes')
#             # time.sleep(1800)
#             i += 1
#     finally:
#         # sock.close()
#         pass

# print(find_category(session, 'catalog/zhenshchinam/plyazhnaya-moda'))
# print(parse_catalog(load_catalog(), s=session))

# r = session.get(f'https://nm-2-card.wildberries.ru/enrichment/v1/api?spp=0&regions=69,33,68,75,63,64,48,40,30,'
#                 f'1,4,31,71,22,38,65,66,70&nm=397887;')

def pars(cat, product: dict, url='', req=None, s=None, udp=None, que: list = None):
    if type(cat) is dict:
        # print(url)
        if req is None:
            page = 1
            thread = []
            while page < 2:
                try:
                    s = requests.Session()
                    s.headers['User-Agent'] = 'Opera/9.80 (Windows NT 6.1; U; en-GB) Presto/2.7.62 Version/11.00'
                    req = s.get(f'https://www.wildberries.ru/catalog{url}?page={page}')
                except requests.exceptions.ConnectionError:
                    print(f'https://www.wildberries.ru/catalog{url}?page={page}')
                if req.status_code == 404:
                    break
                if req.status_code != 200:
                    page += 1
                    continue
                t = threading.Thread(target=pars, args=(cat, product, req.url, req, s, udp, que))
                t.start()
                thread.append(t)
                page += 1
            for t in thread:
                t.join()
            # print(product)
            return product
        else:
            _id = []
            soup = BeautifulSoup(req.text, 'html.parser')
            for div in soup.findAll('div', class_='dtList i-dtList j-card-item'):
                _id.append(div.get('data-popup-nm-id'))
            r = s.get(f'https://nm-2-card.wildberries.ru/enrichment/v1/api?spp=0&regions=69,33,68,75,63,64,48,40,30,'
                      f'1,4,31,71,22,38,65,66,70&nm={";".join(_id)}')
            if r.status_code != 200:
                return product
            data = r.json()['data']['products']
            for d in data:
                otv = None
                if str(d['id']) in product:
                    if 'extended' not in d:
                        if d['price'] > 50:
                            product.pop(str(d['id']))
                            continue
                        elif d['price'] <= 50:
                            c_price = product[str(d['id'])]['price']
                            if d['price'] != c_price:
                                product[str(d['id'])]['price'] = d['price']
                                otv = {'id': d['id'], 'name': product[str(d['id'])]['name'], 'price': d['price']}
                    else:
                        price = get_price(d['extended'])
                        c_price = product[str(d['id'])]['price']
                        if price is None:
                            continue
                        if price > 1000:
                            product.pop(str(d['id']))
                            continue
                        if price != c_price:
                            sail = round(100 - (price / d['price']) * 100)
                            if sail >= 80:
                                # print(sail)
                                product[str(d['id'])]['price'] = price
                                otv = {'id': d['id'], 'name': product[str(d['id'])]['name'], 'ex_price': price,
                                       'price': d['price']}
                            else:
                                product.pop(str(d['id']))
                                continue
                        else:
                            continue
                else:
                    if 'extended' not in d:
                        if d['price'] <= 50:
                            product.update({str(d['id']): {'name': d['name'], 'price': d['price']}})
                            # product[d['id']] = {'name': d['name'], 'price': d['price']}
                            otv = {'id': d['id'], 'name': d['name'], 'price': d['price']}
                        else:
                            continue
                    else:
                        price = get_price(d['extended'])
                        if price is None:
                            continue
                        if price <= 1000:
                            sail = round(100 - (price / d['price']) * 100)
                            # print(type(d['id']))
                            if sail >= 80:
                                # print(sail)
                                product.update({str(d['id']): {'name': d['name'], 'price': price}})
                                # cat[d['id']] = {'name': d['name'], 'price': price}
                                otv = {'id': d['id'], 'name': d['name'], 'ex_price': price, 'price': d['price']}
                        else:
                            continue
                if otv is None:
                    continue
                print(otv)
                que.append(otv)
            # print(product)
            return product

    else:
        thread = []
        for i in range(len(cat)):
            if type(cat[i]) is str:
                thread.append(
                    threading.Thread(target=pars, args=(cat[i + 1], product, url + f"/{cat[i]}", None, s, udp, que)))
        for t in thread:
            t.start()
        for t in thread:
            t.join()
        # udp.sendto(bytes('close', encoding='utf-8'), ('127.0.0.1', 8888))
    return product


if __name__ == '__main__':
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('127.0.0.1', 7777))
    # t = datetime.datetime.now()
    while True:
        t = datetime.datetime.now()
        prod = load_products()
        queue = []
        pars(load_catalog(), prod, s=None, udp=sock, que=queue)
        with open('product.json', 'w') as f:
            json.dump(prod, f)
        with open('queue.json', 'w') as f:
            json.dump(queue, f)
        # print((datetime.datetime.now() - t).seconds)
        sock.sendto(bytes('close', encoding='utf-8'), ('127.0.0.1', 8888))
        received = sock.recv(512)
        received = received.decode("utf-8")
        if received == "start":
            print(f'start  {1800 - (datetime.datetime.now() - t).seconds}')
            if 1800 - (datetime.datetime.now() - t).seconds > 0:
                time.sleep(1800 - (datetime.datetime.now() - t).seconds)
            continue
