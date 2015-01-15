#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
IG Markets REST API Library for Python
http://labs.ig.com/rest-trading-api-reference
By Lewis Barber - 2014 - http://uk.linkedin.com/in/lewisbarber/
Modified by Femto Trader - 2014-2015

"""

import requests
from requests import Session
import json
import logging
import traceback
import os
import datetime
from pandas.io.json import json_normalize
from pandas.tseries.frequencies import to_offset

from version import __author__, __copyright__, __credits__, \
    __license__, __version__, __maintainer__, __email__, __status__, __url__

try:
    import pandas as pd
except ImportError:
    _HAS_PANDAS = False
    logging.warning("Can't import %r" % "pandas")
else:
    _HAS_PANDAS = True

try:
    from bunch import bunchify
except ImportError:
    _HAS_BUNCH = False
    logging.warning("Can't import %r" % "bunch")
else:
    _HAS_BUNCH = True


class ConfigEnvVar(object):
    def __init__(self, env_var_base="IG_SERVICE"):
        self.ENV_VAR_BASE = env_var_base

    def _env_var(self, key):
        return(self.ENV_VAR_BASE + "_" + key.upper())

    def get(self, key, default_value=None):
        return(os.environ.get(self._env_var(key), default_value))

    def __getattr__(self, key):
        return(os.environ[self._env_var(key)])

class IG_Session_CRUD(object):
    """
    Session with CRUD operation
    """
    CLIENT_TOKEN = None
    SECURITY_TOKEN = None

    BASIC_HEADERS = None
    LOGGED_IN_HEADERS = None
    DELETE_HEADERS = None

    BASE_URL = None

    HEADERS = {}

    def __init__(self, base_url, api_key):
        self.BASE_URL = base_url
        self.API_KEY = api_key

        self.HEADERS['BASIC'] = { 
            'X-IG-API-KEY': self.API_KEY,
            'Content-Type': 'application/json', 
            'Accept': 'application/json; charset=UTF-8' 
        }

        self.session = Session() # requests Session

        self.create = self._create_first
        
    def _url(self, endpoint):
        """Returns url from endpoint and base url"""
        return(self.BASE_URL + endpoint)

    def _create_first(self, endpoint, params):
        """Create first = POST with headers=BASIC_HEADERS"""
        url = self._url(endpoint)
        response = self.session.post(url, data=json.dumps(params), headers=self.HEADERS['BASIC'])
        self._set_headers(response.headers, True)
        self.create = self._create_logged_in
        return(response)

    def _create_logged_in(self, endpoint, params):
        """Create when logged in = POST with headers=LOGGED_IN_HEADERS"""
        url = self._url(endpoint)
        response = self.session.post(url, data=json.dumps(params), headers=self.HEADERS['LOGGED_IN'])
        return(response)

    def read(self, endpoint, params):
        """Read = GET with headers=LOGGED_IN_HEADERS"""
        url = self._url(endpoint)
        #print(url, params)
        response = self.session.get(url, params=params, headers=self.HEADERS['LOGGED_IN'])
        return(response)

    def update(self, endpoint, params):
        """Update = PUT with headers=LOGGED_IN_HEADERS"""
        url = self._url(endpoint)
        response = self.session.put(url, data=json.dumps(params), headers=self.HEADERS['LOGGED_IN'])
        return(response)

    def delete(self, endpoint, params):
        """Delete = POST with DELETE_HEADERS"""
        url = self._url(endpoint)
        response = self.session.post(url, data=json.dumps(params), headers=self.HEADERS['DELETE'])
        return(response)

    def _set_headers(self, response_headers, update_cst):
        """Sets headers"""
        if update_cst == True:
            self.CLIENT_TOKEN = response_headers['CST']

        try:
            self.SECURITY_TOKEN = response_headers['X-SECURITY-TOKEN']
        except:
            self.SECURITY_TOKEN = None

        self.HEADERS['LOGGED_IN'] = { 
            'X-IG-API-KEY': self.API_KEY, 
            'X-SECURITY-TOKEN': self.SECURITY_TOKEN, 
            'CST': self.CLIENT_TOKEN, 
            'Content-Type': 'application/json', 
            'Accept': 'application/json; charset=UTF-8' 
        }

        self.HEADERS['DELETE'] = { 
            'X-IG-API-KEY': self.API_KEY, 
            'X-SECURITY-TOKEN': self.SECURITY_TOKEN, 
            'CST': self.CLIENT_TOKEN, 
            'Content-Type': 'application/json', 
            'Accept': 'application/json; charset=UTF-8',
            '_method': 'DELETE'
        }

def conv_resol(resolution):
    d = {
        to_offset('1Min'):'MINUTE',
        to_offset('2Min'):'MINUTE_2',
        to_offset('3Min'):'MINUTE_3',
        to_offset('5Min'):'MINUTE_5',
        to_offset('10Min'):'MINUTE_10',
        to_offset('15Min'):'MINUTE_15',
        to_offset('30Min'): 'MINUTE_30',
        to_offset('1H'): 'HOUR',
        to_offset('2H'): 'HOUR_2',
        to_offset('3H'): 'HOUR_3',
        to_offset('4H'): 'HOUR_4',
        to_offset('D'): 'DAY',
        to_offset('W'): 'WEEK',
        to_offset('M'): 'MONTH'
    }
    try:
        return(d[to_offset(resolution)])
    except:
        return(resolution)

def conv_datetime_v1(dt):
    format = "%Y:%m:%d-%H:%M:%S"
    return(dt.strftime(format))

class IGService:

    D_BASE_URL = {
        'live': 'https://api.ig.com/gateway/deal',
        'demo': 'https://demo-api.ig.com/gateway/deal'
    }

    API_KEY = None
    IG_USERNAME = None
    IG_PASSWORD = None

    def __init__(self, username, password, api_key, acc_type="demo"):
        """Constructor, calls the method required to connect to the API (accepts acc_type = LIVE or DEMO)"""
        self.API_KEY = api_key
        self.IG_USERNAME = username
        self.IG_PASSWORD = password

        try:
            self.BASE_URL = self.D_BASE_URL[acc_type.lower()]
        except:
            raise(Exception("Invalid account type specified, please provide LIVE or DEMO."))

        self.parse_response = self.parse_response_with_exception

        self.return_dataframe = _HAS_PANDAS
        self.return_bunch = _HAS_BUNCH

        self.crud_session = IG_Session_CRUD(self.BASE_URL, self.API_KEY)

    ########## PARSE_RESPONSE ##########

    def parse_response_without_exception(self, *args, **kwargs):
        """Parses JSON response
        returns dict
        no exception raised when error occurs"""
        response = json.loads(*args, **kwargs)
        return(response)

    def parse_response_with_exception(self, *args, **kwargs):
        """Parses JSON response
        returns dict
        exception raised when error occurs"""
        response = json.loads(*args, **kwargs)
        if 'errorCode' in response:
            raise(Exception(response['errorCode']))
        return(response)

    ############ END ############



    ########## DATAFRAME TOOLS ##########

    def colname_unique(self, d_cols):
        """Returns a set of column names (unique)"""
        s = set()
        for col, lst in d_cols.items():
             for colname in lst:
                 s.add(colname)
        return(s)

    def expand_columns(self, data, d_cols, flag_col_prefix=False, col_overlap_allowed=[]):
        """Expand columns"""
        for (col_lev1, lst_col) in d_cols.items():
            ser = data[col_lev1]
            del data[col_lev1]
            for col in lst_col:
                if col not in data.columns or col in col_overlap_allowed:
                    if flag_col_prefix:
                        colname = col_lev1 + "_" + col
                    else:
                        colname = col
                    data[colname] = ser.map(lambda x: x[col])
                else:
                    raise(NotImplementedError("col overlap: %r" % col))
        return(data)

    ############ END ############



    ########## ACCOUNT ##########

    def fetch_accounts(self):
        """Returns a list of accounts belonging to the logged-in client"""
        params = {}
        endpoint = '/accounts'
        response = self.crud_session.read(endpoint, params)
        data = self.parse_response(response.text)
        if self.return_dataframe:
            data = pd.DataFrame(data['accounts'])
            d_cols = {
                'balance': [u'available', u'balance', u'deposit', u'profitLoss']
            }
            data = self.expand_columns(data, d_cols, False)

            if len(data)==0:
                columns = ['accountAlias', 'accountId', 'accountName', 'accountType', 'balance', 'available', 'balance', 'deposit', 'profitLoss', 'canTransferFrom', 'canTransferTo', 'currency', 'preferred', 'status']
                data = pd.DataFrame(columns=columns)
                return(data)

        return(data)

    def fetch_account_activity_by_period(self, milliseconds):
        """Returns the account activity history for the last specified period"""
        params = {}
        endpoint = '/history/activity/%s' % milliseconds
        response = self.crud_session.read(endpoint, params)
        data = self.parse_response(response.text)
        if self.return_dataframe:
            data = pd.DataFrame(data['activities'])

            if len(data)==0:            
                columns = ['actionStatus', 'activity', 'activityHistoryId', 'channel', 'currency', 'date', 'dealId', 'epic', 'level', 'limit', 'marketName', 'period', 'result', 'size', 'stop', 'stopType', 'time']
                data = pd.DataFrame(columns=columns)
                return(data)

        return(data)

    def fetch_transaction_history_by_type_and_period(self, milliseconds, trans_type):
        """Returns the transaction history for the specified transaction type and period"""
        params = {}
        endpoint = '/history/transactions/%s/%s' % (trans_type, milliseconds)
        response = self.crud_session.read(endpoint, params)
        data = self.parse_response(response.text)
        if self.return_dataframe:
            data = pd.DataFrame(data['transactions'])

            if len(data)==0:
                columns = ['cashTransaction', 'closeLevel', 'currency', 'date', 'instrumentName', 'openLevel', 'period', 'profitAndLoss', 'reference', 'size', 'transactionType']
                data = pd.DataFrame(columns=columns)
                return(data)

        return(data)

    ############ END ############



    ########## DEALING ##########

    def fetch_deal_by_deal_reference(self, deal_reference):
        """Returns a deal confirmation for the given deal reference"""
        params = {}
        endpoint = '/confirms/%s' % deal_reference
        response = self.crud_session.read(endpoint, params)
        data = self.parse_response(response.text)
        return(data)

    def fetch_open_positions(self):
        """Returns all open positions for the active account"""
        params = {}
        endpoint = '/positions'
        response = self.crud_session.read(endpoint, params)
        data = self.parse_response(response.text)
        if self.return_dataframe:
            lst = data['positions']
            data = pd.DataFrame(lst)

            d_cols = {
                'market': ['bid', 'delayTime', 'epic', 'expiry', 'high', 'instrumentName', 'instrumentType', 'lotSize', 'low', 'marketStatus', 'netChange', 'offer', 'percentageChange', 'scalingFactor', 'streamingPricesAvailable', 'updateTime'],
                'position': ['contractSize', 'controlledRisk', 'createdDate', 'currency', 'dealId', 'dealSize', 'direction', 'limitLevel', 'openLevel', 'stopLevel', 'trailingStep', 'trailingStopDistance']
            }

            if len(data)==0:
                data = pd.DataFrame(columns=self.colname_unique(d_cols))
                return(data)
            
            #data = self.expand_columns(data, d_cols)
        
        return(data)

    def close_open_position(self, deal_id, direction, epic, expiry, level, order_type, quote_id, size):
        """Closes one or more OTC positions"""
        params = { 
            'dealId': deal_id, 
            'direction': direction, 
            'epic': epic, 
            'expiry': expiry, 
            'level': level,
            'orderType': order_type,
            'quoteId': quote_id,
            'size': size
        }
        endpoint = '/positions/otc'
        response = self.crud_session.delete(endpoint, params)

        if response.status_code == 200:
            deal_reference = json.loads(response.text)['dealReference']
            return(self.fetch_deal_by_deal_reference(deal_reference))
        else:
            return(response.text)

    def create_open_position(self, currency_code, direction, epic, expiry, force_open, 
        guaranteed_stop, level, limit_distance, limit_level, order_type, quote_id, size, 
        stop_distance, stop_level):
        """Creates an OTC position"""
        params = { 
            'currencyCode': currency_code, 
            'direction': direction, 
            'epic': epic, 
            'expiry': expiry, 
            'forceOpen': force_open, 
            'guaranteedStop': guaranteed_stop,
            'level': level,
            'limitDistance': limit_distance,
            'limitLevel': limit_level,
            'orderType': order_type,
            'quoteId': quote_id,
            'size': size,
            'stopDistance': stop_distance,
            'stopLevel': stop_level
        }

        endpoint = '/positions/otc'
        response = self.crud_session.create(endpoint, params)

        if response.status_code == 200:
            deal_reference = json.loads(response.text)['dealReference']
            return(self.fetch_deal_by_deal_reference(deal_reference))
        else:
            return(response.text) # parse_response ?

    def update_open_position(self, limit_level, stop_level, deal_id):
        """Updates an OTC position"""
        params = {
            'limitLevel': limit_level,
            'stopLevel': stop_level
        }

        endpoint = '/positions/otc/%s' % deal_id
        response = self.crud_session.update(endpoint)

        if response.status_code == 200:
            deal_reference = json.loads(response.text)['dealReference']
            return(self.fetch_deal_by_deal_reference(deal_reference))
        else:
            return(response.text) # parse_response ?

    def fetch_working_orders(self):
        """Returns all open working orders for the active account"""
        params = {}
        endpoint = '/workingorders'
        response = self.crud_session.read(endpoint, params)
        data = self.parse_response(response.text)
        if self.return_dataframe:
            lst = data['workingOrders']
            data = pd.DataFrame(lst)

            d_cols = {
                'marketData': [u'instrumentName', u'exchangeId', u'streamingPricesAvailable', u'offer', u'low', u'bid', u'updateTime', u'expiry', u'high', u'marketStatus', u'delayTime', u'lotSize', u'percentageChange', u'epic', u'netChange', u'instrumentType', u'scalingFactor'],
                'workingOrderData': [u'size', u'trailingStopDistance', u'direction', u'level', u'requestType', u'currencyCode', u'contingentLimit', u'trailingTriggerIncrement', u'dealId', u'contingentStop', u'goodTill', u'controlledRisk', u'trailingStopIncrement', u'createdDate', u'epic', u'trailingTriggerDistance', u'dma']
            }

            if len(data)==0:
                data = pd.DataFrame(columns=self.colname_unique(d_cols))
                return(data)

            col_overlap_allowed = ['epic']

            data = self.expand_columns(data, d_cols, False, col_overlap_allowed)

            #d = data.to_dict()
            #data = pd.concat(list(map(pd.DataFrame, d.values())), keys=list(d.keys())).T

        return(data)

    def create_working_order(self, currency_code, direction, epic, expiry, good_till_date, 
        guaranteed_stop, level, limit_distance, limit_level, size, stop_distance, stop_level,
        time_in_force, order_type):
        """Creates an OTC working order"""
        params = { 
            'currencyCode': currency_code, 
            'direction': direction, 
            'epic': epic, 
            'expiry': expiry, 
            'goodTillDate': good_till_date, 
            'guaranteedStop': guaranteed_stop,
            'level': level,
            'limitDistance': limit_distance,
            'limitLevel': limit_level,
            'size': size,
            'stopDistance': stop_distance,
            'stopLevel': stop_level,
            'timeInForce': time_in_force,
            'type': order_type
        }
        endpoint = '/workingorders/otc'
        response = self.crud_session.create(endpoint, params)

        if response.status_code == 200:
            deal_reference = json.loads(response.text)['dealReference']
            return(self.fetch_deal_by_deal_reference(deal_reference))
        else:
            return(response.text) # parse_response ?

    def delete_working_order(self, deal_id):
        """Deletes an OTC working order"""
        params = {}
        endpoint = '/workingorders/otc/%s' % deal_id
        response = self.crud_session.delete(endpoint, params)

        if response.status_code == 200:
            deal_reference = json.loads(response.text)['dealReference']
            return(self.fetch_deal_by_deal_reference(deal_reference))
        else:
            return(response.text) # parse_response ?

    def update_working_order(self, good_till_date, level, limit_distance, limit_level, 
        stop_distance, stop_level, time_in_force, order_type, deal_id):
        """Updates an OTC working order"""
        params = {
            'goodTillDate': good_till_date,
            'limitDistance': limit_distance,
            'level': level,
            'limitLevel': limit_level,
            'stopDistance': stop_distance,
            'stopLevel': stop_level,
            'timeInForce': time_in_force,
            'type': order_type
        }
        endpoint = '/workingorders/otc/%s' % deal_id
        response = self.crud_session.update(endpoint)

        if response.status_code == 200:
            deal_reference = json.loads(response.text)['dealReference']
            return(self.fetch_deal_by_deal_reference(deal_reference))
        else:
            return(response.text) # parse_response ?

    ############ END ############



    ########## MARKETS ##########

    def fetch_client_sentiment_by_instrument(self, market_id):
        """Returns the client sentiment for the given instrument's market"""
        params = {}
        endpoint = '/clientsentiment/%s' % market_id
        response = self.crud_session.read(endpoint, params)
        data = self.parse_response(response.text)
        if self.return_bunch:
            data = bunchify(data)
        return(data)

    def fetch_related_client_sentiment_by_instrument(self, market_id):
        """Returns a list of related (also traded) client sentiment for the given instrument's market"""
        params = {}
        endpoint = '/clientsentiment/related/%s' % market_id
        response = self.crud_session.read(endpoint, params)
        data = self.parse_response(response.text)
        if self.return_dataframe:
            data = pd.DataFrame(data['clientSentiments'])
        return(data)

    def fetch_top_level_navigation_nodes(self):
        """Returns all top-level nodes (market categories) in the market navigation hierarchy."""
        params = {}
        endpoint = '/marketnavigation'
        response = self.crud_session.read(endpoint, params)
        data = self.parse_response(response.text)
        if self.return_dataframe:
            data['markets'] = pd.DataFrame(data['markets'])
            if len(data['markets'])==0:
                columns = ['bid', 'delayTime', 'epic', 'expiry', 'high', 'instrumentName', 'instrumentType', 'lotSize', 'low', 'marketStatus', 'netChange', 'offer', 'otcTradeable', 'percentageChange', 'scalingFactor', 'streamingPricesAvailable', 'updateTime']
                data['markets'] = pd.DataFrame(columns=columns)
            data['nodes'] = pd.DataFrame(data['nodes'])
            if len(data['nodes'])==0:
                columns = ['id', 'name']
                data['nodes'] = pd.DataFrame(columns=columns)
        #if self.return_bunch:
        #    data = bunchify(data) # ToFix: ValueError: The truth value of a DataFrame is ambiguous. Use a.empty, a.bool(), a.item(), a.any() or a.all().
        return(data)

    def fetch_sub_nodes_by_node(self, node):
        """Returns all sub-nodes of the given node in the market navigation hierarchy"""
        params = {}
        endpoint = '/marketnavigation/%s' % node
        response = self.crud_session.read(endpoint, params)
        data = self.parse_response(response.text)
        if self.return_dataframe:
            data['markets'] = pd.DataFrame(data['markets'])
            data['nodes'] = pd.DataFrame(data['nodes'])
        return(data)

    def fetch_market_by_epic(self, epic):
        """Returns the details of the given market"""
        params = {}
        endpoint = '/markets/%s' % epic
        response = self.crud_session.read(endpoint, params)
        data = self.parse_response(response.text)
        if self.return_bunch:
            data = bunchify(data)
        return(data)

    def search_markets(self, search_term):
        """Returns all markets matching the search term"""
        endpoint = '/markets'
        params = {
            'searchTerm': search_term
        }
        response = self.crud_session.read(endpoint, params)
        data = self.parse_response(response.text)
        if self.return_dataframe:
            data = pd.DataFrame(data['markets'])
        return(data)

    def format_prices_old(self, prices):
        """Format prices data as a dict with 
         - 'price' : a Pandas Panel
                ask, bid, last as Items axis
                date as Major_axis axis
                Open High Low Close as Minor_axis axis
         - 'volume' : a timeserie for lastTradedVolume
        """
        df = pd.DataFrame(prices)
        df = df.set_index('snapshotTime')
        df.index.name = 'DateTime'
        df_ask = df[[u'openPrice', u'highPrice', u'lowPrice', u'closePrice']].applymap(lambda x: x['ask'])
        df_bid = df[[u'openPrice', u'highPrice', u'lowPrice', u'closePrice']].applymap(lambda x: x['bid'])
        df_lastTraded = df[[u'openPrice', u'highPrice', u'lowPrice', u'closePrice']].applymap(lambda x: x['lastTraded'])
        ts_lastTradedVolume = df['lastTradedVolume']
        #ts_lastTradedVolume.name = 'Volume'
        panel = pd.Panel.from_dict({'ask': df_ask, 'bid': df_bid, 'last': df_lastTraded})
        panel = panel.rename(minor={'openPrice': 'Open', 'highPrice': 'High', 'lowPrice': 'Low', 'closePrice': 'Close'})
        panel['spread'] = panel['ask'] - panel['bid']
        prices = {}
        prices['price'] = panel

        prices['volume'] = ts_lastTradedVolume
        return(prices)


    def format_prices(self, prices, flag_calc_spread=True):
        """Format prices data as a DataFrame with hierarchical columns"""

        def cols(typ):
            return({
                'openPrice.%s' % typ: 'Open',
                'highPrice.%s' % typ: 'High',
                'lowPrice.%s' % typ: 'Low',
                'closePrice.%s' % typ: 'Close',
                'lastTradedVolume': 'Volume'                
            })

        df = json_normalize(prices)
        df = df.set_index('snapshotTime')
        df.index.name = 'DateTime'

        df_ask = df[['openPrice.ask', 'highPrice.ask', 'lowPrice.ask', 'closePrice.ask']]
        df_ask = df_ask.rename(columns=cols('ask'))

        df_bid = df[['openPrice.bid', 'highPrice.bid', 'lowPrice.bid', 'closePrice.bid']]
        df_bid = df_bid.rename(columns=cols('bid'))

        if flag_calc_spread:
            df_spread = df_ask - df_bid

        df_last = df[['openPrice.lastTraded', 'highPrice.lastTraded', 'lowPrice.lastTraded', 'closePrice.lastTraded', 'lastTradedVolume']]
        df_last = df_last.rename(columns=cols('lastTraded'))

        if not flag_calc_spread:
            df2 = pd.concat([df_bid, df_ask, df_last], axis=1, keys=['bid', 'ask', 'last'])
        else:
            df2 = pd.concat([df_bid, df_ask, df_spread, df_last], axis=1, keys=['bid', 'ask', 'spread', 'last'])
        return(df2)

    def fetch_historical_prices_by_epic_and_num_points(self, epic, resolution, num_points):
        """Returns a list of historical prices for the given epic, resolution, number of points"""
        resolution = conv_resol(resolution)
        params = {}
        endpoint = "/prices/{epic}/{resolution}/{numpoints}".format(epic=epic, resolution=resolution, numpoints=num_points)
        response = self.crud_session.read(endpoint, params)
        data = self.parse_response(response.text)
        if self.return_dataframe:
            data['prices'] = self.format_prices(data['prices'])
        return(data)

    def fetch_historical_prices_by_epic_and_date_range(self, epic, resolution, start_date, end_date):
        """Returns a list of historical prices for the given epic, resolution, multiplier and date range"""
        resolution = conv_resol(resolution)
        # v2
        #format = "%Y-%m-%d %H:%M:%S"
        #if isinstance(start_date, datetime.datetime):
        #    start_date = start_date.strftime(format)
        #if isinstance(end_date, datetime.datetime):
        #    end_date = end_date.strftime(format)
        #endpoint = "/prices/{epic}/{resolution}/{startDate}/{endDate}".format(epic=epic, resolution=resolution, startDate=start_date, endDate=end_date)
        #params = {}

        # v1
        #date="2014:12:15-00:00:00"
        if isinstance(start_date, datetime.datetime):
            start_date = conv_datetime_v1(start_date)
        if isinstance(end_date, datetime.datetime):
            end_date = conv_datetime_v1(end_date)
        endpoint = "/prices/{epic}/{resolution}".format(epic=epic, resolution=resolution)
        params = {
            'startdate': start_date,
            'enddate': end_date
        }
        response = self.crud_session.read(endpoint, params)
        data = self.parse_response(response.text)
        if self.return_dataframe:
            data['prices'] = self.format_prices(data['prices'])
        return(data)

    ############ END ############



    ######### WATCHLISTS ########

    def fetch_all_watchlists(self):
        """Returns all watchlists belonging to the active account"""
        params = {}
        endpoint = '/watchlists'
        response = self.crud_session.read(endpoint, params)
        data = self.parse_response(response.text)
        if self.return_dataframe:
            data = pd.DataFrame(data['watchlists'])
        return(data)

    def create_watchlist(self, name, epics):
        """Creates a watchlist"""
        params = { 
            'name': name, 
            'epics': epics
        }
        endpoint = '/watchlists'
        response = self.crud_session.create(endpoint, params)
        data = self.parse_response(response.text)
        return(data)

    def delete_watchlist(self, watchlist_id):
        """Deletes a watchlist"""
        params = {}
        endpoint = '/watchlists/%s' % watchlist_id
        response = self.crud_session.delete(endpoint, params)
        return(response.text)


    def fetch_watchlist_markets(self, watchlist_id):
        """Returns the given watchlist's markets"""
        params = {}
        endpoint = '/watchlists/%s' % watchlist_id
        response = self.crud_session.read(endpoint, params)
        data = self.parse_response(response.text)
        if self.return_dataframe:
            data = pd.DataFrame(data['markets'])
        return(data)


    def add_market_to_watchlist(self, watchlist_id, epic):
        """Adds a market to a watchlist"""
        params = { 
            'epic': epic
        }
        endpoint = '/watchlists/%s' % watchlist_id
        response = self.crud_session.update(endpoint, params)
        data = self.parse_response(response.text)
        return(data)

    def remove_market_from_watchlist(self, watchlist_id, epic):
        """Remove an market from a watchlist"""
        params = {}
        endpoint = '/watchlists/%s/%s' % (watchlist_id, epic)
        response = self.crud_session.delete(endpoint, params)
        return(response.text)

    ############ END ############



    ########### LOGIN ###########

    def logout(self):
        """Log out of the current session"""
        params = {}
        endpoint = '/session'
        response = self.crud_session.delete(endpoint, params)

    def create_session(self):
        """Creates a trading session, obtaining session tokens for subsequent API access"""
        params = { 
            'identifier': self.IG_USERNAME, 
            'password': self.IG_PASSWORD 
        }
        endpoint = '/session'
        response = self.crud_session.create(endpoint, params) # first create (BASIC_HEADERS)
        data = self.parse_response(response.text)
        return(data)

    def switch_account(self, account_id, default_account):
        """Switches active accounts, optionally setting the default account"""
        params = { 
            'accountId': account_id, 
            'defaultAccount': default_account
        }
        endpoint = '/session'
        response = self.crud_session.update(endpoint, params)
        self._set_headers(response.headers, False)
        data = self.parse_response(response.text)
        return(data)

    ############ END ############



    ########## GENERAL ##########
    
    def get_client_apps(self):
        """Returns a list of client-owned applications"""
        params = {}
        endpoint = '/operations/application'
        response = self.crud_session.read(endpoint, params)
        data = self.parse_response(response.text)
        return(data)

    def update_client_app(self, allowance_account_overall, allowance_account_trading, api_key, status):
        """Updates an application"""
        params = { 
            'allowanceAccountOverall': allowance_account_overall, 
            'allowanceAccountTrading': allowance_account_trading, 
            'apiKey': api_key, 
            'status': status
        }
        endpoint = '/operations/application'
        response = self.crud_session.update(endpoint, params)
        data = self.parse_response(response.text)
        return(data)

    def disable_client_app_key(self):
        """Disables the current application key from processing further requests. 
        Disabled keys may be reenabled via the My Account section on the IG Web Dealing Platform."""
        params = {}
        endpoint = '/operations/application/disable'
        response = self.crud_session.update(endpoint, params)
        data = self.parse_response(response.text)
        return(data)
        
    ############ END ############
