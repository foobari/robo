# -*- coding: iso-8859-15 -*-
from collections import OrderedDict
import random
import math
import numpy as np
import scipy
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

p = {}

param_names = [ 'name',		#0
	        'cci_up',	#1
		'cci_down',	#2
		'target',	#3
		'hard',		#4
		'trailing',	#5
		'cci_window',	#6
		'sma_len',	#7
		'rsi_len',	#8
		'rsi_lim',	#9
		'cci_big',	#10
		'rsi_big']	#11

# optimizer window/step
optimizer_window_percentage_min =   5
optimizer_window_percentage_max =   5
optimizer_window_steps_min      =   50
optimizer_window_steps_max      =   50

# parameter list to optimize
#params_idx = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
#params_idx = [1, 2, 3, 4, 5, 9, 10, 11]
#params_idx = [8,9]
params_idx = [1,2,3,4,5,7,9]

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
	p['hard'] 	= bp[index][4]
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
	p['hard'] 	= -random.uniform(1, 3)
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
		#optimizer_steps   = 50
		print("Randomized window: ±", optimizer_window, "%, steps: ", optimizer_steps+1)

	# If param optimizing run is done, change to optimal value, move to next
	if(optimizer_runs == (optimizer_steps+1)):
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

	start_time = time.time()
	random.seed()

	techs = [calc_sma,
		 calc_rsi,
		 calc_cci,
		 #calc_pivots,
		 #calc_bb,
		 #calc_kc,
		 #calc_peaks,
		 #calc_macd,
		 #calc_stochastic,
		]

	algos = [#algo_rsi_trigger,
		 algo_cci_trigger,
		 #algo_pivots,
		 #algo_bb,
		 #algo_squeeze_trigger,
		 #algo_sto_macd_trigger,
		 #algo_bias,
		 #algo_higher_highs,
		 #algo_macd,
		 algo_hard_stoploss,
		 algo_trailing_stoploss,
		 algo_reach_target,
		]
	
	return techs, algos

# winner scan: cat testrun_dax1 | grep days -A6
def get_algo_params():
	# 	cci_up	    cci_down    target    hard   trailing    cci_w    sma_len    rsi_len    rsi_lim    cci_big    rsi_big
	algo_params = (
	#('dax',   999.999,  -140.598,    0.969, -0.780,    -0.677,      81,       104,       188,    28.650,   238.655,    39.745), # dax.65
	#('doge',   179.884,  -254.743,    2.120, -2.202,    -3.156,      69,       183,       337,    44.780,   133.456,    39.693), # doge.50
	('doge',   204.318,  -132.394,    2.595, -2.351,    -2.679,      68,       121,       178,    51.098,   133.456,    39.693), # dogetest
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
			    #stock['rsi_series'][-1] > 50.888):
			    stock['rsi_series'][-1] > algo_params['rsi_lim']):
				if(buy > stock['sma_series_long'][-1]):
					reason = "cci_buy"
					flip = 1

		if(stock['active_position']):
			if((stock['cci_series'][-2] > algo_params['cci_up']) and (stock['cci_series'][-1] <= algo_params['cci_up'])):
				if(buy < float(stock['sma_series_long'][-1])):
					reason = "cci_sell"
					flip = -1
		# remove for now
		#if(not stock['active_position'] and not stock['no_buy']):
		#	if(stock['cci_series'][-1] < -algo_params['cci_big'] and stock['rsi_series'][-1] < algo_params['rsi_big']):
		#			reason = "cci_big"
		#			flip = 1

		'''
		if(stock['active_position']):
			if(stock['cci_series'][-1] > algo_params['cci_big'] and stock['rsi_series'][-1] > (100 - algo_params['rsi_big'])):
				reason = "cci_big"
				flip = -1


		if(stock['cci_series'][-2] < -algo_params['cci_big'] and stock['cci_series'][-1] > -algo_params['cci_big'] and
			stock['rsi_series'][-1] < algo_params['rsi_big']):
			reason = "cci_big"
			flip = 1
		'''
	return flip, reason

'''
def algo_pivots(stock, index, algo_params):
	flip = 0
	reason = ""
	buy  = float(stock['buy_series'][-1])

	if(index > PIVOT_WIN):
		
		if(stock['active_position']):
			pp_idx = 0
			for i in (stock['pivots'][-1]):
				if(stock['last_buy'] > i):
					break
				pp_idx += 1
			
			
			if(pp_idx < 7):
				to_upper = stock['pivots'][-1][pp_idx - 1] - stock['last_buy']
				to_lower = stock['last_buy'] - stock['pivots'][-1][pp_idx]
				
				if(stock['target'] != stock['pivots'][-1][pp_idx - 3]):
					stock['target'] = stock['pivots'][-1][pp_idx - 3]
					print "new target", stock['target']



		# break level up
		for i in (stock['pivots'][-1][5], stock['pivots'][-1][6]):
			if(stock['buy_series'][-2] < i and stock['buy_series'][-1] > i):
				flip = 1
				#stock['signals_list_buy'].append((index, stock['sell_series'][-1]))

		# break level down
		for i in (stock['pivots'][-1][0], stock['pivots'][-1][1], stock['pivots'][-1][2]):
			if(stock['buy_series'][-2] > i and stock['buy_series'][-1] < i):
				flip = -1
				#stock['signals_list_sell'].append((index, stock['sell_series'][-1]))

	return flip, reason
'''	

def algo_rsi_trigger(stock, index, algo_params):
	flip = 0
	reason = ""
	RSI_LIMIT  = algo_params['rsi_lim']
	RSI_WINDOW = algo_params['rsi_len']

	if(index > RSI_WINDOW):
		if(not stock['active_position'] and not stock['no_buy']):
			if(stock['rsi_series'][-2] < RSI_LIMIT and stock['rsi_series'][-1] > RSI_LIMIT):
					flip = 1
					reason = 'rsi'
		
		'''
		# Makes slightly worse
		if(stock['active_position'] and stock['rsi_series'][-2] > (100 - RSI_LIMIT) and stock['rsi_series'][-1] < (100 - RSI_LIMIT)):
			flip = -1
			reason = 'rsi'
		'''
	return flip, reason



'''
def algo_bb(stock, index, algo_params):
	flip = 0
	reason = ""

	buy  = float(stock['buy_series'][-1])

	if(not stock['active_position']):
		if(buy < stock['bb_lower'][-1]):
			reason = "bb"
			flip = 1

	if(stock['active_position']):
		if(buy > stock['bb_upper'][-1]):
			reason = "bb"
			flip = -1

	return flip, reason
'''

def algo_hard_stoploss(stock, index, algo_params):
	flip = 0
	reason = ""
	buy  = float(stock['buy_series'][-1])
	sell = float(stock['sell_series'][-1])

	if(stock['active_position']):
		if(sell <= stock['hard_stop_loss']):
			reason = "hard_stop_loss"
			flip = -1
	return flip, reason


def algo_trailing_stoploss(stock, index, algo_params):
	flip = 0
	reason = ""
	buy  = float(stock['buy_series'][-1])
	sell = float(stock['sell_series'][-1])

	if(stock['active_position']):
		trailing = algo_params['trailing']
		target_price = ((1 + float(trailing) * stock['leverage'] / 100) * stock['current_top'])
			
		if(buy >= stock['current_top']):
			stock['current_top'] = buy
			stock['trailing_stop_loss'] = target_price
		if(sell <= stock['trailing_stop_loss']):
			reason = "trailing_stop_loss"
			flip = -1

	return flip, reason


def algo_reach_target(stock, index, algo_params):
	flip = 0
	reason = ""
	buy  = float(stock['buy_series'][-1])
	
	if(stock['active_position']):
		if(buy >= stock['target']):
			reason = "target"
			flip = -1

	return flip, reason
'''
def algo_higher_highs(stock, index, algo_params):
	flip = 0
	reason = ""
	SMA_LONG = algo_params['sma_len']
	PEAK_COUNT = 4
	PEAK_WINDOW = 10

	buy  = float(stock['buy_series'][-1])
	
	hh_count = stock['hh'][-PEAK_WINDOW:].count(1)
	stock['hh_sma'].append(hh_count)
	if(hh_count >= PEAK_COUNT):
		if(index > SMA_LONG):
			flip = -1
			reason = 'hh'
	

	return flip, reason

def algo_macd(stock, index, algo_params):
	flip = 0
	reason = ""

	SMA_LONG = algo_params['sma_len']

	if(index > SMA_LONG):
		if((stock['macd_signal'][-2] > stock['macd_line'][-2]) and
		(stock['macd_signal'][-1] < stock['macd_line'][-1])):
			flip = 1
			reason = "macd"

		if(stock['active_position']):
			if((stock['macd_signal'][-2] < stock['macd_line'][-2]) and
			(stock['macd_signal'][-1] > stock['macd_line'][-1])):
				flip = -1
				reason = "macd"

	return flip, reason

def algo_bias(stock, index, algo_params):
	flip = 0
	reason = ""

	bias = 0

	if(index > 0):
		
		if(stock['buy_series'][-1] > stock['sma_series_short'][-1]):
			bias += 1
		else:
			bias -= 1

		if(stock['buy_series'][-1] > np.max(stock['buy_series'][-10:-2])):
			bias += 1
		else:
			bias -= 1

		if(stock['buy_series'][-1] > stock['buy_series'][-2] and
			stock['buy_series'][-2] > stock['buy_series'][-3] ):
			bias += 1
		elif(stock['buy_series'][-1] < stock['buy_series'][-2] and
			stock['buy_series'][-2] < stock['buy_series'][-3] ):
			bias -= 1
		
		if(stock['rsi_series'][-1] > 50):
			bias += 1
		else:
			bias -= 1
		
		
		if((stock['cci_series'][-2] < algo_params['cci_down']) and (stock['cci_series'][-1] >= algo_params['cci_down'])):
			bias += 1
		elif((stock['cci_series'][-2] > algo_params['cci_up']) and (stock['cci_series'][-1] <= algo_params['cci_up'])):
			bias -= 1
		
		if((stock['cci_series'][-1] > algo_params['cci_up'])):
			bias += 1
		elif((stock['cci_series'][-1] < algo_params['cci_down'])):
			bias -= 1

		stock['bias'].append(bias)
		stock['bias_sma'].append(np.mean(stock['bias'][-10:]))

	if(index > 100):
		if(stock['bias_sma'] >= 1):
			flip = 1
			reason = "bias"

	return flip, reason


def algo_squeeze_trigger(stock, index, algo_params):
	flip = 0
	reason = ""

	sqz_on  = True
	squeeze = 0
	
	#value = (Highest[lengthKC](high)+Lowest[lengthKC](low)+average[lengthKC](close))/3
	#val = linearregression[lengthKC](close-value)
 
	#if(stock['bb_lower'][-1] > stock['kc_lower'][-1] and
	#   stock['bb_upper'][-1] < stock['kc_upper'][-1]):
	#	sqz_on = True

	if(stock['bb_lower'][-1] < stock['kc_lower'][-1] and
	   stock['bb_upper'][-1] > stock['kc_upper'][-1]):
	   	sqz_on = False
	
	val = stock['buy_series'][-1] - stock['kc_typ'][-1]

	if(sqz_on):
		squeeze = 0
	else:
		squeeze = val

	squeeze = stock['bb_lower'][-1] - stock['kc_lower'][-1]
	stock['squeeze'].append(squeeze)
	
	
	if(index > 200):
		if(stock['squeeze'][-2] > 0.2 and stock['squeeze'][-1] < 0.2):
			flip = 1
			reason = "squeeze"
		elif(stock['squeeze'][-2] > 0.05 and stock['squeeze'][-1] < 0.05):
			flip = -1
			reason = "squeeze"
	
	return flip, reason

def algo_sto_macd_trigger(stock, index, algo_params):
	flip = 0
	bias = 0
	reason = ""

	if(index > 400):
	#Generally, if the %K value rises above the %D, then a buy signal is indicated by this crossover,
	#provided the values are under 80. If they are above this value, the security is considered overbought.
		
		if(stock['stochastic_k'][-2] < stock['stochastic_d'][-2] and
		   stock['stochastic_k'][-1] > stock['stochastic_d'][-1] and
		   stock['stochastic_k'][-1] > 80 and stock['stochastic_d'][-1] > 80):
			flip = 1

	
		if(stock['stochastic_k'][-2] > stock['stochastic_d'][-2] and
		   stock['stochastic_k'][-1] < stock['stochastic_d'][-1]):
			bias -= 1

		#Common triggers occur when the %K line drops below 20, the stock is considered oversold, and it is a buying signal.	
		if(stock['stochastic_k'][-1] < 20):
			bias += 1

		#Common triggers occur when the %K line drops below 20, the stock is considered oversold, and it is a buying signal.	
		if(stock['stochastic_k'][-1] > 80):
			bias -= 1

		#If the %K peaks just below 100 and heads downward, the stock should be sold before that value drops below 80
		if(stock['stochastic_k'][-2] > 99 and
		stock['stochastic_k'][-1] < 99):
			bias -= 1

		if(stock['stochastic_k'][-2] < 1 and
		stock['stochastic_k'][-1] > 1):
			bias += 1
	
		# In the case of a bullish MACD, this will occur when the histogram value is above the equilibrium line,
		# and also when the MACD line is of greater value than the nine-day EMA, also called the "MACD signal line."


	return flip, reason

def calc_hurst_exponent(stock, index, algo_params):
	hh = 0
	H = 0

	if(index > 100):
		H, c, val = compute_Hc(stock['buy_series'][-100:])
		stock['hurst'].append(H)
	else:
		stock['hurst'].append(0.5)
	
	stock['hurst_sma'].append(np.mean(stock['hurst'][-20:]))
	return 0, ''
'''

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
'''
def calc_peaks(stock, index, algo_params):
	PEAK_WINDOW = 110
	buy = stock['buy_series'][-1]
	if(index > 200):
		window = stock['buy_series'][-PEAK_WINDOW:-1]
		max = np.max(window)
		min = np.min(window)
		stock['win_max'] = max
		stock['win_min'] = min
		if(buy > max):
			stock['hh'].append(1)
		else:
			stock['hh'].append(0)
	
def calc_macd(stock, index, algo_params):
	mul = 10
	
	window = 26 * mul
	values = stock['buy_series'][-window:]
	weights = np.exp(np.linspace(-1., 0., window))
	weights /= weights.sum()
	a = np.convolve(values, weights, mode='full')[:len(values)]

	window = 12 * mul
	values = stock['buy_series'][-window:]
	weights = np.exp(np.linspace(-1., 0., window))
	weights /= weights.sum()
	b = np.convolve(values, weights, mode='full')[:len(values)]

	c = b[-1] - a[-1]
	stock['macd_line'].append(c)
	
	window = 9 * mul
	values = stock['macd_line'][-window:]
	weights = np.exp(np.linspace(-1., 0., window))
	weights /= weights.sum()
	d = np.convolve(values, weights, mode='full')[:len(values)]
	
	stock['macd_signal'].append(d[-1])
	stock['macd_histogram'].append(c-d[-1])


def calc_stochastic(stock, index, algo_params):
	mul = 20

	window_l  = 14 * mul
	window_s =  3 * mul

	close = stock['buy_series'][-1]
	low_long   = np.min(stock['buy_series'][-window_l:])
	high_long  = np.max(stock['buy_series'][-window_l:])

	k = 100 * (close - low_long) / (high_long - low_long)
	
	stock['stochastic_k'].append(k)
	
	d = np.mean(stock['stochastic_k'][-window_s:])
	
	stock['stochastic_d'].append(d)

def calc_bb(stock, index, algo_params):
	length = 15
	mult = 0.5
 
	basis = np.mean(stock['buy_series'][-length:])
	dev = mult * np.std(stock['buy_series'][-length:])
	
	stock['bb_upper'].append(basis + dev)
	stock['bb_lower'].append(basis - dev)

def calc_kc(stock, index, algo_params):
	length = 20
	mult = 1
	
	if(index > length):
		r1 = np.max(stock['buy_series'][-length:]) - np.min(stock['buy_series'][-length:])
		r2 = abs(np.max(stock['buy_series'][-length:]) - np.max(stock['buy_series'][-length - 1]))
		r3 = abs(np.min(stock['buy_series'][-length:]) - np.max(stock['buy_series'][-length - 1]))

		stock['tr'].append(np.max((r1, r2, r3)))
	else:
		stock['tr'].append(np.max(stock['buy_series'][-length:]) - np.min(stock['buy_series'][-length:]))


	typical = (np.max(stock['buy_series'][-length:]) + np.min(stock['buy_series'][-length:]) + stock['buy_series'][-1]) / 3
	stock['kc_typ'].append(typical) 
	stock['kc_upper'].append(typical + (mult * stock['tr'][-1]))
	stock['kc_lower'].append(typical - (mult * stock['tr'][-1]))
'''
'''
def calc_pivots(stock, index, algo_params):
	length = PIVOT_WIN
	
	#if(index >= length):

	if(index % length == 0):
		series_high  = np.max(stock['buy_series'][-length:])
		series_low   = np.min(stock['buy_series'][-length:])
		series_close = stock['buy_series'][-1]
		pp = (series_high + series_low + series_close) / 3
		r1 = 2 * pp - series_low
		r2 = pp + (series_high - series_low)
		r3 = series_high + 2 * (pp - series_low)
		s1 = 2 *pp - series_high
		s2 = pp - (series_high - series_low)
		s3 = series_low - 2 * (series_high - pp)
		stock['pivots'].append((r3,r2,r1,pp,s1,s2,s3))
	else:
		stock['pivots'].append((stock['pivots'][-1]))

	# sliding pivots 
	series_high  = np.max(stock['buy_series'][-length:])
	series_low   = np.min(stock['buy_series'][-length:])
	series_close = stock['buy_series'][-1]
	pp = (series_high + series_low + series_close) / 3
	r1 = 2 * pp - series_low
	r2 = pp + (series_high - series_low)
	r3 = series_high + 2 * (pp - series_low)
	s1 = 2 *pp - series_high
	s2 = pp - (series_high - series_low)
	s3 = series_low - 2 * (series_high - pp)
	stock['pivots'].append((r3,r2,r1,pp,s1,s2,s3))

	#else:
	#	p = stock['buy_series'][-1]
	#	stock['pivots'].append((p,p,p,p,p,p,p))
'''


def check_signals(stock, index, algo_params):
	global algos

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
			return flip, reason

	return flip, reason
