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

WAIT_FETCHING_SECS = 10
	

def init_stocks():
	global ax1, ax2

	with open('stocks.json', 'r') as f:
		stocks = json.load(f)

	for stock in stocks:
		stock['valid'] = False
		stock['active_position'] = False
		stock['buy'] = 0
		stock['sell'] = 0
		stock['last_buy'] = 0
		stock['stocks'] = 0
		stock['current_top'] = 0
		stock['hard_stop_loss'] = 0
		stock['dir'] = 0
		stock['trailing_stop_loss'] = 0
		stock['buy_series'] = pd.Series([])
		stock['sell_series'] = pd.Series([])
		stock['sma_series_short'] = pd.Series([])
		stock['sma_series_long'] = pd.Series([])
		stock['cci_series'] = pd.Series([])
		stock['cci_ptyp'] = pd.Series([])
		stock['cci_last'] = 0
		stock['signals_list_sell'] = []
		stock['signals_list_buy'] = []
		stock['browser'] = 0

	return stocks

###################################################################################################
#					prog start						  #
###################################################################################################

PRINT_GRAPH   = False
GRAPH_UPDATE  = 1

file_index = 0
best_total = 0

algo_params = algo.init()

with open('credentials.json', 'r') as f:
	creds = json.load(f)

PRINT_GRAPH = common.check_args(sys.argv)

if(PRINT_GRAPH):
	graph.init()

while(True):
	stocks = init_stocks()
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
			time.sleep(WAIT_FETCHING_SECS)
			continue
		
		# store to file
		common.store_stock_values(stocks, index)

		# check signals, do transactions
		for stock in stocks:
			flip, reason = algo.check_signals(stock, index, algo_params)

			if(flip != 0):
				money, last_total = common.do_transaction(stock,
									  flip,
									  reason,
									  money,
									  last_total,
									  closed_deals,
									  algo_params,
									  index)

		# graph
		if(PRINT_GRAPH and (index % GRAPH_UPDATE == 0)):
			graph.draw(stocks, money_series)

		# re-login after ~every hour
		if(((index+1) % 300) == 0):
			for stock in stocks:
				common.logout(stock)
				common.login(stock, creds)

		time.sleep(WAIT_FETCHING_SECS)		
		index = index + 1

	best_total = common.count_stats(True, stocks, last_total, best_total, closed_deals, algo_params)
