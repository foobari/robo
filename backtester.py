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
import online


def get_backtest_files(folder_path, file_name):
	files = []
	for file in glob.glob(os.path.join(folder_path, file_name)):
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
	print("open backtest file", file, entries)
	return backtest_data, entries

	
	
###################################################################################################
#					prog start						  #
###################################################################################################
filenames = []
file_index, best_total, param_set_index = 0, 0, 0

dry_run, i_file, o_file, do_graph, do_actions = common.check_args(sys.argv)
dry_run = True

s = settings.init('settings_backtester.json')
alg = algo.init()

if(s['cycle_params']):
	alg = algo.set_new_params(alg, 0)
	param_set_index = param_set_index + 1

if(s['randomize']):
	alg = algo.randomize_params(alg)

if(do_graph):
	graph.init()

# get file(s)
filenames = get_backtest_files(s['file_dir'], s['file_name'])

while(True):
	closed_deals = []
	index, money, last_total = 0, 0, 0
	stocks = common.init_stocks(alg, i_file)

	if(file_index < len(filenames)):
		backtest_data, entries = get_backtest_data(filenames[file_index])
		file_index = file_index + 1
	else:
		if(s['one_shot']):
			quit()
		
		if(s['randomize']):
			alg = algo.randomize_params(alg)
		
		if(s['cycle_params']):
			if(param_set_index < len(algo.get_backtest_params())):
				alg = algo.set_new_params(alg, param_set_index)
				param_set_index = param_set_index + 1
			else:
				quit()
		file_index = 0
		best_total = 0
		continue

	# Run for one day in backtesting
	while(index < entries):
		
		# check signals, do transactions
		for stock in stocks:
			online.get_stock_values(stock, index, backtest_data)

			is_last = (index == (entries - 1))
			flip, reason = algo.check_signals(stock, index, alg, is_last, False)

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
		if(do_graph and (index % s['graph_update_interval'] == 0)):
			graph.draw(stocks)

		index = index + 1

	last_run = file_index == len(filenames)
	best_total = common.count_stats(last_run, stocks, last_total, best_total, closed_deals, alg)

	if(last_run and s['one_shot']):
		print("Pausing...")
		while True:
			time.sleep(1)
