# -*- coding: iso-8859-15 -*-
from collections import OrderedDict
import random
import math
import numpy as np
#import scipy
import common
import time

#from hurst import compute_Hc

PIVOT_WIN = 600
algos = []
techs = []

optimizer_window =  None
optimizer_steps  =  None

optimizer_runs    =  0
optimizer_param   =  0
optimizer_bigruns =  0
optimizer_params = []

trailing_tweak = 0
p = {}

param_names = [ 'name',		#0
	        'cci_up',	#1
		'cci_down',	#2
		'target',	#3
		'ttrail',	#4
		'trailing',	#5
		'cci_window',	#6
		'sma_len',	#7
		'rsi_len',	#8
		'rsi_lim',	#9
		'cci_big',	#10
		'rsi_big']	#11

# optimizer window/step
optimizer_window_percentage_min =  90
optimizer_window_percentage_max =  90
optimizer_window_steps_min      =  50
optimizer_window_steps_max      =  50

# parameter list to optimize
#params_idx = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
#params_idx = [2, 3, 4, 5, 9, 10, 11]
params_idx = [4]
#params_idx = [2,3,4,5,7,9]

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
	p['cci_up'] 	= bp[index][1]
	p['cci_down'] 	= bp[index][2]
	p['target']	= bp[index][3]
	p['ttrail'] 	= bp[index][4]
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

	p['cci_up'] 	=  random.uniform(130,  230)
	p['cci_down'] 	= -random.uniform(70,  170)
	p['target']	=  random.uniform(1, 3)
	p['ttrail'] 	= -random.uniform(1, 3)
	p['trailing'] 	= -random.uniform(1, 3)
	p['cci_window']	=  int(random.uniform(50, 100))
	p['sma_len']	=  int(random.uniform(100, 200))
	p['rsi_len']	=  int(random.uniform(250, 350))
	p['rsi_lim']	=  random.uniform(20, 50)
	p['cci_big'] 	=  random.uniform(100, 200)
	p['rsi_big'] 	=  random.uniform(30, 50)

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

	optimizer_result_best_algo_params = common.get_current_best_optimizer_vars()

	if(optimizer_runs == 0):
		if(randomize_params_start_values):
			print("Randomized parameter start values")
			algo_params = randomize_params()

		params_idx = random.sample(params_idx, len(params_idx))
		print("Randomized order", params_idx)

		optimizer_window =  int(random.uniform(optimizer_window_percentage_min,  optimizer_window_percentage_max))
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

	xs = ' ' * 100 + ' ' * 9 * (params_idx[optimizer_param] - 1) + '^'
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
		]
	
	return techs, algos

def print_decision_vars(stock):
	if(True):
		len = 5
		print("current_top", stock['current_top'])
		print("sell_series", stock['sell_series'][-len:])
		print("sma_series_short", stock['sma_series_short'][-len:])
		print("sma_series_long", stock['sma_series_long'][-len:])
		print("cci_series", stock['cci_series'][-len:])
		print("rsi_series", stock['rsi_series'][-len:])

# winner scan: cat testrun_dax1 | grep days -A6
def get_algo_params():
	#          cci_up    cci_down    target  ftarget  trailing    cci_w    sma_len    rsi_len    rsi_lim    cci_big    rsi_big
	algo_params = (
	('doge',   000.000,  -132.394,    2.602,  0.232,    -5.024,      68,       121,       178,    51.098,   240.422,    39.269), # dogetest
	('btc',    147.329,  -138.338,    5.587, -1.632,    -2.159,      69,       142,       180,    29.869,   314.882,    42.664), # btc.49
	)
	return algo_params

def algo_cci_trigger(stock, index, algo_params):
	flip = 0
	reason = ""

	SMA_LONG = algo_params['sma_len']
	buy  = float(stock['buy_series'][-1])
	sell = float(stock['sell_series'][-1])

	if(index > SMA_LONG):
		
		if(not stock['active_position'] and not stock['no_buy']):
			if((stock['cci_series'][-2] < algo_params['cci_down']) and (stock['cci_series'][-1] >= algo_params['cci_down']) and
			    stock['rsi_series'][-1] > algo_params['rsi_lim']):
				if(buy > stock['sma_series_long'][-1]):
					reason = "cci"
					flip = 1
		
		if(stock['cci_series'][-2] < -algo_params['cci_big'] and stock['cci_series'][-1] > -algo_params['cci_big'] and
			stock['rsi_series'][-1] < algo_params['rsi_big']):
			reason = "cci_rsi"
			flip = 1
		
	return flip, reason


def algo_trailing_stoploss(stock, index, algo_params):
	global trailing_tweak

	flip = 0
	reason = ""
	buy  = float(stock['buy_series'][-1])
	sell = float(stock['sell_series'][-1])

	if(stock['active_position']):
		if(trailing_tweak == 0):
			trailing = algo_params['trailing']
			reason = "trailing_stop_loss"
		else:
			trailing = trailing_tweak
			reason = "flex_target"

		target_price = ((1 + float(trailing) * stock['leverage'] / 100) * stock['current_top'])
			
		if(buy >= stock['current_top']):
			stock['current_top'] = buy
			stock['trailing_stop_loss'] = target_price
		if(sell <= stock['trailing_stop_loss']):
			flip = -1

	return flip, reason


def algo_reach_target(stock, index, algo_params):
	global trailing_tweak

	flip = 0
	reason = ""
	buy  = float(stock['buy_series'][-1])
	
	if(stock['active_position']):
		if(buy >= stock['target']):
			#print("target reached", buy, stock['target'])
			stock['target'] = stock['target'] * 10
			#print("new target", stock['target'])
			trailing_tweak = algo_params['trailing'] * algo_params['ttrail']
			#print("new trailing stop_loss", trailing_tweak)
			#trailing = algo_params['trailing']
			#target_price = ((1 + float(trailing) * stock['leverage'] / 100) * stock['current_top'])


			#reason = "target"
			#flip = -1

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


def check_signals(stock, index, algo_params):
	global algos
	global trailing_tweak

	flip = 0
	reason = ""

	# calculate all technicals
	for tech in techs:
		tech(stock, index, algo_params)
	
	# loop through all algos
	for algo in algos:
		flip, reason = algo(stock, index, algo_params)
		stock['flip'] = flip
		if(flip != 0):
			trailing_tweak = 0
			return flip, reason

	return flip, reason
