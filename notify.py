#!/usr/bin/env python3
# _*_ coding:utf-8 _*_

"""
# telegram 推送
export TELEGRAM_BOT_TOKEN='1xxxx6:Axxxxw'
export TELEGRAM_USER_ID='8xxxx2'
export TELEGRAM_BOT_PROXY_URL='https://api.telegram.org'

# 微信推送
export WXPUSHER_APP_TOKEN='Axxxxm'
export WXPUSHER_UIDS='UID_xxxx,UID_xxxx'
"""

import requests
import logging
import os
import re
import json

logging.basicConfig(format='%(asctime)s - lineno:%(lineno)d - func:%(funcName)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    force=True)


class Env:
    def __init__(self, name, tg_bot_token='', tg_user_id='', tg_proxy_url='', wx_app_token='', wx_uids=None):
        if wx_uids is None:
            wx_uids = []
        self.name = name
        self.tg_bot_token = tg_bot_token
        self.tg_user_id = tg_user_id
        self.tg_proxy_url = tg_proxy_url
        self.wx_app_token = wx_app_token
        self.wx_uids = wx_uids

    @staticmethod
    def escape_markdown(text):
        # List of characters to escape for MarkdownV2
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

    def telegram_bot(self, message_type='message', title=None, content=None, file=None):
        try:
            if not self.tg_bot_token or not self.tg_user_id or not self.tg_proxy_url:
                raise ValueError("Telegram bot token, user ID, and proxy URL must be set.")

            url = f'{self.tg_proxy_url}/bot{self.tg_bot_token}/send{message_type.capitalize()}'
            if message_type == 'message':
                escaped_title = self.escape_markdown(title)
                escaped_content = self.escape_markdown(content)
                data = {
                    'chat_id': self.tg_user_id,
                    'text': f'*{escaped_title}*\n\n{escaped_content}',
                    'disable_web_page_preview': 'true',
                    'parse_mode': 'MarkdownV2'
                }
                response = requests.post(url=url, data=data, timeout=15).json()
            elif message_type == 'document' and file:
                with open(file, 'rb') as f:
                    files = {
                        'chat_id': self.tg_user_id,
                        'document': f,
                    }
                    response = requests.post(url=url, files=files, timeout=15).json()
            else:
                raise ValueError("Unsupported type or missing file for document type.")

            if response.get('ok'):
                logging.info('Telegram bot message sent successfully!')
            else:
                logging.error('Telegram bot message failed to send: %s', response)
        except Exception as e:
            logging.error('An error occurred: %s', e)

    def wx_pusher(self, content, summary=None, content_type=3, topic_ids=None, url=None, verify_pay_type=0):
        try:
            if not self.wx_app_token or not self.wx_uids:
                raise ValueError("WxPusher app token and user IDs must be set.")

            wx_pusher_url = 'https://wxpusher.zjiecode.com/api/send/message'
            data = {
                "appToken": self.wx_app_token,
                "content": content,
                "summary": summary if summary else content[:20],
                # Default summary to first 20 chars of content if not provided
                "contentType": content_type,
                "topicIds": topic_ids if topic_ids else [],
                "uids": self.wx_uids,
                "url": url,
                "verifyPayType": verify_pay_type
            }

            headers = {
                'Content-Type': 'application/json'
            }

            response = requests.post(url=wx_pusher_url, data=json.dumps(data), headers=headers, timeout=15).json()

            if response.get('code') == 1000:
                logging.info('WxPusher message sent successfully!')
            else:
                logging.error('WxPusher message failed to send: %s', response)
        except Exception as e:
            logging.error('An error occurred: %s', e)


def send(title, content, push_type=None):
    """
    消息推送模块
    :param title: 消息标题
    :param content: 消息内容
    :param push_type: ['telegram_bot', 'wx_pusher']
    :return:
    """
    if push_type is None:
        push_type = ['telegram_bot']

    tg_bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
    tg_user_id = os.getenv('TELEGRAM_USER_ID', '')
    tg_proxy_url = os.getenv('TELEGRAM_BOT_PROXY_URL', 'https://api.telegram.org')
    wx_app_token = os.getenv('WXPUSHER_APP_TOKEN', '')
    wx_uids = os.getenv('WXPUSHER_UIDS', '').split(',')

    env = Env(name='notify',
              tg_bot_token=tg_bot_token, tg_user_id=tg_user_id, tg_proxy_url=tg_proxy_url,
              wx_app_token=wx_app_token, wx_uids=wx_uids)

    if 'telegram_bot' in push_type:
        env.telegram_bot(message_type='message', title=title, content=content)
    if 'wx_pusher' in push_type:
        env.wx_pusher(content=content,
