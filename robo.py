from lxml import html
import requests
import time
import sys
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import math
import os,glob
import json
from datetime import datetime

import pdb

import algo
import graph
import common
import settings
import online

index, money, last_total, best_total = 0, 0, 0, 0
is_last = False

closed_deals = []	

techs, algos = algo.init()

options = common.check_args(sys.argv)
stocks 	= common.init_stocks(options)
sett 	= settings.init('settings_robo.json')

algo_params = algo.set_new_params(stocks)

with open('credentials.json', 'r') as f:
	creds = json.load(f)

if(options['do_graph']):
	graph.init()


# here we go, login
for stock in stocks:
	print(datetime.now().strftime("start %H:%M:%S:"), stock['name'], stock['transaction_type'])
	if(stock['buy_full_money'] == True):
		print("transaction_money", stock['transaction_money'])
	else:
		print("transaction_size", stock['transaction_size'])
	if(stock['transaction_type'] == 'sell_away'):
		print("target", stock['target'])
		print("last_buy", stock['last_buy'])

	print("priming...")
	online.login(stock, creds)

# run for one day max in live trading
while(not is_last):
	# live data from Nordnet/Binance
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
		flip, reason = algo.check_signals(stock, index, algo_params, True)
	
		if(flip != 0):
			money, last_total = common.do_transaction(stock,
								  flip,
								  reason,
								  money,
								  last_total,
								  closed_deals,
								  algo_params,
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
common.count_stats(True, stocks, last_total, best_total, closed_deals, algo_params, entries)
for stock in stocks:
	online.logout(stock)

time.sleep(1)
