# -*- coding: iso-8859-15 -*-
from collections import OrderedDict
import random
import math
import numpy as np
#import scipy
import common
import time

#from hurst import compute_Hc
#global_test = -0.005

PIVOT_WIN = 600
algos = []
techs = []

optimizer_window =  None
optimizer_steps  =  None

optimizer_runs    =  0
optimizer_param   =  0
optimizer_bigruns =  0
optimizer_params = []

progress_idx = 0

trailing_tweak = 0
p = {}

param_names = [ 'name',		#0
	        'cci_lim',	#1
		'cci_down',	#2
		'target',	#3
		'ftarget',	#4
		'trailing',	#5
		'cci_window',	#6
		'sma_len',	#7
		'rsi_len',	#8
		'rsi_lim',	#9
		'cci_big',	#10
		'rsi_big']	#11

# optimizer window/step
optimizer_window_percentage_min =   1
optimizer_window_percentage_max =  10
optimizer_window_steps_min      =   5
optimizer_window_steps_max      =  50

# parameter list to optimize
#params_idx = [1, 2, 3, 4, 5, 9, 10, 11]
params_idx = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
#params_idx = [4]
#params_idx = [1,2,5,6,7,8,9]

def get_algo_params():
	#         	 1	    2	      3        4         5        6          7          8          9         10         11
	#          cci_lim   cci_down    target  ftarget  trailing    cci_w    sma_len    rsi_len    rsi_lim    cci_big    rsi_big
	algo_params = (
	('doge',  -169.133,  -132.248,    2.538,   0.062,   -6.124,      68,       140,       127,    51.111,  -217.091,    39.776), # doge 96.1/178.9
	('btc',   -163.702,  -126.863,    2.164,   0.007,   -5.746,      44,       122,       167,    51.727,  -234.257,    42.197), # btctest
	('eth',   -157.445,  -133.088,    2.563,   0.069,   -6.787,      68,       142,       127,    50.991,  -217.087,    39.693), # eth test
	)
	return algo_params


def set_new_params(stocks):
	global optimizer_params
	global p

	bp = get_algo_params()

	index = 0
	# find the right algo
	for parset in bp:
		if(parset[0] == stocks[0]['algo']):
			break
		index += 1

	if(index >= len(bp)):
		print("No matching algo, exit")
		quit()

	p['name'] 	= bp[index][0]
	p['cci_lim'] 	= bp[index][1]
	p['cci_down'] 	= bp[index][2]
	p['target']	= bp[index][3]
	p['ftarget'] 	= bp[index][4]
	p['trailing'] 	= bp[index][5]
	p['cci_window']	= bp[index][6]
	p['sma_len']	= bp[index][7]
	p['rsi_len']	= bp[index][8]
	p['rsi_lim']	= bp[index][9]	
	p['cci_big'] 	= bp[index][10]
	p['rsi_big'] 	= bp[index][11]

	print("Parameters", p)
	
	optimizer_params = p.copy()

	return p

def randomize_params():
	global optimizer_params
	global p

	diff = 50
	p['cci_lim'] 	=  random.uniform(p['cci_lim'] - diff,  p['cci_lim'] + diff)
	p['cci_down'] 	=  random.uniform(p['cci_lim'], p['cci_down'] + diff)
	
	diff = 2
	low = p['target'] - diff
	if(low < 0):
		low = 0
	p['target']	=  random.uniform(low, p['target'] + diff)
	
	diff = 0.1
	low = p['ftarget'] - diff
	if(low < 0):
		low = 0
	p['ftarget'] 	=  random.uniform(low, p['ftarget'] + diff)
	
	diff = 3
	high = p['trailing'] + diff
	if(high > 0):
		high = 0
	p['trailing'] 	=  random.uniform(p['trailing'] - diff, high)
	
	diff = 50
	p['cci_window']	=  int(random.uniform(40, p['cci_window'] + diff))
	p['sma_len']	=  int(random.uniform(100, p['sma_len'] + diff))
	p['rsi_len']	=  int(random.uniform(100, p['rsi_len'] + diff))
	
	diff = 3
	p['rsi_lim']	=  random.uniform(p['rsi_lim'] - diff, p['rsi_lim'] + diff)
	
	diff = 50
	p['cci_big'] 	=  random.uniform(p['cci_big'] - diff, p['cci_big'] + diff)
	
	diff = 3
	p['rsi_big'] 	=  random.uniform(p['rsi_big'] - diff, p['rsi_big'] + diff)

	print("Randomized", p)

	optimizer_params = p.copy()

	return p

def get_params():
	global p
	return p

def optimize_params(randomize_params_start_values = False):
	global optimizer_runs
	global optimizer_param
	global optimizer_steps
	global optimizer_bigruns
	global optimizer_params
	global optimizer_window
	global optimizer_steps
	global params_idx
	global param_names
	global p
	global start_time

	# for manual optimizing
	#global global_test
	#global_test += 0.0005
	#print("SMA_SPEED_CUTOFF_PERCENT", 0.05 + global_test)
	#return p

	optimizer_result_best_algo_params = common.get_current_best_optimizer_vars()

	if(optimizer_runs == 0):
		if(randomize_params_start_values):
			print("Randomized parameter start values")
			algo_params = randomize_params()

		params_idx = random.sample(params_idx, len(params_idx))
		print("Randomized order", params_idx)

		optimizer_window =  float(random.uniform(optimizer_window_percentage_min,  optimizer_window_percentage_max))
		optimizer_steps  =  int(random.uniform(optimizer_window_steps_min,       optimizer_window_steps_max))
		#optimizer_window  = 50
		#optimizer_steps   = 5
		print("Randomized window: +-", optimizer_window, "%, steps: ", optimizer_steps+1)

	param_value = optimizer_params[param_names[params_idx[optimizer_param]]]

	if(param_value > 0):
		win_min  = param_value * (float(100 - optimizer_window)/100)
		win_max  = param_value * (1 + float(optimizer_window)/100)
		win_size = win_max - win_min
		win_step = win_size / optimizer_steps
	else:
		win_min  = param_value * (1 + float(optimizer_window)/100)
		win_max  = param_value * (float(100 - optimizer_window)/100)
		win_size = win_min - win_max
		win_step = -win_size / optimizer_steps

	temp_steps = optimizer_steps

	if(param_names[params_idx[optimizer_param]] == 'cci_window' or
	   param_names[params_idx[optimizer_param]] == 'sma_len'    or
	   param_names[params_idx[optimizer_param]] == 'rsi_len'):
		if(win_step <= 1):
			win_step = 1
			temp_steps = int(win_size)


	# If param optimizing run is done, change to optimal value, move to next
	if(optimizer_runs == (optimizer_steps+1) or
	   optimizer_runs > temp_steps):
		param_name  = param_names[params_idx[optimizer_param]]
		p[param_name] = optimizer_result_best_algo_params[param_name]
		optimizer_runs = 0
		optimizer_param += 1


	if(optimizer_param == len(params_idx)):
		print("One optimizer bigrun done")
		optimizer_runs  =  0
		optimizer_param =  0
		optimizer_bigruns += 1

		# set the optimal set as a baseline
		optimizer_params = optimizer_result_best_algo_params

		return p

	param_value = optimizer_params[param_names[params_idx[optimizer_param]]]
	
	if(param_value > 0):
		win_min  = param_value * (float(100 - optimizer_window)/100)
		win_max  = param_value * (1 + float(optimizer_window)/100)
		win_size = win_max - win_min
		win_step = win_size / optimizer_steps
	else:
		win_min  = param_value * (1 + float(optimizer_window)/100)
		win_max  = param_value * (float(100 - optimizer_window)/100)
		win_size = win_min - win_max
		win_step = -win_size / optimizer_steps

	random_offset = 0.25 * float(random.uniform(-win_step, win_step))

	temp_steps = optimizer_steps

	if(param_names[params_idx[optimizer_param]] == 'cci_window' or
	   param_names[params_idx[optimizer_param]] == 'sma_len'    or
	   param_names[params_idx[optimizer_param]] == 'rsi_len'):
		if(win_step <= 1):
			win_step = 1
			temp_steps = int(win_size)

		p[param_names[params_idx[optimizer_param]]] = int(win_min + (optimizer_runs * win_step))
	else:
		p[param_names[params_idx[optimizer_param]]] = round(float(win_min + random_offset + (optimizer_runs * win_step)), 4)


	optimizer_runs += 1

	xs = (' ' * 98) + (' ' * 9 * (params_idx[optimizer_param] - 1)) + '^'
	print(xs)

	b_spaces = '-' * (optimizer_runs - 1)
	a_spaces = '-' * (temp_steps + 1 - optimizer_runs)
	progress_runs = "[" + b_spaces + "x" + a_spaces + "]"
	b_spaces = '-' * optimizer_param
	a_spaces = '-' * (len(params_idx) - 1 - optimizer_param)
	progress_pars = "[" + b_spaces + "x" + a_spaces + "]"

	print('optimizer running {:<1d}: param {:<1d}/{:<2d}, run {:<1d}/{:<1d}, {:<4s}: {:<4.3f} [{:>0.3f},{:>8.3f},{:>6.3f}]'.format(
		optimizer_bigruns, optimizer_param, len(params_idx) - 1,
		optimizer_runs - 1,  temp_steps,
		param_names[params_idx[optimizer_param]], p[param_names[params_idx[optimizer_param]]],
		round(win_min, 3), round(win_max, 3), round(win_step, 3)))
	print(optimizer_bigruns, progress_pars, progress_runs)

	return p

def init():
	global algos
	global techs
	global start_time
	global trailing

	start_time = time.time()
	random.seed()

	techs = [calc_sma,
		 calc_rsi,
		 calc_cci,
		]

	algos = [algo_cci_trigger,
		 algo_trailing_stoploss,
		 algo_reach_target,
		 algo_hard_stoploss,
		]
	
	return techs, algos

def print_decision_vars(stock):
	if(True):
		len = 20
		print("current_top", stock['current_top'])
		print("sell_series", stock['sell_series'][-len:])
		print("sma_series_short", stock['sma_series_short'][-len:])
		print("sma_series_long", stock['sma_series_long'][-len:])
		print("cci_series", stock['cci_series'][-len:])
		print("rsi_series", stock['rsi_series'][-len:])

def print_decision_bars(index, stock, algo_params, trigger1, trigger2, flip):
	global progress_idx
	progress = ['|', '/', '-', '\\', '|', '/', '-', '\\']
	
	trig1_str = ":cci ["
	idx = 0
	for tr in trigger1:
		if(tr == 1):
			trig1_str += str(idx)
		else:
			trig1_str += "-"
		idx += 1
	trig1_str += "]"

	trig2_str = "cci_rsi ["
	idx = 0
	for tr in trigger2:
		if(tr == 1):
			trig2_str += str(idx)
		else:
			trig2_str += "-"
		idx += 1
	trig2_str += "]"

	xval = 0
	if(stock['cci_series'][-2] < algo_params['cci_down']):
		diff = int(algo_params['cci_down'] - stock['cci_series'][-2])
		if(diff > 50):
			diff = 50
			xval = 1
		else:
			xval = 50 - diff
	xstr1 = '[' + (xval)*'#' + (50-xval)*'-' + ']'

	xval = 0
	if(stock['cci_series'][-2] < algo_params['cci_big']):
		diff = int(algo_params['cci_big'] - stock['cci_series'][-2])
		if(diff > 50):
			diff = 50
			xval = 1
		else:
			xval = 50 - diff
	xstr2 = '[' + (xval)*'#' + (50-xval)*'-' + ']'


	print(progress[progress_idx], index, xstr1, xstr2, trig1_str, trig2_str, end = '\r')
	progress_idx += 1
	if(progress_idx == 8):
		progress_idx = 0
	
	if(flip):
		print()


def algo_cci_trigger(stock, index, algo_params, live):
	flip = 0
	reason = ""
	SMA_LONG = algo_params['sma_len']
	buy  = float(stock['buy_series'][-1])
	sell = float(stock['sell_series'][-1])

	trigger1 = [0,0,0,0,0]
	trigger2 = [0,0,0]

	if(index >= SMA_LONG):
		
		#### CCI ####
		if(not stock['active_position'] and not stock['no_buy']):
			trigger1[0] = 1

		if(stock['cci_series'][-2] < algo_params['cci_down'] and stock['cci_series'][-1] >= algo_params['cci_down']):
			trigger1[1] = 1

		if(stock['rsi_series'][-1] > algo_params['rsi_lim']):
			trigger1[2] = 1
		
		if(buy > stock['sma_series_long'][-1]):
			trigger1[3] = 1
		
		if(stock['cci_series'][-2] > algo_params['cci_lim']):
			trigger1[4] = 1

		if(np.sum(trigger1) == 5):
			'''
			X = np.array([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19])
			z = np.polyfit(X, stock['buy_series'][-20:], 1)
			buy_diff = z[0]

			z = np.polyfit(X, stock['cci_series'][-20:], 1)
			cci_diff = z[0]

			z = np.polyfit(X, stock['rsi_series'][-20:], 1)
			rsi_diff = z[0]

			d = buy_diff / (cci_diff * rsi_diff) * 100

			if(d > -0.0032 and d < 0.0051):
			'''
			# doge rsi exclusion filter after statistical analysis
			if(stock['name'] != 'DOGEUSDT'):
				reason = "cci_sma"
				flip = 1
			else:
				if(np.mean(stock['rsi_series'][-20:-5]) < 55.0):
					reason = "cci_sma"
					flip = 1

		#### CCI_RSI ####
		if(not stock['active_position'] and not stock['no_buy']):
			trigger2[0] = 1

		if(stock['cci_series'][-2] < algo_params['cci_big'] and stock['cci_series'][-1] > algo_params['cci_big']):
			trigger2[1] = 1

		if(stock['rsi_series'][-1] < algo_params['rsi_big']):
			trigger2[2] = 1

		if(np.sum(trigger2) == 3):
			if(np.min(stock['rsi_series'][-50:]) < 1):
				print("fail rsi fix")
			else:
				reason = "cci_rsi"
				flip = 1

		#live = True
		if(live):
			if(index == SMA_LONG):
				print("cci/cci_rsi active")

			if(not stock['active_position']):
				print_decision_bars(index, stock, algo_params, trigger1, trigger2, flip)
				

	return flip, reason


def algo_trailing_stoploss(stock, index, algo_params, live):
	flip = 0
	reason = ""
	buy  = float(stock['buy_series'][-1])
	sell = float(stock['sell_series'][-1])

	if(stock['active_position']):
		if(stock['target_tweak'] == 0):
			trailing = algo_params['trailing']
			reason = "trailing_stop_loss"
		else:
			trailing = stock['target_tweak']
			reason = "flex_target"

		target_price = ((1 + float(trailing) * stock['leverage'] / 100) * stock['current_top'])
			
		if(buy > stock['current_top']):
			stock['current_top'] = buy
			stock['trailing_stop_loss'] = target_price
			if(live):
				print('{:<0s}{:>6.4f}{:<0s}{:>6.4f}'.format("top ", round(stock['current_top'], 4), " -> trailing stop ", round(stock['trailing_stop_loss'], 4)))
		if(sell <= stock['trailing_stop_loss']):
			flip = -1

	return flip, reason


def algo_reach_target(stock, index, algo_params, live):
	global global_test

	# optimized manually 28.5.2021
	D_FLEX_TRAILING = 2.12
	SMA_SPEED_CUTOFF_PERCENT = 0.049
	HARD_TRIGGER_TARGET = 0.990
	HARD_TRIGGER_CUTOFF = 1.004

	flip = 0
	reason = ""
	buy  = float(stock['buy_series'][-1])

	if(stock['active_position']):
		# for doge only
		#if(stock['name'] == 'DOGEUSDT' and stock['hard_stop_loss'] == 0 and buy >= (HARD_TRIGGER_TARGET * stock['target'])):
		if(stock['hard_stop_loss'] == 0 and buy >= (HARD_TRIGGER_TARGET * stock['target'])):
			stock['hard_stop_loss'] = HARD_TRIGGER_CUTOFF * stock['last_buy']
			if(live):
				print(">pre-target, hard_stop_loss set", stock['hard_stop_loss'])

		if(buy >= stock['target']):
			if(stock['target_tweak'] == 0):
				sma_speed = 100 * (stock['sma_series_short'][-1] / stock['sma_series_short'][-2] - 1)
				if(sma_speed > SMA_SPEED_CUTOFF_PERCENT):
					tweak = algo_params['ftarget'] * D_FLEX_TRAILING

				else:
					tweak = algo_params['ftarget']

				stock['target_tweak'] = algo_params['trailing'] * tweak

				if(live):
					print(">target, new trailing percentage limit set", stock['target_tweak'])

	return flip, reason

def algo_hard_stoploss(stock, index, algo_params, live):
	flip = 0
	reason = ""
	buy  = float(stock['buy_series'][-1])

	if(stock['active_position']):
		if(stock['hard_stop_loss'] > 0):
			if(buy <= stock['hard_stop_loss']):
				stock['hard_stop_loss'] = 0
				flip = -1
				reason = "hard_stop_loss"

	return flip, reason

def calc_sma(stock, index, algo_params):
	SMA_SHORT = 40
	SMA_LONG = algo_params['sma_len']

	stock['sma_series_short'].append(np.mean(stock['buy_series'][-SMA_SHORT:]))
	stock['sma_series_long'].append(np.mean(stock['buy_series'][-SMA_LONG:]))


def calc_rsi(stock, index, algo_params):
	RSI_WINDOW = algo_params['rsi_len']

	gains = []
	losses = []
	avg_gains = 0
	avg_losses = 0
	# calc avg gains in window, calc avg losses in window
	window = stock['buy_series'][-RSI_WINDOW:]
	for i in range(len(window) - 1):
		if(window[i+1] > window[i]):
			gains.append(window[i+1] - window[i])
			losses.append(0)
		elif(window[i+1] < window[i]):
			losses.append(window[i] - window[i+1])
			gains.append(0)
			
	if(len(gains) > 0):
		avg_gains  = np.mean(gains)
	else:
		avg_gains = 0
	if(len(losses) > 0):
		avg_losses = np.mean(losses)
	else:
		avg_losses = 0
	if(avg_losses > 0):
		rs = avg_gains / avg_losses
		rsi = 100 - (100 / (1 + rs))
	else:
		rsi = 100

	stock['rsi_series'].append(rsi)


def calc_cci(stock, index, algo_params):
	p_max = np.max(stock['sell_series'][-algo_params['cci_window']:])
	p_min = np.min(stock['sell_series'][-algo_params['cci_window']:])
	p_clo = float(stock['sell_series'][-1])
	p_typ = ((p_max + p_min + p_clo) / 3)
	stock['cci_ptyp'].append(p_typ)
	p_sma = np.mean(stock['cci_ptyp'][-algo_params['cci_window']:])
	p_std = np.std(stock['cci_ptyp'][-algo_params['cci_window']:])

	if(p_std != 0):
		stock['cci_series'].append((p_typ - p_sma) / p_std / 0.015)
	else:
		stock['cci_series'].append(0)


def check_signals(stock, index, algo_params, live):
	global algos
	global trailing_tweak

	flip = 0
	reason = ""

	# calculate all technicals
	for tech in techs:
		tech(stock, index, algo_params)
	
	# loop through all algos
	for algo in algos:
		flip, reason = algo(stock, index, algo_params, live)
		stock['flip'] = flip
		if(flip != 0):
			trailing_tweak = 0
			return flip, reason

	return flip, reason
