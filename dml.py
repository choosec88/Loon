#!/usr/bin/env python3
# _*_ coding:utf-8 _*_

"""
玩一局小游戏
抓包 url：https://game.dominos.com.cn/<dml_activity_id>/game/gameDone 请求参数，例如： openid=xxx&score=xxx&tempId=xxx
环境变量：
    export DML_COOKIES='["openid=xxx&score=xxx&tempId=xxx", "openid=xxx&score=xxx&tempId=xxx"]'
    export DML_ACTIVITY_ID='musangking'
"""

import os
import json
import time
import requests
import random
import logging
import re
from urllib.parse import parse_qs
import notify


logging.basicConfig(force=True, level=logging.INFO, format='%(asctime)s - func:%(funcName)s - lineno:%(lineno)d - %(levelname)s - %(message)s')


class Env:
    def __init__(self, name):
        self.name = name
        self.notify_message = ''
        self.cookie_list = self.to_obj(os.getenv('DML_COOKIES', '[]'))
        self.activity_id = os.getenv('DML_ACTIVITY_ID', 'musangking')
        self.prize_map = {}

        self.load_data_from_json()

    @staticmethod
    def to_obj(string, default=None):
        try:
            return json.loads(string)
        except (json.JSONDecodeError, TypeError):
            return default

    def load_data_from_json(self):
        if not os.path.exists('dml.json'):
            self.prize_map = {}
        else:
            with open('dml.json', mode='r', encoding='utf-8') as f:
                self.prize_map = json.load(f)

    def save_data_to_json(self):
        with open('dml.json', mode='w', encoding='utf-8') as f:
            json.dump(self.prize_map, f, ensure_ascii=False, indent=4)


class Task:
    def __init__(self, index, data, env):
        self.env = env
        self.index = index
        self.openid = None
        self.score = None
        self.tempId = 'null'
        self.headers = {
            'Host': 'game.dominos.com.cn',
            'content-type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.42(0x18002a32) NetType/WIFI Language/zh_CN',
            'Referer': 'https://servicewechat.com/wx887bf6ad752ca2f3/61/page-frame.html',
        }
        self.parse_url_params(data)

    @staticmethod
    def get_random_time():
        return random.randint(1, 10)

    def parse_url_params(self, url_params):
        query_params = parse_qs(url_params)
        self.openid, self.score, self.tempId = query_params.get('openid', [None])[0], query_params.get('score', [None])[
            0], query_params.get('tempId', [None])[0]

    def do_task(self):
        self.sharing_done()
        self.game_done()
        self.my_prize()

    def sharing_done(self):
        try:
            index = 0
            while index <= 3:
                data = {
                    'openid': self.openid,
                    'from': '1',
                    'target': '0'
                }
                response = requests.post(f"https://game.dominos.com.cn/{self.env.activity_id}/game/sharingDone",
                                         headers=self.headers, data=data)
                logging.info(response.text)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("statusCode") == 0:
                        game_num = result.get("content", {}).get("gameNum", 0)
                        logging.info(f"账号 {self.index} 分享成功,抽奖次数+{game_num}")
                        time.sleep(self.get_random_time())
                    else:
                        logging.info(f"账号 {self.index} {result.get('errorMessage')}")
                        break
                else:
                    break
                index += 1
        except Exception as e:
            print(e)

    def game_done(self):
        try:
            index = 1
            while index <= 9:
                data = {
                    'openid': self.openid,
                    'score': self.score,
                    'tempId': self.tempId,
                }
                response = requests.post(f'https://game.dominos.com.cn/{self.env.activity_id}/game/gameDone',
                                         headers=self.headers, data=data)
                if response.status_code == 200:
                    result = response.json()
                    logging.info(result)

                    if result.get('statusCode') == 0:
                        content = result.get('content', {})
                        name = content.get('name', '')
                        logging.info(f'账号 {self.index} 抽奖成功!获得{name}')
                        self.env.prize_map[content.get('id')] = re.sub(r"一张|1张", "", re.sub(r"-\d+", "", name)).strip()
                        time.sleep(self.get_random_time())
                    else:
                        logging.error(result.get('errorMessage', result))
                        break
                else:
                    break
                index += 1
        except Exception as e:
            logging.error(e)

    def my_prize(self):
