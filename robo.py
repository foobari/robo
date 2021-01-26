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
 
dry_run, i_file, o_file, do_graph, do_actions = common.check_args(sys.argv)

alg  	= algo.init()
print alg
sett 	= settings.init('settings_robo.json')
stocks 	= common.init_stocks(alg, i_file)
is_last = False

for stock in stocks:
	print(stock['name'], stock['url'], stock['transaction_type'])

while(datetime.now() < datetime.now().replace(hour = 9, minute = 15)):
	print(datetime.now().strftime("%H:%M:%S"), "waiting for Nordnet to open...")
	time.sleep(10)


with open('credentials.json', 'r') as f:
	creds = json.load(f)

if(do_graph):
	graph.init()

# here we go, login to Nordnet
for stock in stocks:
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
		print("Error fetching data")
		time.sleep(sett['wait_fetching_secs'])
		continue
	
	# store to file
	common.store_stock_values(stocks, index, o_file)

	# check signals, do transactions
	for stock in stocks:
		if(datetime.now() > datetime.now().replace(hour = 20, minute = 50)):
			is_last = True
			flip = -1
			reason = 'day_close'
		else:
			stock['no_buy']  = datetime.now() > datetime.now().replace(hour = 20, minute = 00)
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
								  do_actions,
								  dry_run)
	# graph
	if(do_graph and (index % sett['graph_update_interval'] == 0)):
		graph.draw(stocks)

	# refresh after every 30 ticks / ~5min
	if(((index+1) % 30) == 0):
		for stock in stocks:
			print("refresh", stock['name'])
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
