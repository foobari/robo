from lxml import html
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import numpy as np
import math
import time
import json
import pandas as pd
import getopt
import sys
from datetime import datetime

import settings
import online

g_closed_deals = []
stats = {}
stats['sharpe'] = 0
stats['profitability'] = 0
stats['profit_factor'] = 0

def init_stocks(algo_params, file):
	print("open stocks file", file)
	with open(file, 'r') as f:
		stocks = json.load(f)

	for stock in stocks:
		stock['valid'] = False
		stock['buy'] = 0
		stock['sell'] = 0
		stock['current_top'] = 0
		stock['dir'] = 0
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
		if(stock['active_position'] and (stock['transaction_type'] == 'sell_away')):
			stock['trailing_stop_loss'] = ((1 + algo_params['trailing'] * stock['leverage'] / 100) * stock['last_buy'])
			print("MODE: sell_away", "buy", stock['last_buy'], "hard_stop_loss", stock['hard_stop_loss'], stock['stocks'])
		else:
			stock['hard_stop_loss'] = 0
			stock['trailing_stop_loss'] = 0

	return stocks

def calc_stats(closed_deals):
	if(len(closed_deals) > 0):
		if(np.std(closed_deals) != 0):
			stats['sharpe'] = math.sqrt(len(closed_deals)) * np.mean(closed_deals) / np.std(closed_deals)
		else:
			stats['sharpe'] = 0

		profits = [i for i in closed_deals if i >= 0]
		losses  = [i for i in closed_deals if i < 0]
		profits_sum = (sum(profits))
		losses_sum = -(sum(losses))
		stats['profitability'] = float(len(profits) / float(len(closed_deals)))

		if(losses_sum != 0):
			stats['profit_factor'] = profits_sum/losses_sum
		else:
			stats['profit_factor'] = 100
	else:
		stats['sharpe']        = 0
		stats['profit_factor'] = 0
		stats['profitability'] = 0

	return stats

def count_stats(final, stocks, last_total, best_total, closed_deals, algo_params):
	global g_closed_deals
	global stats

	g_closed_deals.extend(closed_deals)

	stats = calc_stats(closed_deals)

	best_total = best_total + last_total

	print(round(last_total, 2), len(closed_deals), round(stats['sharpe'], 2), round(stats['profitability'], 2), round(stats['profit_factor'], 2))

	if(final):
		stats = calc_stats(g_closed_deals)
		print("---------------------------")
		if(stats['sharpe'] > 1.5):
			print("TG:", round(best_total, 2), len(g_closed_deals), round(stats['sharpe'], 2), round(stats['profitability'], 2), round(stats['profit_factor'], 2), algo_params)
		else:
			print("T: ", round(best_total, 2), len(g_closed_deals), round(stats['sharpe'], 2), round(stats['profitability'], 2), round(stats['profit_factor'], 2), algo_params)
		print
		del g_closed_deals[:]
		first_time = True

	return best_total


def do_transaction(stock, flip, reason, money, last_total, closed_deals, algo_params, index, info, dry_run):
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
		
		s = settings.get_settings()
		if(s['use_fixed_stock_amount']):
			stock['stocks'] = s['stock_amount_to_buy']
		else:
			stock['stocks'] = stock['transaction_size']
		
		if(info):
			print(datetime.now().strftime("%H:%M:%S"), "ACTION: BUY ", stock['name'], stock['stocks'], stock['last_buy'], reason)

		if(not dry_run):
			online.execute_buy_order_online(stock)

	# sell
	if(stock['active_position'] and (flip == -1)):
		money = money + ((buy - stock['last_buy']) * stock['stocks'])
		last_total = money
		closed_deals.append((buy - stock['last_buy']) * stock['stocks'])
		stock['current_top'] = 0
		stock['active_position'] = False
		stock['signals_list_sell'].append((index, float(stock['buy_series'][-1:])))
		if(info):
			print(datetime.now().strftime("%H:%M:%S"), "ACTION: SELL", stock['name'], stock['stocks'], buy, reason, "result", round(float(closed_deals[-1]), 2) , "total", round(last_total, 2))
		
		if(not dry_run):
			online.execute_sell_order_online(stock)

		stock['stocks'] = 0

		if(stock['transaction_type'] == 'sell_away'):
			print("sell_away completed, exit")
			online.logout(stock)
			quit()

	return money, last_total


def store_stock_values(stocks, index, file):
	do_write = True
	for stock in stocks:
		if(stock['store_to_file'] == False):
			do_write = False
		if(stock['type'] == 'long'):
			buy_long  = stock['buy_series'][index]
			sell_long = stock['sell_series'][index]
		if(stock['type'] == 'short'):
			buy_short  = stock['buy_series'][index]
			sell_short = stock['sell_series'][index]

	# store
	if(do_write):
		f = open(file,"a+")
		f.write(str((buy_long, sell_long, buy_short, sell_short)) + '\n')
		f.close()



def check_args(argv):
	inputfile = ''
	outputfile = 'guru99.txt'
	do_graph = False
	do_actions = False
	dry_run = False

	try:
		opts, args = getopt.getopt(argv[1:],"hgdai:o:", ["dry-run"])
	except getopt.GetoptError:
		print 'test.py -i <inputfile> -o <outputfile>'
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print argv[0], '-i <inputfile> -o <outputfile>'
			sys.exit()
		elif opt in ("-i"):
			inputfile = arg
		elif opt in ("-o"):
			outputfile = arg
		elif opt in ("-g"):
			do_graph = True
		elif opt in ("-a"):
			do_actions = True
		elif opt in ("-d", "--dry-run"):
			dry_run = True

	if(inputfile == ''):
			print argv[0], '-i <inputfile> -o <outputfile>'
			sys.exit()

	return dry_run, inputfile, outputfile, do_graph, do_actions
