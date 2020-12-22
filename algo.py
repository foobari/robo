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
	p['cci_up'] 	=   241 + (20 - random.random()*40)
	p['cci_down'] 	=  -214 + (20 - random.random()*40)
	p['target'] 	=    0.8 + (0.5 - random.random()*1.0)
	p['hard'] 	=  -(0.5 + (0.5 - random.random()*1.0))
	p['trailing'] 	=  -(0.5 + (0.5 - random.random()*1.0))
	p['cci_window'] =    20 + int(random.random()*30)
	print("randomized")
	return p

def init():
	algo_params = OrderedDict()
	algo_params['cci_up'] 		=  249
	algo_params['cci_down'] 	= -216
	algo_params['target'] 		=   0.71979  # target stop for dax to move +x %
	algo_params['hard'] 		=  -0.16027  # hard stop-loss if entry dax comes down x %
	algo_params['trailing'] 	=  -0.54079  # trailing stop-loss if in active position dax comes down x % from current top
	algo_params['cci_window'] 	=  28
	return algo_params



def get_backtest_params():
	# cci_up	cci_down target		hard		trailing 	cci_window
	backtest_params = (
	# promising after weekend (3d backtesting)
		(249,	-216, 	0.71979,	-0.16027,	-0.54079,	28), #1 +139e
		(249,	-216, 	0.71066,	-0.53953,	-0.36993,	28), #2 +137e
		(249,	-216, 	0.72151,	-0.76016,	-0.39281,	28), #3 +136e
		(249,	-216,	0.70481,	-0.29506,	-0.42720,	28),
		(249,	-216, 	0.71476,	-0.50027,	-0.70258,	28),
		(249,	-216, 	0.72118,	-0.63302,	-0.63115,	28),
		(249,	-216, 	0.71155,	-0.45638,	-0.58903,	28),
		(249,	-216, 	0.71017,	-0.51147,	-0.74067,	28),
		(249,	-216, 	0.72508,	-0.70280,	-0.71108,	28),
		(249,	-216, 	0.72593,	-0.74256,	-0.73300,	28),
		(249,	-216, 	0.72347,	-0.67583,	-0.49178,	28),
		(249,	-216, 	0.70587,	-0.67426,	-0.76074,	28),
		(249,	-216, 	0.71197,	-0.30263,	-0.71572,	28),
		(249,	-216, 	0.71238,	-0.58620,	-0.40590,	28),
		(249,	-216, 	0.70272,	-0.50986,	-0.61627,	28),

	)
	return backtest_params


def check_signals(stock, index, algo_params, is_last):
	SMA_SHORT = 200
	SMA_LONG =  1200

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
			stock['cci_last'] = (p_typ - float(p_sma[-1:])) / float(p_std[-1:]) / 0.015
			stock['cci_series'][index] = stock['cci_last']
			
			if(not stock['active_position'] and (stock['cci_last'] > algo_params['cci_up'])):
				flip = 1
			if(stock['active_position'] and (stock['cci_last'] < algo_params['cci_down'])):
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
			if(buy <= stock['trailing_stop_loss']):
				reason = "trailing_stop_loss"
				flip = -1

	# exit reach target
	if(True):
		if(stock['active_position']):
			target_price = ((1 + algo_params['target'] * stock['leverage'] / 100) * stock['last_buy'])
			if(sell >= target_price):
				reason = "target"
				flip = -1

	# exit day-end
	if(True):
		if(stock['active_position'] and is_last):
			reason = "day_close"
			flip = -1

	return flip, reason
