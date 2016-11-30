#!/usr/bin/env python
# -*- coding: utf-8 -*-

# MySQL
#from __future__ import print_function
import pymysql

_etherscan_key = '59W93VKBDTSR1V8EQTBGYDWEVZEIYIPHCV'

_db_host = "localhost";
_db_name = "zeon";
_db_user = "root";
_db_pass = "";

mysql = pymysql.connect(host = _db_host, port = 3306, user = _db_user, passwd= _db_pass, db=_db_name)
_db = mysql.cursor()


#import for get requests
import requests
import json

import humanize #coma separation on nums

# Imports for Telegram
from telegram.ext import Updater, CommandHandler
import logging
import sys
import emoji

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
job_queue = None

def help(bot, update):
    bot.sendMessage(update.message.chat_id, text="/ethprice - Get latest Ether price\n/ethbalance - Get Ether wallet balance\n/ethcap - Get latest Ether capitalization\n" + 
                                                "/btcprice - Get latest Bitcoin price\n/btcbalance - Get Bitcoin wallet balance\n/btccap - Get latest Bitcoin capitalization\n\n"+
                                                "Have any questions or suggestions? Contact us ASAP at opportunitycrypto@gmail.com\n\nCheck out our channel @cryptoportfolio")

def start(bot, update):
    bot.sendMessage(update.message.chat_id, text='Hi, I am CryptoPortfolioBot and I am ready to please your crypto needs.\n\nUse /help for options list')

def dota_register(bot, update, args):
    global dota_history, steam_api_key, _db
    try:
        steam_id = args[0]
        vanity_id = ResolveVanityUrl(steam_api_key).id(steam_id)
        if (vanity_id):
            add_db_user(_db, "telegram_id='%s'" % update.message.from_user.id, "steam_id='%s'" % vanity_id)
            bot.sendMessage(update.message.chat_id, text='You have been registed. Try /dota_LM')
        else:
            bot.sendMessage(update.message.chat_id, text='This steam ID doesn\'t seem valid')

    except (IndexError, ValueError):
        bot.sendMessage(update.message.chat_id, text='This command needs your steam ID after space. You can obtain it like this http://dl2.joxi.net/drive/2016/07/13/0013/2351/911663/63/e2a5d4a5b9.png')
        return False

def dota_LM(bot, update):
    global dota_history, _db
    try:
        user = get_db_user(_db, "telegram_id='%s'" % update.message.from_user.id)
        last_match = dota_history.matches(account_id = user['steam_id'], matches_requested = 1)
        bot.sendMessage(update.message.chat_id, text = 'http://www.dotabuff.com/matches/' + str(last_match[0].match_id))
    except:
        bot.sendMessage(update.message.chat_id, text = "Something went wrong. Did you /dota_register ?")

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

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
        bot.sendMessage(update.message.chat_id, text = "Something went wrong. Did you /dota_register ?")

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

def main():
    global job_queue, _to_display, _db

    updater = Updater('283008904:AAHhB7m8eS93R5nNr2HBxx5ervfL2IqDZWE')
    job_queue = updater.job_queue

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # On different commands - answer in Telegram
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("ethprice", eth_price))
    dp.add_handler(CommandHandler("ethbalance", eth_balance, pass_args=True))
    dp.add_handler(CommandHandler("ethcap", eth_cap))
    dp.add_handler(CommandHandler("btcprice", btc_price))
    dp.add_handler(CommandHandler("btcbalance", btc_balance, pass_args=True))
    dp.add_handler(CommandHandler("btccap", btc_cap))

    # Log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Block until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
