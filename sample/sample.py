#!/usr/bin/env python
#-*- coding:utf-8 -*-

from trading_ig import IGService
from trading_ig_config import *
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

#config = IGServiceConfig()
ig_service = IGService(username, password, api_key, acc_type)
ig_service.create_session()

accounts = ig_service.fetch_accounts()
print("accounts:\n%s" % accounts)

#account_info = ig_service.switch_account(acc_number, False)
#print(account_info)

open_positions = ig_service.fetch_open_positions()
print("open_positions:\n%s" % open_positions)

print("")

working_orders = ig_service.fetch_working_orders()
print("working_orders:\n%s" % working_orders)

print("")

epic = 'CS.D.EURUSD.MINI.IP'
resolution = 'DAY'
num_points = 10
response = ig_service.fetch_historical_prices_by_epic_and_num_points(epic, resolution, num_points)
df_ask = response['prices']['price']['ask']
print("ask prices:\n%s" % df_ask)
