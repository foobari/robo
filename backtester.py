from lxml import html
import requests
import time
import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas_datareader as web
import numpy as np
import os,glob
import json 
import pdb

import algo
import graph
import common


FIXED_STOCK_AMOUNT = True # True -> use BUY_STOCKS, False -> use MONEY_PER_TRANSACTION
BUY_STOCKS = 100
MONEY_PER_TRANSACTION = 1000


def get_backtest_files(folder_path):
	files = []
	for file in glob.glob(os.path.join(folder_path, '*')):
		files.append(file)

	return files

def get_backtest_data(file):
	backtest_data = []
	with open(file, "rb") as fp:
		for i in fp.readlines():
			tmp = i.replace('(','')
			tmp = tmp.replace(')','')
			tmp = tmp.replace('\n','')
			tmp = tmp.replace(' ','')
			tmp = tmp.split(",")
			try:
				backtest_data.append((float(tmp[0]), float(tmp[1]), float(tmp[2]), float(tmp[3])))
			except:
				pass
		fp.close()

	entries = len(backtest_data)
	print("read", file, entries)
	return backtest_data, entries

	
	
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
RANDOMIZE  = False
SET_PARAMS = False   	# True -> usebacktest_params[], False -> defaults/random
ONE_SHOT   = False	# True -> run through input file(s) only once

PRINT_GRAPH   = False
GRAPH_UPDATE  = 40

file_index = 0
best_total = 0

param_set_index = 0
backtest_params = algo.get_backtest_params()
param_set_len = len(backtest_params)

algo_params = algo.init()

if(SET_PARAMS):
	algo.set_new_params(algo_params, 0)
	param_set_index = param_set_index + 1

if(RANDOMIZE):
	algo.randomize_params(algo_params)

if(PRINT_GRAPH):
	graph.init()

# get all files in dir
filenames = get_backtest_files('/home/foobari/src/robo/backtest/')

# only one file
#filenames.append('/home/foobari/src/robo/backtest/data_18122020_x15.dat')


while(True):
	stocks = init_stocks()
	closed_deals = []
	money_series = pd.Series([])
	index = 0
	money = 0
	last_total = 0

	if(file_index < len(filenames)):
		backtest_data, entries = get_backtest_data(filenames[file_index])
		file_index = file_index + 1
	else:
		if(ONE_SHOT):
			quit()
		
		if(RANDOMIZE):
			algo.randomize_params(algo_params)
		
		if(SET_PARAMS):
			if(param_set_index < param_set_len):
				algo.set_new_params(algo_params, param_set_index)
				param_set_index = param_set_index + 1
			else:
				quit()
		file_index = 0
		best_total = 0
		continue

	# Run for one day in backtesting
	while(index < entries):
		money_series[index] = money

		# data from backtest data from files
		for stock in stocks:
			common.get_stock_values_backtest(stock, index, backtest_data)

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

		index = index + 1

	last_run = file_index == len(filenames)
	best_total = common.count_stats(last_run, stocks, last_total, best_total, closed_deals, algo_params)

	if(last_run and ONE_SHOT):
		print("Pausing...")
		while True:
			time.sleep(1)
