import time

import telebot
import json
import threading
import requests
import my_parser


def get_token():
    with open('settings.json', 'r') as file:
        return json.load(file)['bot_token']


bot = telebot.TeleBot(get_token())


@bot.message_handler(commands=['start'])
def start_message(message):
    with open('settings.json', 'r') as f:
        data = json.load(f)
    if message.chat.type == 'group':
        # print(message)
        id_ = message.chat.id
        if id_ not in data['id_channels']:
            data['id_channels'].append(id_)
            bot.send_message(id_, f'<b>Connect successful!</b>', parse_mode="html")
            with open('settings.json', 'w') as f:
                json.dump(data, f)


@bot.message_handler(commands=['disc', 'disconnect', 'd'])
def disconnect_message(message):
    with open('settings.json', 'r') as f:
        data = json.load(f)
    if message.chat.type == 'group':
        # print(message)
        id_ = message.chat.id
        if id_ in data['id_channels']:
            data['id_channels'].pop(data['id_channels'].index(id_))
            bot.send_message(id_, f'<b>Disconnect!</b>', parse_mode="html")
            with open('settings.json', 'w') as f:
                json.dump(data, f)


@bot.message_handler(commands=['add', 'adc', 'ac'])
def add_catalog_message(message):
    if message.chat.type == 'group':
        session = requests.Session()
        session.headers['User-Agent'] = 'Opera/9.80 (Windows NT 6.1; U; en-GB) Presto/2.7.62 Version/11.00'
        url = ""
        text = message.text.split('?')[0]
        text = text.split('/')
        for i in range(len(text)):
            if text[i] == 'catalog':
                url = text[i:]
        url = '/'.join(url)
        hrefs = my_parser.find_category(session, url)
        catalog = my_parser.load_catalog()
        for href in hrefs:
            catalog = my_parser.add_catalog(catalog, href.split('/')[2:])
        my_parser.save_catalog(catalog)
        bot.send_message(message.chat.id, "Add category successful !")


def print_mes_udp():
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('127.0.0.1', 8888))
    try:
        j = 0
        while True:
            with open('settings.json', 'r') as f:
                id_channels = json.load(f)['id_channels']
            if len(id_channels) == 0 or id_channels is None:
                while True:
                    with open('settings.json', 'r') as f:
                        id_channels = json.load(f)['id_channels']
                    if len(id_channels) == 0 or id_channels is None:
                        time.sleep(30)
                    else:
                        break
            print(f'wait {j}')
            received = sock.recv(512)
            received = received.decode("utf-8")
            # print('start')
            # sock.send(bytes('200', encoding='utf-8'))
            # print(received == '')
            # print(received)
            if received == "close":
                print(j)
                time.sleep(1800)
            if received == '' or received is None:
                # # print(f'{received}:')
                # time.sleep(5)
                continue
            received = json.loads(received)
            i = 0
            for chat_id in id_channels:
                try:
                    if "ex_price" in received:
                        bot.send_message(chat_id=chat_id, text=f'<b>{received["name"]}</b> {received["ex_price"]}₽ '
                                                               f'(<del>{received["price"]}₽</del>)\n'
                                                               f'https://www.wildberries.ru/catalog/{received["id"]}'
                                                               f'/detail.aspx',
                                         parse_mode="html")
                    else:
                        bot.send_message(chat_id=chat_id, text=f'<b>{received["name"]}</b> {received["price"]}₽\n'
                                                               f'https://www.wildberries.ru/catalog/{received["id"]}'
                                                               f'/detail.aspx',
                                         parse_mode="html")
                    time.sleep(2)

                    if i == 20:
                        time.sleep(30)
                        i = 0
                    i += 1
                except telebot.apihelper.ApiException as ex:
                    time.sleep(60)
            j += 1
    finally:
        sock.close()


def print_mes():
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('127.0.0.1', 8888))
    try:
        while True:
            with open('settings.json', 'r') as f:
                id_channels = json.load(f)['id_channels']
            if len(id_channels) == 0 or id_channels is None:
                while True:
                    with open('settings.json', 'r') as f:
                        id_channels = json.load(f)['id_channels']
                    if len(id_channels) == 0 or id_channels is None:
                        time.sleep(30)
                    else:
                        break
            received = sock.recv(512)
            received = received.decode("utf-8")
            if received == "close":
                print('close')
                with open('queue.json', 'r') as f:
                    queue = json.load(f)
                while len(queue) > 0:
                    prod = queue[0]
                    try:
                        for chat_id in id_channels:
                            if "ex_price" in prod:
                                bot.send_message(chat_id=chat_id, text=f'<b>{prod["name"]}</b> {prod["ex_price"]}₽ '
                                                                       f'(<del>{prod["price"]}₽</del>)\n'
                                                                       f'https://www.wildberries.ru/catalog/{prod["id"]}'
                                                                       f'/detail.aspx',
                                                 parse_mode="html")
                            else:
                                bot.send_message(chat_id=chat_id, text=f'<b>{prod["name"]}</b> {prod["price"]}₽\n'
                                                                       f'https://www.wildberries.ru/catalog/{prod["id"]}'
                                                                       f'/detail.aspx',
                                                 parse_mode="html")
                    except telebot.apihelper.ApiException as ex:
                        s = ex.result.json()['parameters']['retry_after']
                        print(s)
                        time.sleep(s + 1)
                        continue
                    queue.pop(0)
                with open('queue.json', 'w') as f:
                    json.dump(queue, f)
                sock.sendto(bytes('start', encoding='utf-8'), ('127.0.0.1', 7777))
    finally:
        sock.close()


t1 = threading.Thread(target=bot.polling)
t2 = threading.Thread(target=print_mes)

t1.start()
t2.start()
