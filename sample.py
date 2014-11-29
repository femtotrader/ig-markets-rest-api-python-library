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
