# -*- coding: iso-8859-15 -*-
from lxml import html
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
stats['files'] = 0
stats['days'] = 0
stats['ticks'] = 0
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
	        'cci_lim',
		'cci_down',
		'target',
		'ftarget',
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
		stock['current_bottom'] = 1000000
		stock['buy_series'] = []
		stock['sell_series'] = []
		stock['sma_series_short'] = []
		stock['sma_series_long'] = []
		stock['cci_series'] = []
		stock['rsi_series'] = []
		stock['cci_ptyp'] = []
		stock['signals_list_sell'] = []
		stock['signals_list_buy'] = []
		stock['browser'] = 0
		stock['reason'] = ''
		stock['flip'] = 0
		stock['target'] = 0
		stock['target_tweak'] = 0
		stock['no_buy'] = False
		stock['hard_stop_loss'] = 0
		stock['trailing_stop_loss'] = 0
		stock['trailing_entry'] = 0

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

		profits = [i for i in results if i > 0]
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
		stats['magic'] = 10 * stats['profitability'] * stats['sharpe'] * (stats['result_eur'] / stats['days']) * (stats['deals'] /  stats['days'])
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

def count_stats(final, stocks, last_total, grand_total, closed_deals, algo_params, entries):
	global g_closed_deals
	global stats
	global param_names
	global previous_best_value
	global optimizer_result_best_stat
	global optimizer_result_best_algo
	global optimizer_results_vs_runs

	stats['files']  = stats['files'] + 1
	stats['ticks'] = stats['ticks'] + entries
	stats['days'] = stats['ticks'] / 8640
	g_closed_deals.extend(closed_deals)

	stats = calc_stats(closed_deals)

	roi = stats['result_eur'] / 100
	
	print('roi: {:>6.2%}'.format(roi), ' profit: {:>6.2%}'.format(stats['result_per']), ' buys: {:>6.2f}'.format(round(stats['all_buys'], 2)),
	      ' sells: {:>6.2f}'.format(round(stats['all_sells'], 2)), ' tot: {:>5.2f}'.format(round(stats['result_eur'], 2)),
	      ' deals: {:>1d}'.format(len(closed_deals)), ' sharpe: {:>6.2f}'.format(round(stats['sharpe'], 2)),
	      ' prftbly: {:>6.2f}'.format(round(stats['profitability'], 2)), ' prf_fac: {:>6.2f}'.format(round(stats['profit_factor'], 2)))

	if(final):
		stats = calc_stats(g_closed_deals)
		if((stats['sharpe']   >= 2.8) and ((len(g_closed_deals) / stats['files']) >= 0.75) and stats['result_per'] >= 0.032):
			id = "T3"
		elif((stats['sharpe']   >= 2.0) and ((len(g_closed_deals) / stats['files']) >= 0.75) and stats['result_per'] >= 0.02):
			id = "T2"
		elif((stats['sharpe'] >= 1.0) and ((len(g_closed_deals) / stats['files']) >= 0.75)):
			id = "T1"
		else:
			id = "T0"

		print()
		print("       |  days  files  deals    magic   eur/d   deals/d    sharpe   prftbly   prof_fac   |  cci_lim     cci_d   target ftarget trailing   cci_w   sma_len   rsi_len   rsi_lim   cci_big   rsi_big")
		print("-------|---------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------")
		print('{:<2s}     |{:>6.1f}{:>7d}{:>7d}{:>9.1f}{:>8.2f}{:>10.2f}{:>10.3f}{:>10.3f}{:>11.3f}   |{:>9.3f}{:>10.3f}{:>9.3f}{:>8.3f}{:>9.3f}{:>8d}{:>10d}{:>10d}{:>10.3f}{:>10.3f}{:>10.3f}'.format(
					id,
					stats['days'],
					stats['files'],
					len(g_closed_deals),
					stats['magic'],
					float(stats['result_eur']/stats['days']),
					float(stats['deals']/stats['days']),
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


		indicator = 'best   |'
		current_best_value = optimizer_result_best_stat[optimizer_stat_to_optimize]
		if(current_best_value > previous_best_value):
			previous_best_value = current_best_value
			indicator = 'best x |'
		
		print('{:<0s}{:>6.1f}{:>7d}{:>7d}{:>9.1f}{:>8.2f}{:>10.2f}{:>10.3f}{:>10.3f}{:>11.3f}   |{:>9.3f}{:>10.3f}{:>9.3f}{:>8.3f}{:>9.3f}{:>8d}{:>10d}{:>10d}{:>10.3f}{:>10.3f}{:>10.3f}'.format(
					indicator,
					stats['days'],
					optimizer_result_best_stat['files'],
					optimizer_result_best_stat['deals'],
					#optimizer_result_best_stat['result_per'],
					optimizer_result_best_stat['magic'],
					optimizer_result_best_stat['result_eur']/stats['days'],
					float(optimizer_result_best_stat['deals'])/stats['days'],
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
		stats['files'] = 0
		stats['days'] = 0
		stats['ticks'] = 0

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

def do_transaction(stock, flip, reason, money, last_total, closed_deals, algo_params, index, options):
	buy  = float(stock['buy_series'][-1])
	sell = float(stock['sell_series'][-1])

	# buy
	if((not stock['active_position']) and (flip == 1)):
		stock['active_position'] = True
		stock['current_top']        = buy
		stock['last_buy']           = sell
		stock['target']             = ((1 + algo_params['target'] * stock['leverage'] / 100) * sell)
		stock['trailing_stop_loss'] = ((1 + algo_params['trailing'] * stock['leverage'] / 100) * sell)
		stock['hard_stop_loss'] = 0

		stock['signals_list_buy'].append((index, stock['sell_series'][-1]))

		if(stock['buy_full_money'] == True):
			if((float(stock['transaction_money']) / sell) > 1):
				stock['transaction_size'] = int(stock['transaction_money'] / sell)
			else:
				stock['transaction_size'] = float(stock['transaction_money'] / sell)

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
		stock['current_bottom'] = 1000000
		stock['active_position'] = False
		stock['signals_list_sell'].append((index, stock['buy_series'][-1]))
		result_eur = stock['stocks']*(buy - stock['last_buy'])
		result_per = (buy - stock['last_buy']) / stock['last_buy']
		marker = "down"
		if(result_eur > 0):
			marker = "up"
		if(options['do_actions']):
			print(datetime.now().strftime("%H:%M:%S"), "ACTION: SELL", stock['name'], stock['transaction_size'], buy, '{:.1%}'.format(result_per),
			      round(result_eur, 2), reason, "total", round(last_total, 2), marker)

		stock['target_tweak'] = 0

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
