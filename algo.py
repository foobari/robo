from collections import OrderedDict
import random
import math
import numpy as np
import scipy

#from hurst import compute_Hc

def set_new_params(p, index):
	bp = get_backtest_params()
	p['cci_up'] 	= bp[index][0]
	p['cci_down'] 	= bp[index][1]
	p['target']	= bp[index][2]
	p['hard'] 	= bp[index][3]
	p['trailing'] 	= bp[index][4]
	p['cci_window']	= bp[index][5]
	p['sma_len']	= bp[index][6]
	p['rsi_len']	= bp[index][7]
	p['rsi_lim']	= bp[index][8]	
	print("parametrized set", index)
	return p

def randomize_params(p):
	#p['cci_up'] 	=  random.uniform( 165,  175)
	p['cci_down'] 	=  random.uniform(-162, -112)
	#p['target'] 	=  random.uniform( 0.675,  1.025)
	#p['hard'] 	=  random.uniform(-0.55, -0.35)
	#p['trailing'] 	=  random.uniform(-0.5, -0.4)
	p['cci_window'] =  int(random.uniform(46, 120))
	#p['sma_len'] 	=  int(random.uniform(181, 191))
	#p['rsi_len'] 	=  int(random.uniform(191, 201))
	#p['rsi_lim'] 	=  int(random.uniform(32, 46))

	print("randomized")
	return p

def init():
	p = set_new_params(OrderedDict(), 0)
	return p

def get_backtest_params():
	# 	cci_up   	cci_down 	target		hard		trailing 	cci_w	sma	rsi_len	rsi_lim
	backtest_params = (
		# 5d tests
		(170,		-147,		0.875,		-0.45000,	-0.6000,	 81,	186, 	196, 	34), # dive-in
		#(170,		-147,		0.97651,	-0.40920,	-0.40920,	 81,	186, 	196, 	34), # dive-in
		#(171.64886,	-146.34588,	0.97651,	-0.40920,	-0.40920,	 81,	186, 	196, 	34), # 
		#(168.59650,	-146.02200,	0.97651,	-0.40920,	-0.40920,	 81,	186, 	196, 	34), # rsitest
		#(171.64886,	-146.34588,	0.97651,	-0.40920,	-0.40920,	 80,	194, 	194, 	35), # rsitest
		#(171.64886,	-146.34588,	0.97651,	-0.40920,	-0.40920,	 80,	194, 	259, 	35), 
		#(100,		-100	,	0.97651,	-0.40950,	-0.34290,	 102,	102, 	102, 	5), # testing rsi+csi
	)
	return backtest_params

def check_signals(stock, index, algo_params, is_last, no_buy):
	SMA_SHORT = 40
	SMA_LONG = algo_params['sma_len']
	flip = 0
	reason = ""
	hh = 0
	H = 0

	RSI_WINDOW = algo_params['rsi_len']
	RSI_LIMIT  = algo_params['rsi_lim']
	
	buy  = float(stock['buy_series'][-1])
	sell = float(stock['sell_series'][-1])

	stock['sma_series_short'].append(np.mean(stock['buy_series'][-SMA_SHORT:]))
	stock['sma_series_long'].append(np.mean(stock['buy_series'][-SMA_LONG:]))

	
	# hurst exponent
	'''
	if(index > 100):
		H, c, val = compute_Hc(stock['buy_series'][-200:])
		if(H < 0.5):
			text = "Mean reverting"
		elif(H == 0.5):
			text = "Brownian motion"
		elif(H > 0.5):
			text = "Trending"
		print(text, "{:.4f}".format(H))
		stock['hurst'].append(H)
	else:
		stock['hurst'].append(0.5)
	'''

	# enter rsi 
	if(True and not is_last):
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

		if(index > RSI_WINDOW):
			if(stock['rsi_series'][-2] < RSI_LIMIT and stock['rsi_series'][-1] > RSI_LIMIT):
				flip = 1
				reason = 'rsi'


	# enter/exit cci + rsi
	if(True and not is_last):
		p_max = np.max(stock['sell_series'][-algo_params['cci_window']:])
		p_min = np.min(stock['sell_series'][-algo_params['cci_window']:])
		p_clo = sell
		p_typ = ((p_max + p_min + p_clo) / 3)
		stock['cci_ptyp'].append(p_typ)
		p_sma = np.mean(stock['cci_ptyp'][-algo_params['cci_window']:])
		p_std = np.std(stock['cci_ptyp'][-algo_params['cci_window']:])

		if(p_std != 0):
			stock['cci_series'].append((p_typ - p_sma) / p_std / 0.015)
			if(index > SMA_LONG):
				if(not stock['active_position']):
					if(stock['cci_series'][-2] < algo_params['cci_down'] and
					   stock['cci_series'][-1] >= algo_params['cci_down'] and
					   stock['rsi_series'][-1] > 50):
						if(buy > stock['sma_series_long'][-1]):
							reason = "cci_buy"
							flip = 1

				if(stock['active_position']):
					if(stock['cci_series'][-2] > algo_params['cci_up'] and
					   stock['cci_series'][-1] <= algo_params['cci_up'] and
					   stock['rsi_series'][-1] < 50):
						if(buy < float(stock['sma_series_long'][-1])):
							reason = "cci_sell"
							flip = -1
		else:
			stock['cci_series'].append(0)

	# exit hard stop-loss
	if(True):
		if(stock['active_position']):
			if(buy <= stock['hard_stop_loss']):
				reason = "hard_stop_loss"
				flip = -1
				
	# exit trailing stop-loss
	if(True):
		if(stock['active_position']):
			trailing = algo_params['trailing']
			target_price = ((1 + trailing * stock['leverage'] / 100) * stock['current_top'])
				
			if(buy >= stock['current_top']):
				stock['current_top'] = buy
				stock['trailing_stop_loss'] = target_price
			if(sell <= stock['trailing_stop_loss']):
				reason = "trailing_stop_loss"
				stock['reason'] = ""
				flip = -1

	# exit reach target
	if(True):
		if(stock['active_position']):
			target_price = ((1 + algo_params['target'] * stock['leverage'] / 100) * stock['last_buy'])
			if(buy >= target_price):
				reason = "target"
				flip = -1

	# exit day-end
	if(True):
		if(stock['active_position'] and is_last):
			reason = "day_close"
			flip = -1

	# "no buy" -zone in the evening
	if(no_buy and flip == 1):
		print(reason, "no buy zone")
		flip = 0

	return flip, reason
