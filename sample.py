#!/usr/bin/env python
#-*- coding:utf-8 -*-

from ig_service import IGService
from ig_service_config import *

ig_service = IGService(username, password, api_key, acc_type)
ig_service.create_session()

#account_info = ig_service.switch_account(acc_number, False)
#print(account_info)

open_positions = ig_service.fetch_open_positions()
print(open_positions)

epic = 'CS.D.EURUSD.MINI.IP'
resolution = 'DAY'
num_points = 100
response = ig_service.fetch_historical_prices_by_epic_and_num_points(epic, resolution, num_points)
print(response['prices']['price']['ask'])
