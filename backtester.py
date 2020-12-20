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

import algo
import graph


FIXED_STOCK_AMOUNT = True # True -> use BUY_STOCKS, False -> use MONEY_PER_TRANSACTION
BUY_STOCKS = 100
MONEY_PER_TRANSACTION = 1000


def get_stock_values(stock, index):
	global backtest_data

	stock['valid'] = True

	# Backtest data from stored files
	i = 0
	for stock in stocks:
		stock['buy_series'][index] = backtest_data[index][i]
		stock['sell_series'][index] = backtest_data[index][i + 1] 
		i = i + 2
	
	# sanity checks
	if((stock['buy_series'][index] == 0)):
		print(stock['name'], "buy read zero, copy last")
		stock['valid'] = False
		if(index > 0):
			stock['buy_series'][index]  = stock['buy_series'][index - 1]
	if((stock['sell_series'][index] == 0)):
		stock['valid'] = False
		print(stock['name'], "sell read zero, copy last")
		if(index > 0):
			stock['sell_series'][index] = stock['sell_series'][index - 1]
	if((stock['sell_series'][index] - stock['buy_series'][index]) > stock['spread']):
		stock['valid'] = False
		if(index > 0):
			print(stock['name'], "spread too big, copy last")
			stock['buy_series'][index]  = stock['buy_series'][index - 1]
			stock['sell_series'][index] = stock['sell_series'][index - 1]

def do_transaction(stock, flip, reason):
	global money
	global last_total
	global closed_deals
	global algo_params

	buy  = float(stock['buy_series'][-1:])
	sell = float(stock['sell_series'][-1:])

	# buy
	if((not stock['active_position']) and (flip == 1)):
		stock['active_position'] = True
		stock['current_top']        = sell
		stock['last_buy']           = sell
		stock['hard_stop_loss']	    = ((1 + algo_params['hard']     * stock['leverage'] / 100) * sell)
		stock['trailing_stop_loss'] = ((1 + algo_params['trailing'] * stock['leverage'] / 100) * sell)
		stock['signals_list_buy'].append((index, float(stock['sell_series'][-1:])))
		
		if(FIXED_STOCK_AMOUNT):
			stock['stocks'] = BUY_STOCKS
		else:
			stock['stocks'] = int(MONEY_PER_TRANSACTION / sell)
		
		if(PRINT_ACTIONS):
			print("ACTION: BUY ", stock['name'], stock['stocks'], stock['last_buy'])

		return

	# sell
	if(stock['active_position'] and (flip == -1)):
		money = money + ((buy - stock['last_buy']) * stock['stocks'])
		last_total = money
		closed_deals.append((buy - stock['last_buy']) * stock['stocks'])
		stock['current_top'] = 0
		stock['active_position'] = False
		stock['signals_list_sell'].append((index, float(stock['buy_series'][-1:])))
		if(PRINT_ACTIONS):
			print("ACTION: SELL", stock['name'], stock['stocks'], buy, reason, "result", round(float(closed_deals[-1]), 2) , "total", round(last_total, 2))

		stock['stocks'] = 0
		return


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


def count_stats(final):
	global last_total
	global best_total
	global closed_deals
	global algo_params

	unclosed_deals = 0
	pending_money  = 0

	for stock in stocks:
		if(stock['active_position']):
			unclosed_deals = unclosed_deals + 1
			closing_sell = ((float(stock['buy_series'][-1:]) - stock['last_buy']) * stock['stocks'])
			closed_deals.append(closing_sell)
			last_total = last_total + closing_sell
			
	if(np.std(closed_deals) != 0):
		sharpe = math.sqrt(len(closed_deals)) * np.mean(closed_deals) / np.std(closed_deals)
	else:
		sharpe = 0
	
	profits = [i for i in closed_deals if i >= 0]
	losses  = [i for i in closed_deals if i < 0]
	profit_sum = (sum(profits))
	losses_sum = -(sum(losses))
	profitability = 0
	
	if(len(closed_deals) > 0):
		profitability = float(len(profits) / float(len(closed_deals)))
	if(losses_sum > 0):
		profit_factor = profit_sum/losses_sum
	else:
		profit_factor = 100
	
	best_total = best_total + last_total
	

	print("profit", round(last_total, 2), "algo closed", len(closed_deals) - unclosed_deals, "force closed", unclosed_deals, "metrics", round(sharpe, 2), round(profitability, 2), round(profit_factor, 2))

	if(final):
		print("total", round(best_total, 2), algo_params)
		print
	
	
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
RANDOMIZE  = True
SET_PARAMS = False   	# True -> usebacktest_params[], False -> defaults/random
ONE_SHOT   = False	# True -> run through input file(s) only once

PRINT_ACTIONS = False
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

		# "Live" data from backtest data from files
		try:
			for stock in stocks:
				get_stock_values(stock, index)	
		except:
			print("Error fetching data")
			time.sleep(1)
			continue
		
		# check signals, do transactions
		for stock in stocks:
			flip, reason = algo.check_signals(stock, index, algo_params)
			do_transaction(stock, flip, reason)

		# graph
		if(PRINT_GRAPH and (index % GRAPH_UPDATE == 0)):
			graph.draw(stocks, money_series)

		index = index + 1

	last_run = file_index == len(filenames)
	count_stats(last_run)

	if(last_run and ONE_SHOT):
		print("Pausing...")
		while True:
			time.sleep(1)

		