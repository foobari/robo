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


###################################################################################################
#					prog start						  #
###################################################################################################

file_index = 0
best_total = 0

a = algo.init()
s = settings.init('settings_robo.json')

with open('credentials.json', 'r') as f:
	creds = json.load(f)

do_graph, do_actions = common.check_args(sys.argv)

if(do_graph):
	graph.init()

while(True):
	stocks = common.init_stocks(a)
	closed_deals = []
	money_series = pd.Series([])
	index = 0
	money = 0
	last_total = 0

	entries = 4320

	# Here we go, login to Nordnet
	for stock in stocks:
		common.login(stock, creds)

	# Run for one day max in live trading
	while(index < entries):
		money_series[index] = money

		# live data from Nordnet
		try:
			for stock in stocks:
				common.get_stock_values_live(stock, index)
		except:
			print("Error fetching data")
			time.sleep(s['wait_fetching_secs'])
			continue
		
		# store to file
		common.store_stock_values(stocks, index)

		# check signals, do transactions
		for stock in stocks:
			is_last = False
			flip, reason = algo.check_signals(stock, index, a, is_last)

			if(flip != 0):
				money, last_total = common.do_transaction(stock,
									  flip,
									  reason,
									  money,
									  last_total,
									  closed_deals,
									  a,
									  index,
									  do_actions)

		# graph
		if(do_graph and (index % s['graph_update_interval'] == 0)):
			graph.draw(stocks, money_series)

		# re-login after ~every hour
		if(((index+1) % 300) == 0):
			for stock in stocks:
				common.logout(stock)
				common.login(stock, creds)

		time.sleep(s['wait_fetching_secs'])
		index = index + 1

	best_total = common.count_stats(True, stocks, last_total, best_total, closed_deals, a)
