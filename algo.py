from collections import OrderedDict
import random
import math
import numpy as np
import scipy

def set_new_params(p, index):
	bp = get_backtest_params()
	p['cci_up'] 	= bp[index][0]
	p['cci_down'] 	= bp[index][1]
	p['target']	= bp[index][2]
	p['hard'] 	= bp[index][3]
	p['trailing'] 	= bp[index][4]
	p['cci_window']	= bp[index][5]
	p['sma_len']	= bp[index][6]
	print("parametrized set", index)
	return p

def randomize_params(p):
	#p['cci_up'] 	=  random.uniform( 196.5,  198.5)
	#p['cci_down'] 	=  random.uniform(-180.8, -178.8)
	#p['target'] 	=  random.uniform( 0.90,  2.00)
	p['hard'] 	=  random.uniform(-1.0, -0.01)
	#p['trailing'] 	=  random.uniform(-0.73, -0.53)
	#p['cci_window'] =  int(random.uniform(80, 86))
	#p['sma_len'] 	=  int(random.uniform(190, 210)) #200
	print("randomized")
	return p

def init():
	p = set_new_params(OrderedDict(), 0)
	return p


def get_backtest_params():
	# 	cci_up   	cci_down 	target		hard		trailing 	cci_w	sma_len
	backtest_params = (
		# 5d tests
		(181.53411,	-155.60905,	0.97391,	-0.46445,	-0.35692,	 78,	195), # after testrun1 / target opt. sh=2.52 / 6.04%
		(181.53411,	-155.60905,	0.78219,	-0.46445,	-0.35692,	 78,	195), # after testrun1 sh=2.27 / 5.59%
		(197.54381,	-179.85561,	0.52458,	-0.43402,	-0.63594,	 83,	209), # after testrun2 sh=2.70 / 3.55%
		(198.72637,	-176.73968,	0.43072,	-0.46735,	-0.63427,	 87,	200), # 8d sh=2.96 / 3.19%/d
		(180.26122,	-153.15132,	0.88069,	-0.47235,	-0.28211,	 81,	202), # 8d sh=1.63 / 5.34%/d
		#(202.0436609,	-167.130678,	0.518,		-0.407697,	-0.611367,	 85,	200), #v0.2.0 sharpe = 2.14 / +3.2%d
		#(179.5546800,	-162.723594,	0.8,		-0.4,		-0.5,		 82,	200), #v0.2.0 new_cci, sharpe = 1.88
		#(100,		-100,		0.8,		-0.4,		-0.5,		 40), #modified cci test
		#(284.568471,	-124.732507,	0.979095,	-0.416562,	-0.557422,	100), #v0.1.0 5d sharpe = 1.78 / 7.25%
		#(293.421375,	-120.987870,	1.052508,	-0.338324,	-0.470415,	101), #v0.1.1 5d sharpe = 1.79 / 7.52%
		#(286.271007,	-141.609216,	1.150073,	-0.396210,	-0.506074,	100), #       5d sharpe = 1.97
		#(212.259167,	-255.610183,	0.843542,	-0.686087,	-0.400189,	242), #       5d sharpe = 1.42 / 237e
	)
	return backtest_params

def check_signals(stock, index, algo_params, is_last):
	SMA_SHORT = 40
	SMA_LONG = algo_params['sma_len']

	flip = 0
	reason = ""

	buy  = float(stock['buy_series'][-1:])
	sell = float(stock['sell_series'][-1:])

	stock['sma_series_short'] = stock['buy_series'].rolling(SMA_SHORT, min_periods=0).mean()
	stock['sma_series_long']  = stock['buy_series'].rolling(SMA_LONG,  min_periods=0).mean()

	# enter/exit cci
	if(True and not is_last):
		p_max = (float(stock['sell_series'][-algo_params['cci_window']:-1].max()))
		p_min = (float(stock['sell_series'][-algo_params['cci_window']:-1].min()))
		p_clo = (float(stock['sell_series'][-1:]))
		p_typ = ((p_max + p_min + p_clo) / 3)
		stock['cci_ptyp'][index] = p_typ
		p_sma = stock['cci_ptyp'].rolling(algo_params['cci_window'], min_periods=0).mean()
		p_std = stock['cci_ptyp'].rolling(algo_params['cci_window'], min_periods=0).std()

		if(float(p_std[-1:]) != 0):
			sma = float(p_sma[-1:])
			std = float(p_std[-1:])
			stock['cci_last'] = (p_typ - sma) / std / 0.015
			stock['cci_series'][index] = stock['cci_last']
			
			if(index > SMA_SHORT):
				if(not stock['active_position']):
					if(buy > float(stock['sma_series_long'][-1:]) and
					   stock['cci_series'][index-1] < algo_params['cci_down'] and
					   stock['cci_series'][index] >= algo_params['cci_down']):
						reason = "cci_buy"
						flip = 1

				if(stock['active_position']):
					if(buy < float(stock['sma_series_long'][-1:]) and
					   stock['cci_series'][index-1] > algo_params['cci_up'] and
					   stock['cci_series'][index] <= algo_params['cci_up']):
						reason = "cci_sell"
						flip = -1

				# blips
				'''
				if(buy > float(stock['sma_series_short'][-1:]) and
					stock['cci_series'][index-1] < algo_params['cci_down'] and  stock['cci_series'][index] >= algo_params['cci_down']):
						print("blip up", sell)
						stock['signals_list_buy'].append((index, float(stock['sell_series'][-1:])))
				if(buy < float(stock['sma_series_short'][-1:]) and
					stock['cci_series'][index-1] > algo_params['cci_up'] and stock['cci_series'][index] <= algo_params['cci_up']):
						print("blip down", buy)
						stock['signals_list_sell'].append((index, float(stock['buy_series'][-1:])))
				'''
		else:
			stock['cci_series'][index] = stock['cci_series'][index-1]
		


	# exit SMA flips
	if(False):
		if(float(stock['sma_series_short'][-1:]) > float(stock['sma_series_long'][-1:])):
			#if(stock['dir'] <= 0):
			#	print("SMA_FLIP up", stock['name'], "could buy now", sell)
			stock['dir'] = 1
		else:
			if(stock['dir'] > 0):
				#print("SMA_FLIP down", stock['name'], "could sell now", buy)
				reason = "sma_flip_down"
				flip = -1
			stock['dir'] = -1

	# exit hard stop-loss
	if(True):
		if(stock['active_position']):
			if(buy <= stock['hard_stop_loss']):
				reason = "hard_stop_loss"
				flip = -1
				
	# exit trailing stop-loss
	if(True):
		if(stock['active_position']):
			target_price = ((1 + algo_params['trailing'] * stock['leverage'] / 100) * stock['current_top'])
			if(buy >= stock['current_top']):
				stock['current_top'] = buy
				stock['trailing_stop_loss'] = target_price
			if(sell <= stock['trailing_stop_loss']):
				reason = "trailing_stop_loss"
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

	return flip, reason
