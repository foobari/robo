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


def randomize_params(p):
	#p['cci_up'] 	=   241 + (10 - random.random()*20)
	#p['cci_down'] 	=  -214 + (10 - random.random()*20)
	p['target'] 	=   0.9919 + (0.5 - random.random()*1.0)
	p['hard'] 	=  -(0.4 + (0.4 - random.random()*0.8))
	p['trailing'] 	=  -(0.4 + (0.4 - random.random()*0.8))
	#p['cci_window'] =    20 + int(random.random()*30)

	print("randomized", p)

def init():
	# default params, #1 so far
	algo_params = OrderedDict()
	algo_params['cci_up'] 		=  249
	algo_params['cci_down'] 	= -216
	algo_params['target'] 		=   0.70481  # target stop for dax to move +x %
	algo_params['hard'] 		=  -0.29506  # hard stop-loss if entry dax comes down x %
	algo_params['trailing'] 	=  -0.42720  # trailing stop-loss if in active position dax comes down x % from current top
	algo_params['cci_window'] 	=  28
	return algo_params



def get_backtest_params():
	# cci_up		cci_down		target			hard		trailing 	cci_windows
	backtest_params = (
	(249.50256140567475,	-216.03885069653387,	0.9919496922293249,	-0.4330237918474565, -0.3886362997089748, 28),	# +52e 2d wow
#	(150,			-300,			0.3584086017,		-0.332201008,	-0.4917583083,	40),	# +14e, statisticically from 2d, only 1 closed deal
#	(262.6280835539,	-135.7762585974,	0.3584086017,		-0.332201008,	-0.4917583083,	446),	# +14e, statisticically from 2d, only 1 closed deal
#	(182,			-148,			0.492436,		-0.155745,	-0.173158,	346), 	# -17e  1d
	)
# promising after weekend (2d backtesting)
#64	'cci_up'	249	'cci_down'	-216	'target'	0.70481	'hard'	-0.29506	'trailing'	-0.42720	'cci_window'	28
#64	'cci_up'	249	'cci_down'	-216	'target'	0.71476	'hard'	-0.50027	'trailing'	-0.70258	'cci_window'	28
#64	'cci_up'	249	'cci_down'	-216	'target'	0.72118	'hard'	-0.63302	'trailing'	-0.63115	'cci_window'	28
#64	'cci_up'	249	'cci_down'	-216	'target'	0.71155	'hard'	-0.45638	'trailing'	-0.58903	'cci_window'	28
#64	'cci_up'	249	'cci_down'	-216	'target'	0.71017	'hard'	-0.51147	'trailing'	-0.74067	'cci_window'	28
#64	'cci_up'	249	'cci_down'	-216	'target'	0.72508	'hard'	-0.70280	'trailing'	-0.71108	'cci_window'	28
#64	'cci_up'	249	'cci_down'	-216	'target'	0.72593	'hard'	-0.74256	'trailing'	-0.73300	'cci_window'	28
#64	'cci_up'	249	'cci_down'	-216	'target'	0.72347	'hard'	-0.67583	'trailing'	-0.49178	'cci_window'	28
#64	'cci_up'	249	'cci_down'	-216	'target'	0.72151	'hard'	-0.76016	'trailing'	-0.39281	'cci_window'	28
#64	'cci_up'	249	'cci_down'	-216	'target'	0.71979	'hard'	-0.16027	'trailing'	-0.54079	'cci_window'	28
#64	'cci_up'	249	'cci_down'	-216	'target'	0.70587	'hard'	-0.67426	'trailing'	-0.76074	'cci_window'	28
#64	'cci_up'	249	'cci_down'	-216	'target'	0.71197	'hard'	-0.30263	'trailing'	-0.71572	'cci_window'	28
#64	'cci_up'	249	'cci_down'	-216	'target'	0.71238	'hard'	-0.58620	'trailing'	-0.40590	'cci_window'	28
#64	'cci_up'	249	'cci_down'	-216	'target'	0.70272	'hard'	-0.50986	'trailing'	-0.61627	'cci_window'	28
#64	'cci_up'	249	'cci_down'	-216	'target'	0.71066	'hard'	-0.53953	'trailing'	-0.36993	'cci_window'	28
#('total', 54.0, OrderedDict([('cci_up', 249), 		      ('cci_down', -216),                ('target', 0.621229524286191),  ('hard', -0.21450886251843937), ('trailing', -0.443139037641552),  ('cci_window', 28)])) 5+5 deals
#('total', 53.0, OrderedDict([('cci_up', 249), 		      ('cci_down', -216), 		 ('target', 0.5976852816940262), ('hard', -0.7329437931794475),  ('trailing', -0.33393069453857155),('cci_window', 28)])) 5+5 deals
#('total', 52.0, OrderedDict([('cci_up', 249.50256140567475), ('cci_down', -216.03885069653387), ('target', 0.9919496922293249), ('hard', -0.4330237918474565),  ('trailing', -0.3886362997089748), ('cci_window', 28)])) 2d wow
#('total', 52.0, OrderedDict([('cci_up', 249), 		      ('cci_down', -216), 		 ('target', 0.9525734349965086), ('hard', -0.41268294579956377), ('trailing', -0.3871192691491473), ('cci_window', 28)])) 4+4 deals
#('total', 52.0, OrderedDict([('cci_up', 249), 		      ('cci_down', -216), 		 ('target', 1.1996799230193091), ('hard', -0.18900600087327435), ('trailing', -0.7386388806755458), ('cci_window', 28)]))

#('total', 36.0, OrderedDict([('cci_up', 249), 		      ('cci_down', -216), 	         ('target', 0.6076674635547948), ('hard', -0.20477535697520755), ('trailing', -0.217476913312031),  ('cci_window', 28)]))
#('total', 34.0, OrderedDict([('cci_up', 249), 		      ('cci_down', -216), 		 ('target', 0.757949942126881),  ('hard', -0.33157030017385786), ('trailing', -0.1769790670131084), ('cci_window', 28)]))
#('total', 46.0, OrderedDict([('cci_up', 241.13982757351428), ('cci_down', -214.73172261066048), ('target', 1.181251961302452),  ('hard', -0.1697423870617957), ('trailing', -0.4961019880632199), ('cci_window', 28)])) 2d wow!
#('total', 42.0, OrderedDict([('cci_up', 234.73374002476442), ('cci_down', -215.77209446238564), ('target', 1.186686667883335),  ('hard', -0.3305816786246104), ('trailing', -0.4280666875898905), ('cci_window', 28)]))

#('total', 26.0, OrderedDict([('cci_up', 307.07888393376334), ('cci_down', -422.44291512542344), ('target', 0.5815241062161417), ('hard', -1.034611870674152), ('trailing', -0.10346339274809371), ('cci_window', 356)]))
#('total', 10.0, OrderedDict([('cci_up', 243.9818033384035),  ('cci_down', -404.5615585477548),  ('target', 0.6718226869273493), ('hard', -0.8412898130110619), ('trailing', -1.0513628987412271), ('cci_window', 50)]))
#('total', 46.0, OrderedDict([('cci_up', 224.1187499291742),  ('cci_down', -355.1983499213747),  ('target', 0.3124042963465917), ('hard', -0.9969613503655007), ('trailing', -0.9123952048101441), ('cci_window', 506)])) ?

	return backtest_params


def check_signals(stock, index, algo_params):
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
			stock['cci_series'][index] = stock['cci_last'] - algo_params['cci_up']
			
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

	return flip, reason
