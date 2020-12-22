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
import settings


def get_backtest_files(folder_path, file_name):
	files = []
	for file in glob.glob(os.path.join(folder_path, file_name)):
		print file
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

	
	
###################################################################################################
#					prog start						  #
###################################################################################################
filenames = []
file_index = 0
best_total = 0

param_set_index = 0
backtest_params = algo.get_backtest_params()
param_set_len = len(backtest_params)

a = algo.init()
s = settings.init('settings_backtester.json')

do_graph, do_actions = common.check_args(sys.argv)

if(s['set_params']):
	a = algo.set_new_params(a, 0)
	param_set_index = param_set_index + 1

if(s['randomize']):
	a = algo.randomize_params(a)

if(do_graph):
	graph.init()

# get file(s)
filenames = get_backtest_files(s['file_dir'], s['file_name'])

while(True):
	stocks = common.init_stocks(a)
	closed_deals = []
	money_series = pd.Series([])
	index = 0
	money = 0
	last_total = 0

	if(file_index < len(filenames)):
		backtest_data, entries = get_backtest_data(filenames[file_index])
		file_index = file_index + 1
	else:
		if(s['one_shot']):
			quit()
		
		if(s['randomize']):
			a = algo.randomize_params(a)
		
		if(s['set_params']):
			if(param_set_index < param_set_len):
				a = algo.set_new_params(a, param_set_index)
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
			is_last = (index == (entries - 1))
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

		index = index + 1

	last_run = file_index == len(filenames)
	best_total = common.count_stats(last_run, stocks, last_total, best_total, closed_deals, a)

	if(last_run and s['one_shot']):
		print("Pausing...")
		while True:
			time.sleep(1)
