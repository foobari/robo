from lxml import html
import requests
import time
import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas_datareader as web
import numpy as np
import math
import os,glob
import json
from datetime import datetime

import pdb
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

import algo
import graph
import common
import settings
import online

index, money, last_total, best_total = 0, 0, 0, 0


closed_deals = []	

algo.init() 

options = common.check_args(sys.argv)
stocks 	= common.init_stocks(options)
sett 	= settings.init('settings_robo.json')

alg = algo.set_new_params(stocks)

is_last = False

if(stocks[0]['url'] != 'binance_api'):
	while(datetime.now() < datetime.now().replace(hour = 9, minute = 15)):
		print(datetime.now().strftime("%H:%M:%S"), "waiting for Nordnet to open...")
		time.sleep(10)


with open('credentials.json', 'r') as f:
	creds = json.load(f)

if(options['do_graph']):
	graph.init()



# here we go, login
for stock in stocks:
	print datetime.now().strftime("Start %H:%M:%S:"), stock['name'], stock['transaction_type']
	if(stock['transaction_type'] == 'sell_away'):
		print("hard_stop_loss", stock['hard_stop_loss'])
	online.login(stock, creds)

#############################################
# run for one day max in live trading
#
while(not is_last):
	# live data from Nordnet
	try:
		for stock in stocks:
			online.get_stock_values(stock, index)
	except:
		print(datetime.now().strftime("%H:%M:%S Error fetching data"))
		time.sleep(sett['wait_fetching_secs'])
		continue
	
	# store to file
	common.store_stock_values(stocks, index, options)

	# check signals, do transactions
	flip = 0
	for stock in stocks:
		if(stock['url'] != 'binance_api'):
			if(datetime.now() > datetime.now().replace(hour = 20, minute = 50)):
				print("Day end, closing open positions and exit")
				is_last = True
				flip = -1
				reason = 'day_close'
			else:
				stock['no_buy'] = datetime.now() > datetime.now().replace(hour = 20, minute = 00)
				flip, reason = algo.check_signals(stock, index, alg)
		else:
			flip, reason = algo.check_signals(stock, index, alg)	

		if(flip != 0):
			money, last_total = common.do_transaction(stock,
								  flip,
								  reason,
								  money,
								  last_total,
								  closed_deals,
								  alg,
								  index,
								  options)

	# cross check for Nordnet bull/bear
	if(len(stocks) == 2):
		for stock in stocks:
			if(stock['type'] == 'long'):
				cc_long = stock
			elif(stock['type'] == 'short'):
				cc_short = stock

		if(cc_short['active_position'] and cc_long['flip'] == 1):
				money, last_total = common.do_transaction(cc_short,
									-1,
									"cross",
									money,
									last_total,
									closed_deals,
									alg,
									index,
									options)

		if(cc_long['active_position'] and cc_short['flip'] == 1):
				money, last_total = common.do_transaction(cc_long,
									-1,
									"cross",
									money,
									last_total,
									closed_deals,
									alg,
									index,
									options)

	# graph
	if(options['do_graph'] and (index % sett['graph_update_interval'] == 0)):
		graph.draw(stocks)

	# refresh after every 30 ticks / ~5min
	if(((index+1) % 30) == 0):
		for stock in stocks:
			online.refresh(stock)

	# re-login after ~every hour
	if(((index+1) % 300) == 0):
		for stock in stocks:
			online.logout(stock)
			online.login(stock, creds)

	time.sleep(sett['wait_fetching_secs'])
	index = index + 1


#############################################
# and exit
#
common.count_stats(True, stocks, last_total, best_total, closed_deals, alg)
for stock in stocks:
	online.logout(stock)

time.sleep(1)
