from collections import OrderedDict
import random

def set_new_params(p, index):
	bp = get_backtest_params()
	p['cci_up'] 	= bp[index][0]
	p['cci_down'] 	= bp[index][1]
	p['target']	= bp[index][2]
	p['hard'] 	= bp[index][3]
	p['trailing'] 	= bp[index][4]
	p['cci_window']	= bp[index][5]
	print("parametrized set", index)
	return p

def randomize_params(p):
	p['cci_up'] 	=  random.uniform(284-10, 284+10)
	p['cci_down'] 	=  random.uniform(-124-10, -124+10)
	p['target'] 	=  random.uniform(0.979-0.10, 0.979+0.10)
	p['hard'] 	=  random.uniform(-0.416-0.10, -0.416+0.10)
	p['trailing'] 	=  random.uniform(-0.557-0.10, -0.557+0.10)
	p['cci_window'] =  int(random.uniform(90, 110))
	print("randomized")
	return p

def init():
	p = OrderedDict()
	p['cci_up'] 	=  284.568471
	p['cci_down'] 	= -124.732507
	p['target'] 	=   0.979095  # target stop for dax to move +x %
	p['hard'] 	=  -0.416562 #-0.16027  # hard stop-loss if entry dax comes down x %
	p['trailing'] 	=  -0.557422  # trailing stop-loss if in active position dax comes down x % from current top
	p['cci_window'] =  100
	return p



def get_backtest_params():
	# 	cci_up   	cci_down 	target		hard		trailing 	cci_window
	backtest_params = (
		# 5d tests
		(293.421375,	-120.987870,	1.052508,	-0.338324,	-0.470415,	101), #v0.1.1 5d sharpe = 1.79 / 7.52%
		(284.568471,	-124.732507,	0.979095,	-0.416562,	-0.557422,	100), #v0.1.0 5d sharpe = 1.78 / 7.25%
		(286.271007,	-141.609216,	1.150073,	-0.396210,	-0.506074,	100), #       5d sharpe = 1.97
		(212.259167,	-255.610183,	0.843542,	-0.686087,	-0.400189,	242), #       5d sharpe = 1.42 / 237e

	)
	return backtest_params

def check_signals(stock, index, algo_params, is_last):
	SMA_SHORT = 40
	SMA_LONG =  200

	flip = 0

	buy  = float(stock['buy_series'][-1:])
	sell = float(stock['sell_series'][-1:])

	stock['sma_series_short'] = stock['buy_series'].rolling(SMA_SHORT, min_periods=0).mean()
	stock['sma_series_long']  = stock['buy_series'].rolling(SMA_LONG,  min_periods=0).mean()

	reason = ""

	# enter/exit cci
	if(True):
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
			
			if(not stock['active_position'] and (stock['cci_last'] > algo_params['cci_up'])):
				flip = 1
			if(stock['active_position'] and (stock['cci_last'] < algo_params['cci_down']) and buy > stock['last_buy']):
			#if(stock['active_position'] and (stock['cci_last'] < algo_params['cci_down'])):
				reason = "cci_down"
				flip = -1

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
