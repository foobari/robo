# -*- coding: iso-8859-15 -*-
from lxml import html
#from selenium import webdriver
#from selenium.webdriver.common.by import By
#from selenium.webdriver.support.ui import WebDriverWait
#from selenium.webdriver.support import expected_conditions as EC
#from selenium.webdriver.support.ui import Select
import requests
import numpy as np
import math
import random
import time
import json
import getopt
import sys
from datetime import datetime
import settings
import online
import graph

optimizer_result_best_stat = {}
optimizer_result_best_algo = {}

start_time = time.time()

#result parameter to optimize to
#optimizer_stat_to_optimize = 'result_eur'
optimizer_stat_to_optimize = 'magic'
previous_best_value = -10000

g_closed_deals = []

stats = {}
stats['magic'] = 0
stats['sharpe'] = 0
stats['days'] = 0
stats['profitability'] = 0
stats['profit_factor'] = 0
stats['result_eur'] = 0
stats['result_per'] = 0

options = {}
options['inputfile']   = ''
options['outputfile']  = 'guru99x.txt'
options['do_graph']    = False
options['do_actions']  = False
options['dry_run']     = False
options['do_optimize'] = False

param_names = [ 'name',
	        'cci_up',
		'cci_down',
		'target',
		'hard',
		'trailing',
		'cci_window',
		'sma_len',
		'rsi_len',
		'rsi_lim',
		'cci_big',
		'rsi_big']

def init_stocks(options):
	#print("open stocks file", options['inputfile'])
	with open(options['inputfile'], 'r') as f:
		stocks = json.load(f)

	for stock in stocks:
		stock['valid'] = False
		stock['buy'] = 0
		stock['sell'] = 0
		stock['current_top'] = 0
		stock['dir'] = 0
		stock['trigger'] = 0
		stock['guard'] = 0
		stock['buy_series'] = []
		stock['sell_series'] = []
		stock['sma_series_short'] = []
		stock['sma_series_long'] = []
		stock['cci_series'] = []
		stock['rsi_series'] = []
		stock['cci_ptyp'] = []
		stock['hurst'] = []
		stock['win_high'] = []
		stock['win_low'] = []		
		stock['hh'] = []
		stock['hh_sma'] = []
		stock['bias'] = []
		stock['bias_sma'] = []
		stock['macd_line'] = []
		stock['macd_signal'] = []
		stock['macd_histogram'] = []
		stock['stochastic_d'] = []
		stock['stochastic_k'] = []
		stock['test'] = []
		stock['test_sma'] = []
		stock['pivots'] = []
		stock['bb_upper'] = []
		stock['bb_lower'] = []
		stock['bb_spread'] = []
		stock['bb_spread_dev'] = []
		stock['tr'] = []
		stock['kc_typ'] = []
		stock['kc_upper'] = []
		stock['kc_lower'] = []
		stock['squeeze'] = []
		stock['squeeze_val'] = []
		stock['signals_list_sell'] = []
		stock['signals_list_buy'] = []
		stock['browser'] = 0
		stock['reason'] = ''
		stock['flip'] = 0
		stock['no_buy'] = False
		stock['trailing_stop_loss'] = 0
		if(stock['transaction_type'] != "sell_away"):
			stock['hard_stop_loss'] = 0

	return stocks

def get_deal_result(deal):
	buy  = deal[0] * deal[1]
	sell = deal[0] * deal[2]
	res  = sell - buy
	
	return buy, sell, res

def calc_stats(closed_deals):
	results = []
	all_buys  = 0
	all_sells = 0
	
	#if(len(closed_deals) > 0 and stats['days'] > 0):
	if(len(closed_deals) > 0):
		for deal in closed_deals:
			buy, sell, res = get_deal_result(deal)
			all_buys  += buy
			all_sells += sell
			results.append(res)

		if(np.std(results) != 0):
			stats['sharpe'] = math.sqrt(len(results)) * np.mean(results) / np.std(results)
		else:
			stats['sharpe'] = 0

		profits = [i for i in results if i >= 0]
		losses  = [i for i in results if i < 0]
		profits_sum = (sum(profits))
		losses_sum = -(sum(losses))
		stats['profitability'] = float(len(profits) / float(len(closed_deals)))

		if(losses_sum != 0):
			stats['profit_factor'] = profits_sum/losses_sum
		else:
			stats['profit_factor'] = 100

		stats['all_buys']   = all_buys
		stats['all_sells']  = all_sells
		stats['result_eur'] =  all_sells - all_buys
		stats['result_per'] = (all_sells - all_buys) / all_buys
		stats['deals'] = len(closed_deals)
		stats['magic'] = 100 * stats['result_eur'] * stats['profitability'] * stats['sharpe'] / stats['days']
		if(stats['magic'] > 0 and stats['result_eur'] < 0):
			stats['magic'] *= -1
	else:
		stats['sharpe']        = 0
		stats['profit_factor'] = 0
		stats['profitability'] = 0
		stats['all_buys']      = 0
		stats['all_sells']     = 0
		stats['result_eur']    = 0
		stats['result_per']    = 0
		stats['magic']         = 0
		stats['deals'] 	       = 0

	return stats

def get_current_best_optimizer_vars():
	global optimizer_result_best_algo

	return optimizer_result_best_algo

def count_stats(final, stocks, last_total, grand_total, closed_deals, algo_params):
	global g_closed_deals
	global stats
	global param_names
	global previous_best_value
	global optimizer_result_best_stat
	global optimizer_result_best_algo
	global optimizer_results_vs_runs

	stats['days'] = stats['days'] + 1
	g_closed_deals.extend(closed_deals)

	stats = calc_stats(closed_deals)

	print('{:.2%}'.format(stats['result_per']), round(stats['all_buys'], 2), round(stats['all_sells'], 2), round(stats['result_eur'], 2), len(closed_deals), round(stats['sharpe'], 2), round(stats['profitability'], 2), round(stats['profit_factor'], 2))

	if(final):
		stats = calc_stats(g_closed_deals)
		if((stats['sharpe']   >= 2.8) and ((len(g_closed_deals) / stats['days']) >= 0.75) and stats['result_per'] >= 0.032):
			id = "T3"
		elif((stats['sharpe']   >= 2.0) and ((len(g_closed_deals) / stats['days']) >= 0.75) and stats['result_per'] >= 0.02):
			id = "T2"
		elif((stats['sharpe'] >= 1.0) and ((len(g_closed_deals) / stats['days']) >= 0.75)):
			id = "T1"
		else:
			id = "T0"

		print
		print("       │ days   deals    magic   eur/d   deals/d    sharpe   profitability   profit_factor   │   cci_u     cci_d   target   hard  trailing   cci_w   sma_len   rsi_len   rsi_lim   cci_big   rsi_big")
		print("───────┼─────────────────────────────────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────")
		print('{:<2s}     │{:>5d}{:>8d}{:>9.3f}{:>8.2f}{:>10.2f}{:>10.3f}{:>16.3f}{:>16.3f}   │{:>8.3f}{:>10.3f}{:>9.3f}{:>7.3f}{:>10.3f}{:>8d}{:>10d}{:>10d}{:>10.3f}{:>10.3f}{:>10.3f}'.format(
					id,
					stats['days'],
					len(g_closed_deals),
					#stats['result_per'],
					stats['magic'],
					stats['result_eur']/stats['days'],
					float(stats['deals'])/float(stats['days']),
					stats['sharpe'],
					stats['profitability'],
					stats['profit_factor'],
					algo_params[param_names[1]],
					algo_params[param_names[2]],
					algo_params[param_names[3]],
					algo_params[param_names[4]],
					algo_params[param_names[5]],
					algo_params[param_names[6]],
					algo_params[param_names[7]],
					algo_params[param_names[8]],
					algo_params[param_names[9]],
					algo_params[param_names[10]],
					algo_params[param_names[11]]
		))

		if(len(optimizer_result_best_stat) == 0):
			optimizer_result_best_stat = stats.copy()
			optimizer_result_best_algo = algo_params.copy()
		elif(stats[optimizer_stat_to_optimize] > optimizer_result_best_stat[optimizer_stat_to_optimize]):
			optimizer_result_best_stat = stats.copy()
			optimizer_result_best_algo = algo_params.copy()


		indicator = 'best   │'
		current_best_value = optimizer_result_best_stat[optimizer_stat_to_optimize]
		if(current_best_value > previous_best_value):
			previous_best_value = current_best_value
			indicator = 'best x │'
		
		print('{:<0s}{:>5d}{:>8d}{:>9.3f}{:>8.2f}{:>10.2f}{:>10.3f}{:>16.3f}{:>16.3f}   │{:>8.3f}{:>10.3f}{:>9.3f}{:>7.3f}{:>10.3f}{:>8d}{:>10d}{:>10d}{:>10.3f}{:>10.3f}{:>10.3f}'.format(
					indicator,
					optimizer_result_best_stat['days'],
					optimizer_result_best_stat['deals'],
					#optimizer_result_best_stat['result_per'],
					optimizer_result_best_stat['magic'],
					optimizer_result_best_stat['result_eur']/optimizer_result_best_stat['days'],
					float(optimizer_result_best_stat['deals'])/float(optimizer_result_best_stat['days']),
					optimizer_result_best_stat['sharpe'],
					optimizer_result_best_stat['profitability'],
					optimizer_result_best_stat['profit_factor'],
					optimizer_result_best_algo[param_names[1]],
					optimizer_result_best_algo[param_names[2]],
					optimizer_result_best_algo[param_names[3]],
					optimizer_result_best_algo[param_names[4]],
					optimizer_result_best_algo[param_names[5]],
					optimizer_result_best_algo[param_names[6]],
					optimizer_result_best_algo[param_names[7]],
					optimizer_result_best_algo[param_names[8]],
					optimizer_result_best_algo[param_names[9]],
					optimizer_result_best_algo[param_names[10]],
					optimizer_result_best_algo[param_names[11]]
		))

		del g_closed_deals[:]
		first_time = True
		stats['days'] = 0

	return grand_total


def post_to_toilet(time, action, name, amount, price):
	if(False):
		url = "http://ptsv2.com/t/stockrobo/post"
		data = {
			"time": time,
			"action": action,
			"name": name,
			"amount": amount,
			"price": price
		}
		resp = requests.post(url, json=data)
		print(resp)

def print_decision_vars(stock):
	if(False):
		len = 5
		print("current_top", stock['current_top'])
		print("sell_series", stock['sell_series'][-len:])
		print("sma_series_short", stock['sma_series_short'][-len:])
		print("sma_series_long", stock['sma_series_long'][-len:])
		print("cci_series", stock['cci_series'][-len:])
		print("rsi_series", stock['rsi_series'][-len:])
		print("cci_ptyp", stock['cci_ptyp'][-len:])
		print("bb_upper", stock['bb_upper'][-len:])
		print("bb_lower", stock['bb_lower'][-len:])

def do_transaction(stock, flip, reason, money, last_total, closed_deals, algo_params, index, options):
	buy  = float(stock['buy_series'][-1])
	sell = float(stock['sell_series'][-1])

	# buy
	if((not stock['active_position']) and (flip == 1)):
		stock['active_position'] = True
		stock['current_top']        = buy
		stock['last_buy']           = sell
		stock['hard_stop_loss']	    = ((1 + algo_params['hard'] * stock['leverage'] / 100) * sell)
		stock['target']             = ((1 + algo_params['target'] * stock['leverage'] / 100) * sell)
		stock['trailing_stop_loss'] = ((1 + algo_params['trailing'] * stock['leverage'] / 100) * sell)

		stock['signals_list_buy'].append((index, stock['sell_series'][-1]))

		if(stock['buy_full_money'] == True):
			if((float(stock['transaction_money']) / sell) > 1):
				stock['transaction_size'] = int(stock['transaction_money'] / sell)
			else:
				stock['transaction_size'] = float(stock['transaction_money'] / sell)

		if(options['do_actions']):
			print(datetime.now().strftime("%H:%M:%S"), "ACTION: BUY ", stock['name'], stock['transaction_size'], stock['last_buy'], reason)

		print_decision_vars(stock)

		post_to_toilet(datetime.now().strftime("%H:%M:%S"), "BUY", stock['name'], stock['transaction_size'], stock['last_buy'])

		stock['stocks'] = stock['transaction_size']
		if(not options['dry_run']):
			online.execute_buy_order_online(stock)

	# sell
	if(stock['active_position'] and (flip == -1)):
		money = money + ((buy - stock['last_buy']) * stock['transaction_size'])
		last_total = money
		this_deal = tuple([stock['transaction_size'], stock['last_buy'], buy])
		closed_deals.append(this_deal)
		stock['current_top'] = 0
		stock['active_position'] = False
		stock['signals_list_sell'].append((index, stock['buy_series'][-1]))
		result_eur = stock['stocks']*(buy - stock['last_buy'])
		result_per = (buy - stock['last_buy']) / stock['last_buy']
		if(options['do_actions']):
			print(datetime.now().strftime("%H:%M:%S"), "ACTION: SELL", stock['name'], stock['transaction_size'], buy, '{:.1%}'.format(result_per), round(result_eur, 2), reason, "total", round(last_total, 2))

		post_to_toilet(datetime.now().strftime("%H:%M:%S"), "SELL", stock['name'], stock['transaction_size'], buy)

		print_decision_vars(stock)

		if(not options['dry_run']):
			online.execute_sell_order_online(stock)

		stock['stocks'] = 0

		if(stock['transaction_type'] == 'sell_away'):
			print("sell_away completed, exit")
			online.logout(stock)
			quit()

	return money, last_total


def store_stock_values(stocks, index, options):
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
		f = open(options['outputfile'],"a+")
		if(len(stocks) == 1):
			# Binance
			f.write(str((buy_long, sell_long)) + '\n')
		else:
			# Nordnet
			f.write(str((buy_long, sell_long, buy_short, sell_short)) + '\n')
		f.close()



def check_args(argv):
	global options
	
	try:
		opts, args = getopt.getopt(argv[1:],"hgdazi:o:", ["dry-run"])
	except getopt.GetoptError:
		print('test.py -i <inputfile> -o <outputfile>')
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print(argv[0], '-i <inputfile> -o <outputfile>')
			sys.exit()
		elif opt in ("-i"):
			options['inputfile'] = arg
		elif opt in ("-o"):
			options['outputfile'] = arg
		elif opt in ("-g"):
			options['do_graph'] = True
		elif opt in ("-a"):
			options['do_actions'] = True
		elif opt in ("-z"):
			options['do_optimize'] = True
		elif opt in ("-d", "--dry-run"):
			options['dry_run'] = True

	if(options['inputfile'] == ''):
			print(argv[0], '-i <inputfile> -o <outputfile>')
			sys.exit()

	return options
