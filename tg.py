from logging import log
import os
import json
import telegram
from logger import log


def _init() -> telegram.Bot:
  TG_BOT_TOKEN = os.environ.get('TG_BOT_TOKEN')

  if not TG_BOT_TOKEN:
    log.error('environment variable `TG_BOT_TOKEN` must be set')
    raise NotImplementedError

  return telegram.Bot(TG_BOT_TOKEN)


class tg:
  chat_id = os.environ.get('TG_CHAT_ID', None)
  bot = _init()

  @staticmethod
  def webhook(url):
    log.info('tg webhook url: %u', url)

    webhook = tg.bot.set_webhook(url)

    if webhook:
      log.info('tg ')
    else:
      log.error('tg webhook url error: %u', url)

  @staticmethod
  def update(payload):
    return telegram.Update.de_json(json.loads(payload), tg.bot)
