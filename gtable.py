# -*- coding: utf-8 -*-
import os
import json
import gspread
import gspread.utils

SPREADSHEET_ID = ""

EMPLOYEE_CHECK = ['']

TG_BOT_TOKEN = ''
TG_CHAT_ID = ''


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
    service_account = json.loads(f.read().replace('%3d', '='))
    f.close()

  gc = gspread.service_account_from_dict(
      os.environ.get('GOOGLE_SERVICE_ACCOUNT'))

  sheet = gc.open_by_key(SPREADSHEET_ID)
  work_sheet = sheet.get_worksheet(0)

  table_seed = work_sheet.get_all_values()
  header = table_seed[:1]
  table = table_seed[1:]

  employee = [em.lower() for em in EMPLOYEE_CHECK]
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

    # parse_mode': 'Markdown',
    #       'text': '*Новое собрание*\n\n`' + theme + '`\n\nДата: ' + date+' ' + time + '\nТип: ' + type + '\nСостав: ' + people


main()
