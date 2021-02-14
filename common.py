# -*- coding: iso-8859-15 -*-
from lxml import html
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
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

optimizer_results_stats = []
optimizer_results_algos = []

#result parameter to optimize to
optimizer_param_to_optimize = 'result_eur'
previous_best_value = -10000

g_closed_deals = []
stats = {}
stats['sharpe'] = 0
stats['days'] = 0
stats['profitability'] = 0
stats['profit_factor'] = 0
stats['result_eur'] = 0
stats['result_per'] = 0

options = {}
options['inputfile']   = ''
options['outputfile']  = 'guru99.txt'
options['do_graph']    = False
options['do_actions']  = False
options['dry_run']     = False
options['do_optimize'] = False

param_names = ['cci_up',
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

def init_stocks(algo_params, options):
	#print("open stocks file", options['inputfile'])
	with open(options['inputfile'], 'r') as f:
		stocks = json.load(f)

	for stock in stocks:
		stock['valid'] = False
		stock['buy'] = 0
		stock['sell'] = 0
		stock['current_top'] = 0
		stock['dir'] = 0
		stock['buy_series'] = []
		stock['sell_series'] = []
		stock['sma_series_short'] = []
		stock['sma_series_long'] = []
		stock['cci_series'] = []
		stock['rsi_series'] = []
		stock['cci_ptyp'] = []
		stock['hurst'] = []
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

		if(stock['active_position'] and (stock['transaction_type'] == 'sell_away')):
			stock['trailing_stop_loss'] = ((1 + algo_params['trailing'] * stock['leverage'] / 100) * stock['last_buy'])
			print("buy", stock['last_buy'], "hard_stop_loss", stock['hard_stop_loss'], stock['stocks'])
		else:
			stock['hard_stop_loss'] = 0
			stock['trailing_stop_loss'] = 0

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
	else:
		stats['sharpe']        = 0
		stats['profit_factor'] = 0
		stats['profitability'] = 0
		stats['all_buys']      = 0
		stats['all_sells']     = 0
		stats['result_eur']    = 0
		stats['result_per']    = 0
		stats['deals'] 	       = 0

	return stats

def count_stats(final, stocks, last_total, grand_total, closed_deals, algo_params):
	global g_closed_deals
	global stats
	global optimizer_results
	global param_names
	global previous_best_value

	g_closed_deals.extend(closed_deals)

	stats = calc_stats(closed_deals)

	print('{:.2%}'.format(stats['result_per']), round(stats['all_buys'], 2), round(stats['all_sells'], 2), round(stats['result_eur'], 2), len(closed_deals), round(stats['sharpe'], 2), round(stats['profitability'], 2), round(stats['profit_factor'], 2))

	stats['days'] = stats['days'] + 1

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
		print("       │    days    deals   profit   eur/d   deals/d    sharpe   profitability   profit_factor   │   cci_u    cci_d   target   hard  trailing   cci_w   sma_len   rsi_len   rsi_lim   cci_big   rsi_big")
		print("───────┼─────────────────────────────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────")
		print('{:<2s}     │{:>8d}{:>9d}{:>9.2%}{:>8.2f}{:>10.2f}{:>10.2f}{:>16.2f}{:>16.2f}   │{:>8.2f}{:>9.2f}{:>9.2f}{:>7.2f}{:>10.2f}{:>8d}{:>10d}{:>10d}{:>10.2f}{:>10.2f}{:>10.2f}'.format(
					id,
					stats['days'],
					len(g_closed_deals),
					stats['result_per'],
					stats['result_eur']/stats['days'],
					float(stats['deals'])/float(stats['days']),
					stats['sharpe'],
					stats['profitability'],
					stats['profit_factor'],
					algo_params[param_names[0]],
					algo_params[param_names[1]],
					algo_params[param_names[2]],
					algo_params[param_names[3]],
					algo_params[param_names[4]],
					algo_params[param_names[5]],
					algo_params[param_names[6]],
					algo_params[param_names[7]],
					algo_params[param_names[8]],
					algo_params[param_names[9]],
					algo_params[param_names[10]]
		))



		s = stats.copy()
		a = algo_params.copy()
		optimizer_results_stats.append(s)
		optimizer_results_algos.append(a)

		seq = [x[optimizer_param_to_optimize] for x in optimizer_results_stats]
		best_run_idx = seq.index(max(seq))

		indicator = 'best   │'
		current_best_value = optimizer_results_stats[best_run_idx][optimizer_param_to_optimize]
		if(current_best_value > previous_best_value):
			previous_best_value = current_best_value
			indicator = 'best * │'
		
		print('{:<0s}{:>8d}{:>9d}{:>9.2%}{:>8.2f}{:>10.2f}{:>10.2f}{:>16.2f}{:>16.2f}   │{:>8.2f}{:>9.2f}{:>9.2f}{:>7.2f}{:>10.2f}{:>8d}{:>10d}{:>10d}{:>10.2f}{:>10.2f}{:>10.2f}'.format(
					indicator,
					optimizer_results_stats[best_run_idx]['days'],
					optimizer_results_stats[best_run_idx]['deals'],
					optimizer_results_stats[best_run_idx]['result_per'],
					optimizer_results_stats[best_run_idx]['result_eur']/optimizer_results_stats[best_run_idx]['days'],
					float(optimizer_results_stats[best_run_idx]['deals'])/float(optimizer_results_stats[best_run_idx]['days']),
					optimizer_results_stats[best_run_idx]['sharpe'],
					optimizer_results_stats[best_run_idx]['profitability'],
					optimizer_results_stats[best_run_idx]['profit_factor'],
					optimizer_results_algos[best_run_idx][param_names[0]],
					optimizer_results_algos[best_run_idx][param_names[1]],
					optimizer_results_algos[best_run_idx][param_names[2]],
					optimizer_results_algos[best_run_idx][param_names[3]],
					optimizer_results_algos[best_run_idx][param_names[4]],
					optimizer_results_algos[best_run_idx][param_names[5]],
					optimizer_results_algos[best_run_idx][param_names[6]],
					optimizer_results_algos[best_run_idx][param_names[7]],
					optimizer_results_algos[best_run_idx][param_names[8]],
					optimizer_results_algos[best_run_idx][param_names[9]],
					optimizer_results_algos[best_run_idx][param_names[10]]
		))
		print

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
		print resp

def do_transaction(stock, flip, reason, money, last_total, closed_deals, algo_params, index, options):
	buy  = float(stock['buy_series'][-1])
	sell = float(stock['sell_series'][-1])

	# buy
	if((not stock['active_position']) and (flip == 1)):
		stock['active_position'] = True
		stock['current_top']        = buy
		stock['last_buy']           = sell
		stock['hard_stop_loss']	    = ((1 + algo_params['hard']     * stock['leverage'] / 100) * sell)
		stock['trailing_stop_loss'] = ((1 + algo_params['trailing'] * stock['leverage'] / 100) * sell)
		stock['signals_list_buy'].append((index, stock['sell_series'][-1]))

		if(stock['buy_full_money'] == True):
			stock['transaction_size'] = int(stock['transaction_money'] / sell)

		if(options['do_actions']):
			print(datetime.now().strftime("%H:%M:%S"), "ACTION: BUY ", stock['name'], stock['transaction_size'], stock['last_buy'], reason)

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
		f.write(str((buy_long, sell_long, buy_short, sell_short)) + '\n')
		f.close()



def check_args(argv):
	global options
	
	try:
		opts, args = getopt.getopt(argv[1:],"hgdazi:o:", ["dry-run"])
	except getopt.GetoptError:
		print 'test.py -i <inputfile> -o <outputfile>'
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print argv[0], '-i <inputfile> -o <outputfile>'
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
			print argv[0], '-i <inputfile> -o <outputfile>'
			sys.exit()

	return options
