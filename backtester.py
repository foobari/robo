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
from datetime import datetime
from datetime import timedelta

import algo
import graph
import common
import settings
import online

filecount = 0
fileindex = 0

def get_backtest_files(folder_path, file_name):
	global filecount
	files = []

	for file in glob.glob(os.path.join(folder_path, file_name)):
		files.append(file)
		filecount += 1
	return files


def get_backtest_data(file):
	global filecount
	global fileindex
	backtest_data = []
	spread = 1.0025

	with open(file, "rb") as fp:
		for i in fp.readlines():
			tmp = i.replace('(','')
			tmp = tmp.replace(')','')
			tmp = tmp.replace('\n','')
			tmp = tmp.replace(' ','')
			tmp = tmp.split(",")
			try:	
				if(len(tmp) == 4):
					backtest_data.append((float(tmp[0]), float(tmp[1]), float(tmp[2]), float(tmp[3])))
				elif(len(tmp) == 2):
					backtest_data.append((float(tmp[0]), spread * float(tmp[0])))
			except:
				pass

		fp.close()

	entries = len(backtest_data)
	print('file {:<1d}/{:<2d} {:s} ({:d})'.format(fileindex, filecount - 1, file, entries))
	return backtest_data, entries

	
	
###################################################################################################
#					prog start						  #
###################################################################################################
filenames = []
best_total = 0

options = common.check_args(sys.argv)
options['dry_run'] = True

s = settings.init('settings_backtester.json')

techs, algos = algo.init()

stocks = common.init_stocks(options)

algo_params = algo.set_new_params(stocks)

#if(s['randomize']):
#	algo_params = algo.randomize_params()

if(options['do_graph']):
	graph.init()

# get file(s)
filenames = get_backtest_files(s['file_dir'], s['file_name'])
if(len(filenames) == 0):
	print "No input file(s) found"
	quit()


while(True):
	closed_deals = []
	index, money, last_total = 0, 0, 0

	if(fileindex < len(filenames)):
		if(fileindex == 0 and s['optimize']):
			algo_params = algo.optimize_params(s['randomize'])

		backtest_data, entries = get_backtest_data(filenames[fileindex])
		fileindex = fileindex + 1
	else:
		if(s['one_shot']):
			quit()


		fileindex = 0
		best_total = 0
		start_time = time.time()
		continue


	stocks = common.init_stocks(options)

	# Run for one day in backtesting
	while(index < entries):
		# check signals, do transactions (single stocks)
	
		for stock in stocks:
			online.get_stock_values(stock, index, backtest_data)

			if((index == (entries - 1))):
				flip = -1
				reason = 'day_close'
			else:
				flip, reason = algo.check_signals(stock, index, algo_params)

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

		# cross check
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
										algo_params,
										index,
										options)

			if(cc_long['active_position'] and cc_short['flip'] == 1):
					money, last_total = common.do_transaction(cc_long,
										-1,
										"cross",
										money,
										last_total,
										closed_deals,
										algo_params,
										index,
										options)
		

		# graph
		if(options['do_graph'] and (index % s['graph_update_interval'] == 0)):
			graph.draw(stocks)

		index = index + 1

	last_run = fileindex == len(filenames)
	best_total = common.count_stats(last_run, stocks, last_total, best_total, closed_deals, algo_params)

	if(last_run and s['one_shot']):
		print("Pausing...")
		while True:
			time.sleep(1)
