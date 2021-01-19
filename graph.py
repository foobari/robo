import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
#import pandas_datareader as web
import numpy as np
import math
import os,glob
import pdb

import algo

fig = plt.figure(figsize=(12,10))
ax1 = fig.add_subplot(411)
ax2 = fig.add_subplot(412)
ax3 = fig.add_subplot(413)
ax4 = fig.add_subplot(414)


def draw_stocks(stock):
	global ax1, ax2
	if(stock['type'] == "long"):
		ax = ax1
	if(stock['type'] == "short"):
		ax = ax2

	ax.clear()
	if(len(stock['signals_list_sell'])):
		x_val = [x[0] for x in stock['signals_list_sell']]
		y_val = [x[1] for x in stock['signals_list_sell']]
		ax.plot(x_val, y_val, 'rv')

	if(len(stock['signals_list_buy'])):
		x_val = [x[0] for x in stock['signals_list_buy']]
		y_val = [x[1] for x in stock['signals_list_buy']]
		ax.plot(x_val, y_val, 'g^')


	if(stock['type'] == 'long'):
		color = 'olivedrab'
	else:
		color = 'steelblue'
	ax.plot(stock['buy_series'], color = color, label = stock["name"])
	ax.plot(stock['sma_series_short'], label = "SMA_short", linestyle=':')
	ax.plot(stock['sma_series_long'],  label = "SMA_long", linestyle=':')
	ax.legend(loc="upper left")

def draw_cci(lng, shrt):
	global ax3

	bp = algo.get_backtest_params()
	cci_u = bp[0][0]
	cci_d = bp[0][1]

	ax3.clear()
	ax3.set(ylim=(-250, 250))
	ax3.axhline(y=  cci_u, color='red', label = "cci up", linestyle='dotted')
	ax3.axhline(y=  cci_d, color='green', label = "cci down", linestyle='dotted')
	#ax3.axhline(y= -cci_d, color='steelblue', label = "limits (bear)", linestyle='dotted')
	#ax3.axhline(y= -cci_u, color='steelblue', linestyle='dotted')
	ax3.plot(lng,  color="olivedrab", label = "cci_series (bull)")
	ax3.plot(shrt, color="steelblue", label = "cci_series (bear)")
	ax3.legend(loc="upper left")

def draw_rsi(lng, shrt):
	global ax4

	bp = algo.get_backtest_params()
	rsi = bp[0][8]

	ax4.clear()
	ax4.set(ylim=( 30, 70))
	ax4.axhline(y=  50, color='green', linestyle='dotted')
	ax4.axhline(y= rsi, color='red', linestyle='dotted')
	ax4.axhline(y= 100-rsi, color='red', linestyle='dotted')
	ax4.plot(lng,  color="olivedrab", label = "rsi_series (bull)")
	ax4.plot(shrt, color="steelblue", label = "rsi_series (bear)")
	ax4.legend(loc="upper left")


def draw(stocks):
	cci_lng  = []
	cci_shrt = []

	rsi_lng =[]
	rsi_shrt =[]
	for stock in stocks:
		draw_stocks(stock)
		if(stock['type'] == 'long'):
			cci_lng  = stock['cci_series']
			rsi_lng  = stock['rsi_series']
		else:
			cci_shrt = stock['cci_series']
			rsi_shrt  = stock['rsi_series']
	draw_cci(cci_lng, cci_shrt)
	draw_rsi(rsi_lng, rsi_shrt)
	plt.draw()
	plt.pause(0.0001)

def init():
	plt.ion()

