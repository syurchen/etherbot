#!/usr/bin/env python
# -*- coding: utf-8 -*-

# MySQL
#from __future__ import print_function
import pymysql

#import for get requests
import requests
import json

import humanize #coma separation on nums

# Imports for Telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ReplyKeyboardMarkup
import telegram.bot
import logging
import sys
import emoji

# for ticker

import txaio
txaio.use_twisted()

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.application.internet import ClientService

from autobahn.wamp.types import ComponentConfig
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner

# Defining globals
_bot_key = '223693868:AAFXWdEXwlcAgIas9pP5gUn-NOJiHTw9Ps0'
_bot = telegram.bot.Bot(_bot_key)

_etherscan_key = '59W93VKBDTSR1V8EQTBGYDWEVZEIYIPHCV'
_db_host = "localhost";
_db_name = "zeon";
_db_user = "root";
_db_pass = "";

mysql = pymysql.connect(host = _db_host, port = 3306, user = _db_user, passwd= _db_pass, db=_db_name)
_db = mysql.cursor()

_alerts = {};
_ticker_events = ["BTC_ZEC", "BTC_ETH", "BTC_XMR", "BTC_REP", "USDT_BTC"] #another on in ticker


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
job_queue = None

#keyboards
keyboard_start = [['/general', '/check', '/alerts'],
                  ['/help']]
keyboard_general = [['/ethprice', '/ethcap'],
                        ['/btcprice', '/btccap'],
                        ['/back']]
keyboard_check = [['/ethbalance', '/btcbalance'],
                        ['/back']]
keyboard_alerts = [['/alertETH', '/alertBTC', '/alertZEC'],
                    ['/alertXMR', '/alertREP'],
                        ['/back']]
_markup = {}
_markup['start'] = ReplyKeyboardMarkup(keyboard_start, one_time_keyboard=False)
_markup['general'] = ReplyKeyboardMarkup(keyboard_general, one_time_keyboard=False)
_markup['check'] = ReplyKeyboardMarkup(keyboard_check, one_time_keyboard=False)
_markup['alerts'] = ReplyKeyboardMarkup(keyboard_alerts, one_time_keyboard=False)

#interactions

def start(bot, update):
    global _markup
    update.message.reply_text(
        "Let's go!",
        reply_markup = _markup['start'])

def alerts(bot, update):
    global _markup
    update.message.reply_text(
        "Let's go!",
        reply_markup = _markup['alerts'])


def general(bot, update):
    global _markup
    update.message.reply_text(
        "Let's go!",
        reply_markup = _markup['general'])

def check(bot, update):
    global _markup
    update.message.reply_text(
        "Let's go!",
        reply_markup = _markup['check'])



def help(bot, update):
    bot.sendMessage(update.message.chat_id, text="/ethprice - Get latest Ether price\n/ethbalance - Get Ether wallet balance\n/ethcap - Get latest Ether capitalization\n" + 
                                                "/btcprice - Get latest Bitcoin price\n/btcbalance - Get Bitcoin wallet balance\n/btccap - Get latest Bitcoin capitalization\n\n"+
                                                "Have any questions or suggestions? Contact us ASAP at opportunitycrypto@gmail.com\n\nCheck out our channel @cryptoportfolio")
'''
def start(bot, update):
    bot.sendMessage(update.message.chat_id, text='Hi, I am CryptoPortfolioBot and I am ready to please your crypto needs.\n\nUse /help for options list')
'''

#alerts

def init_alerts(events, type = 'alert'):
    #returns events of type from db
    global _db
    alerts = {}
    _db.execute("select subs from match_bot_users where subs is not null and subs != ''")
    values = _db.fetchone()
    try:
        for val in values:
            val = json.loads(val)
            try:
                for event in val:
                    if (event['type'] == type) and (event['event'] in events):
                        try:
                           alerts[event['event']].append(event )
                        except (KeyError):
                           alerts[event['event']] = [event]
                        event.pop('event')
            except (KeyError):
                print('key error in init_alerts')
    except (TypeError):
        return {}
    return alerts
            

def register_alert(bot, update, args):
    global _alerts, _ticker_events, _db
    try:
        event = args[0]
        threshold = args[1]
        if event not in _ticker_events:
            bot.sendMessage(update.message.chat_id, text='Oops, I dont work with this event. Try one of those: ' + ', '.join(_ticker_events))
            return;
        user = get_db_user(_db, "telegram_id='%s'" % update.message.from_user.id)
        if not user:
            add_db_user(_db, "telegram_id='%s'" % update.message.from_user.id)
            user = get_db_user(_db, "telegram_id='%s'" % update.message.from_user.id)

        if not add_alert(user, event, threshold):
            return bot.sendMessage(update.message.chat_id, text='You are already subscribed to this event')

        bot.sendMessage(update.message.chat_id, text='You\'ll be notified when %s reaches %s' %(event, threshold))

    except (IndexError, ValueError):
        bot.sendMessage(update.message.chat_id, text='This command needs your steam ID after space. You can obtain it like this http://dl2.joxi.net/drive/2016/07/13/0013/2351/911663/63/e2a5d4a5b9.png')
        return False

#def remove_alert_choose(bot, update):

def add_alert(user, event, threshold, type = 'alert'):
    global _alerts, _db
    alert = generate_sub(user, event, threshold, type, True)
    alert.pop('event')
    try:
        if alert in _alerts[event]:
            return False
        else:
            _alerts[event].append(alert)
    except (KeyError):
        _alerts[event] = [alert]

    subs = generate_sub(user, event, threshold)
    if not subs: # returns 0 if this event exists
        print('Memory and db are async. add_alert')
        return False        
    update_db_user(_db, "id='%s'" % str(user['id']), "subs='%s'" % subs)
    return True

def remove_alert(user, event, threshold, type = 'alert', dynamics = False):
    global _alerts, _db
    print('removing alert')
    alert = generate_sub(user, event, threshold, type, True)
    alert.pop('event')
    print(alert)
    if dynamics != False:
        alert['dynamics'] = dynamics
    try:
        if alert in _alerts[event]:
            _alerts[event].remove(alert)
            print(_alerts)
        else:
            return False            
    except (KeyError):
        print('key error in remove_alert')
    try:
        user['subs']
    except (KeyError):
        _db.execute("select subs from match_bot_users where id = '%s'" % user['id'])
        values = _db.fetchone()
        user['subs'] = values[0]

    subs = generate_sub(user, event, threshold, type)
    if not subs: # returns 0 if this event exists
        subs = ''
    update_db_user(_db, "id='%s'" % str(user['id']), "subs='%s'" % subs)
    return True

def generate_sub(user, event, threshold, type = 'alert', no_json = False):
    new_sub = {'type': type, 'event': event, 'threshold': threshold, 'user_id': user['id'], 'telegram_id': user['telegram_id']}
    if no_json == True:
        return new_sub
    if not user['subs']:
        return json.dumps([new_sub])
    else:
        current_sub = json.loads(user['subs'])
        if new_sub in current_sub:
            return 0
        current_sub.append(new_sub)
        return json.dumps(current_sub)

def send_alert(currency, event, cur_value):
    global _bot
    print('sending alert to %s' % event['telegram_id'])
    message = "Hello! %s has reached %s. It's %s now!" % (currency, event['threshold'], cur_value)
    _bot.sendMessage(event['telegram_id'], message)

#leftovers

def dota_LM(bot, update):
    global dota_history, _db
    try:
        user = get_db_user(_db, "telegram_id='%s'" % update.message.from_user.id)
        last_match = dota_history.matches(account_id = user['steam_id'], matches_requested = 1)
        bot.sendMessage(update.message.chat_id, text = 'http://www.dotabuff.com/matches/' + str(last_match[0].match_id))
    except:
        bot.sendMessage(update.message.chat_id, text = "Something went wrong. Did you /dota_register ?")

#error

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

#currencies

def btc_balance(bot, update, args):
    try:
        btc_id = args[0]
        # todo add db storage
        balance = requests.get('https://blockchain.info/address/' + btc_id + '?format=json')
        bot.sendMessage(update.message.chat_id, text = 'Your balance is: ' + parse_blockchain_info(balance) + emoji.emojize(' :b: ', use_aliases=True))
    except:
        bot.sendMessage(update.message.chat_id, text = "Something went wrong. Did you /dota_register ?")

def parse_blockchain_info(balance):
    balance = json.loads(balance.text)
    balance = int(balance['final_balance'])
    return str(balance / (10 ** 8))

def eth_balance(bot, update, args):
    try:
        ether_id = args[0]
        # todo add db storage
        data = {
            'module': 'account',
            'action': 'balance',
            'address': ether_id,
            'tag': 'latest',
            'apikey': _etherscan_key
        }

        balance = requests.get('https://api.etherscan.io/api/', params=data)
        bot.sendMessage(update.message.chat_id, text = 'Your balance is: ' + parse_etherscan(balance) + ' Ether')
    except:
        bot.sendMessage(update.message.chat_id, text = "Send me wallet ID you'ld like to leard balance of")

def echo(bot, update):
    update.message.reply_text(update.message.text)

def parse_etherscan(balance):
    balance = json.loads(balance.text)
    balance = int(balance['result'])
    return str(balance / (10 ** 18))

def btc_price(bot, update):
    try:
        data = requests.get('https://api.coinmarketcap.com/v1/ticker/bitcoin')
        data = json.loads(data.text)
        price_usd = data[0]['price_usd']
        price_change = data[0]['percent_change_24h']
        if price_change.find('-') < 0:
            emote = ' :arrow_upper_right: '
        else:
            emote = ' :arrow_lower_right: '
        bot.sendMessage(update.message.chat_id, text = emoji.emojize("$" + str(price_usd) + emote + price_change + '%', use_aliases=True))
    except:
        bot.sendMessage(update.message.chat_id, text = "Something went wrong. Did you /dota_register ?")
 
def btc_cap(bot, update):
    try:
        data = requests.get('https://api.coinmarketcap.com/v1/ticker/bitcoin')
        data = json.loads(data.text)
        cap_usd = data[0]['market_cap_usd']
        if cap_usd [-2:] == '.0':
            cap_usd = cap_usd[:-2]
        cap_usd = humanize.intcomma(cap_usd)
        bot.sendMessage(update.message.chat_id, text = emoji.emojize("$" + str(cap_usd), use_aliases=True))
    except:
        bot.sendMessage(update.message.chat_id, text = "Something went wrong. Did you /dota_register ?")


def eth_cap(bot, update):
    try:
        data = requests.get('https://api.coinmarketcap.com/v1/ticker/ethereum')
        data = json.loads(data.text)
        cap_usd = data[0]['market_cap_usd']
        if cap_usd [-2:] == '.0':
            cap_usd = cap_usd[:-2]
        cap_usd = humanize.intcomma(cap_usd)
        bot.sendMessage(update.message.chat_id, text = emoji.emojize("$" + str(cap_usd), use_aliases=True))
    except:
        bot.sendMessage(update.message.chat_id, text = "Something went wrong. Did you /dota_register ?")


def eth_price(bot, update):
    try:
        data = requests.get('https://api.coinmarketcap.com/v1/ticker/ethereum')
        data = json.loads(data.text)
        price_usd = data[0]['price_usd']
        price_btc = data[0]['price_btc']

        price_change = data[0]['percent_change_24h']
        if price_change.find('-') < 0:
            emote = ' :arrow_upper_right: '
        else:
            emote = ' :arrow_lower_right: '
            
        bot.sendMessage(update.message.chat_id, text = emoji.emojize("$" + str(price_usd) + ' :b: ' + price_btc + emote + price_change + '%', use_aliases=True))
    except:
        bot.sendMessage(update.message.chat_id, text = "Something went wrong. Did you /dota_register ?")

# Database functions
def get_db_user(db, *args):
# Note that values should be in single quotes
    query = ' and '.join(args)

    db.execute("show columns from match_bot_users")
    columns = db.fetchall()
    db.execute("select * from match_bot_users where %s order by id desc limit 1" % query)
    values = db.fetchone()
    result = {}
    for column, value in zip(columns, values):
        result[column[0]] = value
    return result

def add_db_user(db, *args):
    columns = []
    values = []
    for arg in args:
        temp = arg.split('=')
        columns.append(temp[0])
        values.append(temp[1])
    values = ','.join(values)
    columns = ','.join(columns)
    db.execute("insert into match_bot_users (%s) values (%s)" % (columns, values))

def update_db_user(db, query, *args):
    update = ', '.join(args)
    db.execute("show columns from match_bot_users")
    columns = db.fetchall()
    db.execute("update match_bot_users set %s where %s" % (update, query))

# ticker WART
def ticker_event_handler(event):
    global _alerts
    try:
        this_alert = []
        for alert in _alerts[event[1]]:
            print('handling alert:')
            print(alert)
            if alert['type'] == 'alert':
                this_alert.append(alert)
        if len(this_alert) < 1:
            return False
    except (KeyError):
        #there is no event for this ticker
        print('no event')
        return False
    for alert in this_alert:
        try:
            if alert['dynamics'] == '+' and float(event[2]) >= float(alert['threshold']): # change < to >
                print ('alert!!! %s %f %f' % (alert['dynamics'], float(event[2]), float(alert['threshold'])))
                send_alert(event[1], alert, event[2])
                try:
                    remove_alert({'id': alert['user_id'], 'telegram_id': alert['telegram_id']}, event[1], alert['threshold'], alert['type'], alert['dynamics'])
                except (ValueError):
                    print('value error')
                    
            if alert['dynamics'] == '-' and float(event[2]) <= float(alert['threshold']):
                print ('alert!!! %s %f %f' % (alert['dynamics'], float(event[2]), float(alert['threshold'])))
                send_alert(event[1], alert, event[2])
                try:
                    remove_alert({'id': alert['user_id'], 'telegram_id': alert['telegram_id']}, event[1], alert['threshold'], alert['type'], alert['dynamics'])
                except (ValueError):
                    print('value error')

        except (KeyError):
            print('no dynamics')
            _alerts[event[1]].remove(alert)
            if float(event[2]) > float(alert['threshold']):
                alert['dynamics'] = '-'
            if float(event[2]) < float(alert['threshold']):
                alert['dynamics'] = '+'
            _alerts[event[1]].append(alert)


class MyAppSession(ApplicationSession):

    def __init__(self, config):
        ApplicationSession.__init__(self, config)
        self._countdown = 5

    def onConnect(self):
        self.log.info('transport connected')

        self.join(self.config.realm)

    def onChallenge(self, challenge):
        self.log.info('authentication challenge received')


    def onJoin(self, details):
        #self.log.info('session joined: {}'.format(details))
        sub = self.subscribe(self.on_event, u'ticker')

    def onLeave(self, details):
        self.log.info('session left: {}'.format(details))
        self.disconnect()

    def onDisconnect(self):
        self.log.info('transport disconnected')
        self._countdown -= 1
        if self._countdown <= 0:
            try:
                reactor.stop()
            except ReactorNotRunning:
                pass

    def on_event(*args):
        monitor_events = ["BTC_ZEC", "BTC_ETH", "BTC_XMR", "BTC_REP", "USDT_BTC"]
        if args[1] in monitor_events:
            ticker_event_handler(args)

def start_ticker():
    session = MyAppSession(ComponentConfig(u'realm1', {}))
    runner = ApplicationRunner(u'wss://api.poloniex.com:443', u'realm1')
    runner.run(session, auto_reconnect=True)




def main():
    global job_queue, _to_display, _db, _alerts, _bot_key

    #updater = Updater('283008904:AAHhB7m8eS93R5nNr2HBxx5ervfL2IqDZWE')
    updater = Updater(_bot_key)
    job_queue = updater.job_queue

    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    _alerts = init_alerts(_ticker_events, 'alert')
    # On different commands - answer in Telegram
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("start", start))

    dp.add_handler(CommandHandler("back", start))
    dp.add_handler(CommandHandler("general", general))
    dp.add_handler(CommandHandler("check", check))
    dp.add_handler(CommandHandler("alerts", alerts))

    dp.add_handler(CommandHandler("ethprice", eth_price))
    dp.add_handler(CommandHandler("ethbalance", eth_balance, pass_args=True))
    dp.add_handler(CommandHandler("ethcap", eth_cap))

    dp.add_handler(CommandHandler("btcprice", btc_price))
    dp.add_handler(CommandHandler("btcbalance", btc_balance, pass_args=True))
    dp.add_handler(CommandHandler("btccap", btc_cap))
    
    dp.add_handler(CommandHandler("alert", register_alert, pass_args=True))
    #{'telegram_id': '76516332', 'dynamics': '-', 'type': 'alert', 'threshold': '123', 'user_id': 13}
    # Log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Block until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    
    #start_ticker()

    updater.idle()


if __name__ == '__main__':
    main()
