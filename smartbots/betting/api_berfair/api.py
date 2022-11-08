__version__ = 0.06

import os
import json
from os.path import join
import datetime as dt

try:
    import requests
except:
    msg = 'ERROR: Requests module not installed.\n'
    msg += 'INSTALLATION (run as admin):\n'
    msg += '1. Install "pip": http://pip.readthedocs.org/en/latest/installing.html\n'
    msg += '2. Install "requests": pip install requests'
    print(msg)
    exit()


class Api(object):
    """betfair api-ng library"""

    def __init__(self, path_ssl_certs, aus=False, ssl_prefix='', locale='', ):
        """initiate the api-ng library.
        @aus: type = boolean. if True, use australian endpoints (default = UK exchange)
        @ssl_prefix: type = string. prefix for ssl certs, e.g. 'USERNAME' if certs
            are named 'USERNAME.key', 'USERNAME.crt' or 'USERNAME.pem'
        @locale: type = string. if empty, defaults to your account language.
            ISO codes: http://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
        """
        self.abs_path = os.path.abspath(os.path.dirname(__file__))
        self.certs_paths = self.load_ssl_cert_paths(path_ssl_certs, ssl_prefix)
        self.aus = aus
        self.app_key = ''  # Use create_app_keys() or see online api docs.
        self.locale = locale
        self.session_token = ''

    def load_ssl_cert_paths(self, path_ssl_certs, ssl_prefix=''):
        """loads the ssl cert filepaths.
        @ssl_prefix: type = string. the prefix of your .key, .crt or .pem files.
        HINT: save your certs with your username as prefix, e.g. 'USERNAME.key'
        NOTE: ssl_certs folder MUST contain either a .key/.crt pair OR a single .pem file.
        For help, see: https://api.developer.betfair.com/services/webapps/docs/display/1smk3cen4v3lu3yomq5qye0ni/Non-Interactive+%28bot%29+login
        """
        if not ssl_prefix:
            msg = 'Missing parameter ssl_prefix in API __init__()'
            raise Exception(msg)
        cert_paths = []
        ssl_path = path_ssl_certs
        if os.path.exists(ssl_path):
            filenames = os.listdir(ssl_path)
            for filename in filenames:
                if ssl_prefix in filename:
                    ext = filename.rpartition('.')[2]
                    if ext in ['key', 'crt', 'pem']:
                        cert_path = join(ssl_path, filename)
                        cert_paths.append(cert_path)
        cert_paths.sort()  # sort order = [xxx.crt, xxx.key] OR ['.pem']
        # verify
        if not cert_paths:
            msg = 'SSL CERTS NOT FOUND!\n'
            msg += 'Please ensure that %s exists and contains valid ssl certificates.\n' % ssl_path
            msg += 'Valid files are either a .key and .crt pair OR a single .pem.\n'
            msg += 'For help, see: %s\n' % 'https://api.developer.betfair.com/services/webapps/docs/display/1smk3cen4v3lu3yomq5qye0ni/Non-Interactive+%28bot%29+login'
            msg += 'Also ensure that you have entered a valid USERNAME in manager.py!'
            raise Exception(msg)
        return cert_paths

    def send_http_request(self, url='', data=''):
        """send http request to betfair server & return response"""
        # set headers (defaults = betting operations)
        ssl_cert = None  # default if not using ssl certs
        content_type = 'application/json'
        if 'identitysso-cert.betfair.com' in url:
            # setup for account operations (using ssl certs)
            content_type = 'application/x-www-form-urlencoded'
            ssl_cert = self.certs_paths
        # create header
        headers = {
            'Accept': 'application/json',
            'Content-Type': content_type,
            'Content-Length': str(len(data)),
            'X-Authentication': self.session_token,
            'Connection': 'keep-alive',
            'Accept-Encoding': 'gzip'
        }
        # check if we need to send app_key
        if 'DeveloperAppKeys' not in data:  # NOT a get/createDeveloperAppKeys request
            headers['X-Application'] = self.app_key
        # send request
        if data:  # POST
            resp = requests.post(url, data, cert=ssl_cert, headers=headers, timeout=60)
        else:  # GET
            resp = requests.get(url, cert=ssl_cert, headers=headers, timeout=60)
        # check response
        if resp.status_code == 200:
            # save session token
            resp_json = resp.json()
            if 'sessionToken' in resp_json:
                self.session_token = resp_json['sessionToken']
            # return json
            return resp_json
        else:
            # error
            msg = 'HTTP %s. json = %s' % (resp.status_code, resp.json)
            raise Exception(msg)

    def login(self, username='', password=''):
        """login to betfair api-ng. returns string.
        @username: type = string
        @password: type = string
        """
        url = 'https://identitysso-cert.betfair.com/api/certlogin'
        data = 'username=%s&password=%s' % (username, password)
        resp = self.send_http_request(url, data)
        if type(resp) is dict and 'loginStatus' in resp:
            return resp['loginStatus']
        else:
            raise Exception(str(resp))

    def keep_alive(self):
        """keep login session alive. returns string.
        NOTE: betfair limit = one call every 7 minutes
        """
        url = 'https://identitysso-cert.betfair.com/api/keepAlive'
        resp = self.send_http_request(url)
        if type(resp) is dict and 'status' in resp:
            return resp['status']
        else:
            raise Exception(str(resp))

    def logout(self):
        """logout from betfair api-ng. returns string."""
        url = 'https://identitysso-cert.betfair.com/api/logout'
        resp = self.send_http_request(url)
        if type(resp) is dict and 'status' in resp:
            return resp['status']
        else:
            raise Exception(str(resp))

    def get_account_funds(self, req_id=1):
        """returns json containing account funds
        @req_id: type = integer. OPTIONAL request id number (for customer use only)
        """
        url = 'https://api.betfair.com/exchange/account/json-rpc/v1'
        if self.aus: url = 'https://api-au.betfair.com/exchange/account/json-rpc/v1'
        req = {
            'jsonrpc': '2.0',
            'method': 'AccountAPING/v1.0/getAccountFunds',
            'id': req_id,
            'params': {}
        }
        req = json.dumps(req)  # convert dict to json format
        resp = self.send_http_request(url, req)
        if type(resp) is dict and 'result' in resp:
            return resp['result']
        else:
            raise Exception(str(resp))

    def get_account_details(self, req_id=1):
        """returns json containing account details
        @req_id: type = integer. OPTIONAL request id number (for customer use only)
        """
        url = 'https://api.betfair.com/exchange/account/json-rpc/v1'
        if self.aus: url = 'https://api-au.betfair.com/exchange/account/json-rpc/v1'
        req = {
            'jsonrpc': '2.0',
            'method': 'AccountAPING/v1.0/getAccountDetails',
            'id': req_id,
            'params': {}
        }
        req = json.dumps(req)  # convert dict to json format
        resp = self.send_http_request(url, req)
        if type(resp) is dict and 'result' in resp:
            return resp['result']
        else:
            raise Exception(str(resp))

    def get_account_statement(self, params=None, req_id=1):
        """returns json containing account statement
        @req_id: type = integer. OPTIONAL request id number (for customer use only)
        @params: type = dict.
        example:
        {
            'fromRecord': 0, # type = integer. use for paging.
            'includeItem': 'ALL', # type = string. options = 'EXCHANGE, 'ALL', 'DEPOSITS_WITHDRAWALS' or 'POKER_ROOM'
            'recordCount': 100, # type = integer. max = 100 per page.
            'wallet': 'UK', # type = string. options = 'UK' or 'AUSTRALIAN'
            'itemDateRange': {
                'from': '2014-05-19T20:54:19Z', # type = string. ISO formatted date.
                'to': '2014-05-20T20:54:19Z' # type = string. ISO formatted date.
            }
        }
        NOTE: itemDateRange is ONLY used if includeItem = 'ALL'
        """
        url = 'https://api.betfair.com/exchange/account/json-rpc/v1'
        if self.aus: url = 'https://api-au.betfair.com/exchange/account/json-rpc/v1'
        # build request
        params['locale'] = self.locale
        req = {
            'jsonrpc': '2.0',
            'method': 'AccountAPING/v1.0/getAccountStatement',
            'id': req_id,
            'params': params,
        }
        req = json.dumps(req)  # convert dict to json format
        resp = self.send_http_request(url, req)
        if type(resp) is dict and 'result' in resp:
            return resp['result']
        else:
            raise Exception(str(resp))

    def create_app_keys(self, app_name='', req_id=1):
        """returns json containing NEW app keys or error info
        @app_name: type = string. name of your application.
        @req_id: type = integer. OPTIONAL request id number (for customer use only)
        """
        url = 'https://api.betfair.com/exchange/account/json-rpc/v1'
        if self.aus: url = 'https://api-au.betfair.com/exchange/account/json-rpc/v1'
        req = {
            'jsonrpc': '2.0',
            'method': 'AccountAPING/v1.0/createDeveloperAppKeys',
            'id': req_id,
            'params': {
                'appName': app_name
            }
        }
        req = json.dumps(req)  # convert dict to json format
        resp = self.send_http_request(url, req)
        if type(resp) is dict and 'result' in resp:
            return resp['result']
        else:
            raise Exception(str(resp))

    def get_app_keys(self, req_id=1):
        """returns json containing app keys
        @req_id: type = integer. OPTIONAL request id number (for customer use only)
        """
        url = 'https://api.betfair.com/exchange/account/json-rpc/v1'
        if self.aus: url = 'https://api-au.betfair.com/exchange/account/json-rpc/v1'
        req = {
            'jsonrpc': '2.0',
            'method': 'AccountAPING/v1.0/getDeveloperAppKeys',
            'id': req_id,
            'params': {}
        }
        req = json.dumps(req)  # convert dict to json format
        resp = self.send_http_request(url, req)
        if type(resp) is dict and 'result' in resp:
            return resp['result']
        else:
            raise Exception(str(resp))

    def get_event_types(self, filters=None, req_id=1):
        """returns json containing list of event types
        @filters: type = dict. request filters.
        @req_id: type = integer. OPTIONAL request id number (for customer use only)
        """
        url = 'https://api.betfair.com/exchange/betting/json-rpc/v1'
        if self.aus: url = 'https://api-au.betfair.com/exchange/betting/json-rpc/v1'
        if not filters: filters = {}
        req = {
            'jsonrpc': '2.0',
            'method': 'SportsAPING/v1.0/listEventTypes',
            'id': req_id,
            'params': {
                'locale': self.locale,
                'filter': filters
            }
        }
        req = json.dumps(req)  # convert dict to json format
        resp = self.send_http_request(url, req)
        if type(resp) is dict and 'result' in resp:
            return resp['result']
        else:
            raise Exception(str(resp))

    def get_events(self, filters=None, req_id=1):
        """returns json containing list of events
        @filters: type = dict. request filters.
        @req_id: type = integer. OPTIONAL request id number (for customer use only)
        """
        url = 'https://api.betfair.com/exchange/betting/json-rpc/v1'
        if self.aus: url = 'https://api-au.betfair.com/exchange/betting/json-rpc/v1'
        if not filters: filters = {}
        req = {
            'jsonrpc': '2.0',
            'method': 'SportsAPING/v1.0/listEvents',
            'id': req_id,
            'params': {
                'locale': self.locale,
                'filter': filters
            }
        }
        req = json.dumps(req)  # convert dict to json format
        resp = self.send_http_request(url, req)
        if type(resp) is dict and 'result' in resp:
            return resp['result']
        else:
            raise Exception(str(resp))

    def get_markets(self, params=None, req_id=1):
        """returns json containing list of markets
        @req_id: type = integer. OPTIONAL request id number (for customer use only)
        @params: type = dict containing keys 'filter', 'marketProjection' and 'maxResults'
        example:
        {
            'filter': {'textQuery': 'Aintree', 'bspOnly': True},
            'marketProjection': ['RUNNER_METADATA', 'RUNNER_DESCRIPTION'],
            'maxResults': 50
        }
        NOTE: above 3 keys MUST be present. leave empty if unused, e.g. 'filter': {}
        """
        url = 'https://api.betfair.com/exchange/betting/json-rpc/v1'
        if self.aus: url = 'https://api-au.betfair.com/exchange/betting/json-rpc/v1'
        params['locale'] = self.locale
        req = {
            'jsonrpc': '2.0',
            'method': 'SportsAPING/v1.0/listMarketCatalogue',
            'id': req_id,
            'params': params
        }
        req = json.dumps(req)  # convert dict to json format
        resp = self.send_http_request(url, req)
        if type(resp) is dict and 'result' in resp:
            return resp['result']
        else:
            raise Exception(str(resp))

    def get_market_books(self, market_ids=None, price_data=None,
                         virtualise=True, req_id=1):
        """returns prices for given market ids (max = 5 per request)
        @market_ids: type = list, elements = market ids (strings). MAX LENGTH = 5 market ids
        @virtualise: type = boolean. whether or not to include virtual prices.
        @price_data: type = list, elements = any of the following strings:
            'SP_AVAILABLE', 'SP_TRADED', 'EX_BEST_OFFERS', 'EX_ALL_OFFERS', 'EX_TRADED'
        @req_id: type = integer. OPTIONAL request id number (for customer use only)
        NOTES:
        1. betfair data_crypto request limit = 5 markets per second
        2. you can call this function AFTER market closes to check results! data_crypto
        is available for 90 days after market closure.
        """
        url = 'https://api.betfair.com/exchange/betting/json-rpc/v1'
        if self.aus: url = 'https://api-au.betfair.com/exchange/betting/json-rpc/v1'
        params = {}
        params['locale'] = self.locale
        params['marketIds'] = market_ids
        if price_data:
            params['priceProjection'] = {'priceData': price_data}
        params['virtualise'] = virtualise
        req = {
            'jsonrpc': '2.0',
            'method': 'SportsAPING/v1.0/listMarketBook',
            'id': req_id,
            'params': params
        }
        req = json.dumps(req)  # convert dict to json format
        resp = self.send_http_request(url, req)
        if type(resp) is dict and 'result' in resp:
            return resp['result']
        else:
            raise Exception(str(resp))

    def place_bets(self, market_id='', bets=None, customer_ref='', req_id=1):
        """place bets on given market id.
        returns list of bet execution reports.
        @market_id: type = string
        @customer_ref: type = string. OPTIONAL request identifier (for customer use only)
        @req_id: type = integer. OPTIONAL request id number (for customer use only)
        @bets: type = list, elements = dict of bet instructions. e.g.
            {
                'selectionId': '237486',
                'handicap': '0',
                'side': 'BACK', # options = 'BACK', or 'LAY'
                'orderType': 'LIMIT', # options = 'LIMIT', 'LIMIT_ON_CLOSE' or 'MARKET_ON_CLOSE'
                'limitOrder': {
                    'size': '2.0', # stake
                    'price': '3.2', # odds
                    'persistenceType': 'LAPSE' # options = 'LAPSE', 'PERSIST' or 'MARKET_ON_CLOSE'
                }
            }
            *** BSP BETS ***
            use 'limitOnCloseOrder' instead of 'limitOrder':
            {
                'liability': '10.0', # maximum risk for this bet
                'price': '3.2' # price limit for 'LIMIT_ON_CLOSE' bets
            }
        """
        url = 'https://api.betfair.com/exchange/betting/json-rpc/v1'
        if self.aus: url = 'https://api-au.betfair.com/exchange/betting/json-rpc/v1'
        params = {}
        params['locale'] = self.locale
        params['marketId'] = market_id
        params['instructions'] = bets
        if customer_ref: params['customerRef'] = customer_ref
        req = {
            'jsonrpc': '2.0',
            'method': 'SportsAPING/v1.0/placeOrders',
            'id': req_id,
            'params': params
        }
        req = json.dumps(req)  # convert dict to json format
        resp = self.send_http_request(url, req)
        if type(resp) is dict and 'result' in resp:
            return resp['result']
        else:
            return resp

    def get_settled_bets(self, group_by='BET', req_id=1, fecha_inicial=dt.datetime(2014, 1, 1),
                         fecha_final=dt.datetime.now()):
        """returns settled bets for given market ids.
        @market_id: type = string
        @group_by: type = string. either 'MARKET' OR 'BET'
            'MARKET' = group response as market total including commission.
                Individual bets are NOT included!
            'BET' = return each individual bet. Commission is NOT included!
        @req_id: type = integer. OPTIONAL request id number (for customer use only)
        NOTES:
        This function only returns info for CLOSED (settled) markets - it is
        recommended that you call get_market_books() first to check market
        status == 'CLOSED'. Note that a CLOSED status does NOT guarantee that
        listClearedOrders will return settled bets - there will sometimes be a
        delay between market closure and the api updating! This is an issue that
        betfair are aware of: https://forum.bdp.betfair.com/showthread.php?t=2436
        To workaround this, you should check 'clearedOrders' in the response - if
        it is empty, save the current time and re-check 15 minutes later. If still
        empty, you can safely assume that you had no matched bets on this market.
        """
        url = 'https://api.betfair.com/exchange/betting/json-rpc/v1'
        if self.aus: url = 'https://api-au.betfair.com/exchange/betting/json-rpc/v1'
        params = {}
        rango = [fecha_inicial, fecha_final]
        params["settledDateRange"] = {"from": min(rango).strftime('%Y-%m-%dT%H:%M:%SZ'),
                                      "to": max(rango).strftime('%Y-%m-%dT%H:%M:%SZ')}

        # params['locale'] = self.locale
        params['betStatus'] = 'SETTLED'  # settled bets only
        params['groupBy'] = group_by
        params['includeItemDescription'] = True
        req = {
            'jsonrpc': '2.0',
            'method': 'SportsAPING/v1.0/listClearedOrders',
            'id': req_id,
            'params': params
        }
        req = json.dumps(req)  # convert dict to json format
        resp = self.send_http_request(url, req)
        if type(resp) is dict and 'result' in resp:
            return resp['result']
        else:
            raise Exception(str(resp))

    def get_market_types(self, filters=None, req_id=1):
        """returns json containing list of market types:
        e.g. 'TOP_GOALSCORER', 'MATCH_ODDS', 'CORRECT_SCORE', etc
        @filters: type = dict. request filters.
        @req_id: type = integer. OPTIONAL request id number (for customer use only)
        """
        url = 'https://api.betfair.com/exchange/betting/json-rpc/v1'
        if self.aus: url = 'https://api-au.betfair.com/exchange/betting/json-rpc/v1'
        if not filters: filters = {}
        req = {
            'jsonrpc': '2.0',
            'method': 'SportsAPING/v1.0/listMarketTypes',
            'id': req_id,
            'params': {
                'locale': self.locale,
                'filter': filters
            }
        }
        req = json.dumps(req)  # convert dict to json format
        resp = self.send_http_request(url, req)
        if type(resp) is dict and 'result' in resp:
            return resp['result']
        else:
            raise Exception(str(resp))

    def __parse_menu_paths(self, data=None, temp_path='', menu_paths=None, ignores=None):
        """recursive function to parse menu paths. used by get_menu_paths()"""
        temp_path += '/' + data['name'].replace('/', '-')  # e.g. Over-Under 2.5 Goals
        if 'children' in data:
            for kid in data['children']:
                self.__parse_menu_paths(kid, temp_path, menu_paths, ignores)
        else:
            # market path - check if working with UK or AUS exchange...
            keep = self.aus
            if data['id'][:2] == '1.': keep = not keep  # invert boolean
            # save market path?
            if keep:
                if ignores:
                    if data['id'] not in ignores:
                        menu_paths[data['id']] = temp_path
                else:
                    menu_paths[data['id']] = temp_path

    def get_menu_paths(self, ignores=None):
        """returns the menu paths for all markets.
        return type = dict. keys = market ids, vals = full menu path string
        @ignores: type = list. OPTIONAL list of market ids to ignore.
        NOTES:
        * this is the menu path as shown on left side of betfair website.
        * the return dict can be used to create a list of market ids by looping
          through the menu paths and searching for specific strings, e.g.
          'Wimbledon 2015', 'Half Time Score', etc. The market ids can then be
          passed to the listMarketCatalogue filter (param 'marketIds') to get
          only those markets.
        * the menu paths are updated every 5 minutes by betfair
        """
        # get menu paths json
        menu_paths = {}  # keys = market ids, vals = menu paths
        url = 'https://api.betfair.com/exchange/betting/rest/v1/en/navigation/menu.json'
        try:
            resp = self.send_http_request(url)
            if type(resp) is dict:
                self.__parse_menu_paths(resp, '', menu_paths, ignores)
                return menu_paths
            else:
                raise Exception(str(resp))
        except:
            # malformed menu from betfair
            return menu_paths  # (empty dict)

    def get_current_bets(self, betIds=None, req_id=1):
        """version simplificada de las lista de ordenes..
        devuelve un json con los betIds que le meto como parametros
        """
        url = 'https://api.betfair.com/exchange/betting/json-rpc/v1'
        if self.aus: url = 'https://api-au.betfair.com/exchange/betting/json-rpc/v1'
        params = {}
        params['betId'] = betIds
        req = {
            'jsonrpc': '2.0',
            'method': 'SportsAPING/v1.0/listCurrentOrders',
            'id': req_id,
            'params': params
        }
        req = json.dumps(req)  # convert dict to json format
        resp = self.send_http_request(url, req)
        if type(resp) is dict and 'result' in resp:
            return resp
        else:
            raise Exception(str(resp))

    def replaceOrders(self, market_id=None, bets=None, req_id=1):
        """version simplificada de las lista de ordenes..
            devuelve un json con los betIds que le meto como parametros
            """
        url = 'https://api.betfair.com/exchange/betting/json-rpc/v1'
        if self.aus: url = 'https://api-au.betfair.com/exchange/betting/json-rpc/v1'
        params = {}
        params['marketId'] = market_id
        params['instructions'] = bets
        req = {
            'jsonrpc': '2.0',
            'method': 'SportsAPING/v1.0/replaceOrders',
            'id': req_id,
            'params': params
        }
        req = json.dumps(req)  # convert dict to json format
        resp = self.send_http_request(url, req)
        if type(resp) is dict and 'result' in resp:
            return resp['result']
        else:
            raise Exception(str(resp))

    def cancelOrders(self, betId=None, market_id=None, req_id=1):
        """cancelo las apuestas que no hayan cumplido las condiciones"""
        url = 'https://api.betfair.com/exchange/betting/json-rpc/v1'
        if self.aus: url = 'https://api-au.betfair.com/exchange/betting/json-rpc/v1'
        params = {}
        params['marketId'] = market_id
        params["instructions"] = [{"betId": betId, "sizeReduction": None}]
        req = {
            'jsonrpc': '2.0',
            'method': 'SportsAPING/v1.0/cancelOrders',
            'id': req_id,
            'params': params

        }
        req = json.dumps(req)  # convert dict to json format
        resp = self.send_http_request(url, req)
        if type(resp) is dict and 'result' in resp:
            return resp['result']
        else:
            raise Exception(str(resp))

    def get_market_profit_loss(self, market_ids=None, req_id=1):
        """simplified version of listMarketProfitAndLoss.
        returns json containing P&L for each market.
        @market_ids: type = list. list of market ids.
        @req_id: type = integer. OPTIONAL request id number (for customer use only)
        """
        url = 'https://api.betfair.com/exchange/betting/json-rpc/v1'
        if self.aus: url = 'https://api-au.betfair.com/exchange/betting/json-rpc/v1'
        req = {
            'jsonrpc': '2.0',
            'method': 'SportsAPING/v1.0/listMarketProfitAndLoss',
            'id': req_id,
            'params': {
                'locale': self.locale,
                'marketIds': market_ids
            }
        }
        req = json.dumps(req)  # convert dict to json format
        resp = self.send_http_request(url, req)
        if type(resp) is dict and 'result' in resp:
            # parse P&L
            positions = {}
            for res in resp['result']:
                market_id = res['marketId']
                if market_id not in positions: positions[market_id] = {}
                for pnl in res['profitAndLosses']:
                    sel_id = pnl['selectionId']
                    if sel_id not in positions[market_id]:
                        pnl.pop('selectionId')
                        positions[market_id][sel_id] = pnl
            return positions
        else:
            raise Exception(str(resp))
