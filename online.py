from binance.client import Client
from binance.enums import *
from lxml import html
import numpy as np
import os
import math
import time
import json
import getopt
import sys
import algo

binance_client = []

def execute_buy_order_online(stock):
	global binance_client

	print("Execute buy order", stock['name'])

	if(stock['url'] == 'binance_api'):
		if(stock['name'] == "DOGEUSDT"):
			amount = stock['transaction_size']
			order = binance_client.order_market_buy(symbol='DOGEUSDT', quantity = amount)
			lot_price = float(order['cummulativeQuoteQty'])
			share_price = lot_price / amount
			print("setting:")
			stock['last_buy'] = share_price
			algo_params = algo.get_params()
			stock['target']             = ((1 + algo_params['target'] * stock['leverage'] / 100) * share_price)
			stock['trailing_stop_loss'] = ((1 + algo_params['trailing'] * stock['leverage'] / 100) * share_price)
			print("buy price", share_price)
			print("target", stock['target'])
			print("stoploss", stock['trailing_stop_loss'])
		else:
			print("not supported", stock['name'])


	
def execute_sell_order_online(stock):
	global binance_client
	
	print("Execute sell order", stock['name'])

	if(stock['url'] == 'binance_api'):
		if(stock['name'] == "DOGEUSDT"):
			amount = stock['transaction_size']
			order = binance_client.order_market_sell(symbol = 'DOGEUSDT', quantity = amount)
			print(order)
			lot_price = float(order['cummulativeQuoteQty'])
			share_price = lot_price / amount
			print("setting:")
			print("sell price", share_price)
		else:
			print("not supported", stock['name'])



def stock_sanity_check(stock, index):
	if((stock['buy_series'][-1] == 0)):
		print(stock['name'], "buy read zero, copy last")
		stock['valid'] = False
		if(index > 0):
			stock['buy_series'][-1]  = stock['buy_series'][-2]
	if((stock['sell_series'][-1] == 0)):
		stock['valid'] = False
		print(stock['name'], "sell read zero, copy last")
		if(index > 0):
			stock['sell_series'][-1] = stock['sell_series'][-2]
	if((stock['sell_series'][-1] - stock['buy_series'][-1]) > stock['spread']):
		stock['valid'] = False
		if(index > 0):
			print(stock['name'], "spread too big, copy last")
			stock['buy_series'][-1]  = stock['buy_series'][-2]
			stock['sell_series'][-1] = stock['sell_series'][-2]



def get_stock_values(stock, index, backtest_data=None):
	global binance_client

	stock['valid'] = True

	if(backtest_data == None):
		# Binance
		if(stock['url'] == 'binance_api'):
			trades = binance_client.get_aggregate_trades(symbol=stock['name'])
			buy  = float(trades[-1]['p'])
			# Use standard spread to simulate binance trading fees
			#spread = 1.0001
			spread = 1.002
			sell = buy * spread
			stock['buy_series'].append(buy)
			stock['sell_series'].append(sell)
	else:
		if(stock['type'] == 'long'):
			#if(index == 0 and (backtest_data[index][0] < 0.01 or backtest_data[index][1] < 0.01)):
			#	raise Exception("First value zero")
			stock['buy_series'].append(backtest_data[index][0])
			stock['sell_series'].append(backtest_data[index][1])
		if(stock['type'] == 'short'):
			#if(index == 0 and (backtest_data[index][2] < 0.01 or backtest_data[index][3] < 0.01)):
			#	raise Exception("First value zero")
			stock['buy_series'].append(backtest_data[index][2])
			stock['sell_series'].append(backtest_data[index][3])
	

def login(stock, creds):
	global binance_client

	if(stock['url'] == 'binance_api'):
		binance_client = Client(creds['api_key'], creds['api_secret'])

def logout(stock):
	if(stock['url'] != 'binance_api'):
		print("not supported", stock['url'])

def refresh(stock):
	if(stock['url'] != 'binance_api'):
		print("not supported", stock['url'])
