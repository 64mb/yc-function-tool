# -*- coding: utf-8 -*-
import os
import json
import gspread
import gspread.utils
from tg import *

SPREADSHEET_ID = os.environ.get('GSPREAD_ID')

EMPLOYEE_CHECK = [os.environ.get('EMPLOYEE')]


class COLUMNS:
  DATE = 0
  TIME = 1
  TYPE = 2
  THEME = 3
  PEOPLE = 4


def main():
  service_account = os.environ.get('GOOGLE_SERVICE_ACCOUNT')
  if service_account.endswith('.json'):
    f = open(service_account, 'r')
    service_account = f.read().replace('%3d', '=')
    f.close()
  service_account = json.loads(service_account)

  gc = gspread.service_account_from_dict(service_account)

  sheet = gc.open_by_key(SPREADSHEET_ID)
  work_sheet = sheet.get_worksheet(0)

  table_seed = work_sheet.get_all_values()
  header = table_seed[:1]
  table = table_seed[1:]

  employee = [em.strip().lower() for em in EMPLOYEE_CHECK]
  for row in table:
    people = row[COLUMNS.PEOPLE]

    people_seed = people.strip().lower()

    user_found = False
    for em in employee:
      if em in people_seed:
        user_found = True
        break

    if not user_found:
      continue

    date = row[COLUMNS.DATE].strip()
    time = row[COLUMNS.TIME].strip()
    type = row[COLUMNS.TYPE].strip().lower()
    theme = row[COLUMNS.THEME].strip()

    seed = date + '###' + time + '###' + type + '###' + theme

    tg.bot.send_message(text='*Новое собрание*\n\n`' + theme + '`\n\nДата: ' + date +
                        ' ' + time + '\nТип: ' + type + '\nСостав: ' + people,  parse_mode='Markdown', chat_id=tg.chat_id)
  return


main()
