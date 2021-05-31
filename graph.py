#import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
#import pandas_datareader as web
import numpy as np
import math
import os,glob
import pdb


import algo

fig = plt.figure(figsize=(12,12))
ax1 = fig.add_subplot(511)
ax2 = fig.add_subplot(512)
ax3 = fig.add_subplot(513)
ax4 = fig.add_subplot(514)
ax5 = fig.add_subplot(515)

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
		#ax.axvline(x = x_val, color='red', linestyle='--')
	
	if(len(stock['signals_list_buy'])):
		x_val = [x[0] for x in stock['signals_list_buy']]
		y_val = [x[1] for x in stock['signals_list_buy']]
		ax.plot(x_val, y_val, 'g^',  color='blue')
		#ax.axvline(x = x_val, color='green', linestyle='--')

	if(stock['type'] == 'long'):
		color = 'olivedrab'
	else:
		color = 'steelblue'
	ax.plot(stock['buy_series'], color = color, label = stock["name"])
	ax.plot(stock['sma_series_short'], label = "SMA_short", linestyle=':')
	ax.plot(stock['sma_series_long'],  label = "SMA_long", linestyle=':')

	#ax.axhline(y = stock['pivots'][-1][0], color='green', linestyle='--')
	#ax.axhline(y = stock['pivots'][-1][1], color='green', linestyle='--')
	#ax.axhline(y = stock['pivots'][-1][2], color='green', linestyle='--')
	
	#ax.plot(stock['pivots'])
	#ax.plot(stock['pp_s1'])
	#ax.plot(stock['pp_r1'])

	ax.legend(loc="upper left")

def draw_cci(lng, shrt):
	global ax3

	bp = algo.get_params()
	cci_l = bp['cci_lim']# bp[0][1]
	cci_d = bp['cci_down']# [0][2]
	cci_b = bp['cci_big'] #bp[0][10]

	ax3.clear()
	ax3.set(ylim=(-330, 330))
	#ax3.axhline(y=  cci_l, color='red', label = "cci up", linestyle='dotted')
	ax3.axhline(y=  cci_d, color='green', label = "cci down", linestyle='dotted')
	#ax3.axhline(y= -cci_b, color='brown', label = "cci big", linestyle='dotted')
	ax3.axhline(y=  cci_b, color='brown', label = "cci big", linestyle='dotted')
	ax3.plot(lng,  color="olivedrab", label = "cci_series")
	#ax3.plot(shrt, color="steelblue", label = "cci_series (bear)")
	ax3.legend(loc="upper left")

def draw_rsi(lng, shrt):
	global ax4

	bp = algo.get_params()
	ax4.clear()
	ax4.set(ylim=( 25, 75))
	ax4.axhline(y=  50, color='green', linestyle='dotted')
	ax4.axhline(y= bp['rsi_lim'], color='red', linestyle='dotted')
	#ax4.axhline(y= 100-bp['rsi_lim'], color='red', linestyle='dotted')
	ax4.axhline(y= bp['rsi_big'], color='brown', linestyle='dotted')
	ax4.plot(lng,  color="olivedrab", label = "rsi_series")
	#ax4.plot(shrt, color="steelblue", label = "rsi_series (bear)")
	ax4.legend(loc="upper left")

def draw_test(test1):
	global ax5

	ax5.clear()
	#ax5.set(ylim=( -0.05, 0.05))
	#ax5.axhline(y= 0, color='green', linestyle='dotted')
	ax5.plot(test1, color="black", label = "test")
	#ax5.plot(test2, color="green", label = "test")
	#ax5.plot(test3, color="red", label = "test")
	ax5.legend(loc="upper left")


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
			#test1 = stock['tweak']
			#test2 = stock['pp_r1']
			#test3 = stock['pp_s1']

		else:
			cci_shrt = stock['cci_series']
			rsi_shrt = stock['rsi_series']

	#draw_test(test1)
	draw_cci(cci_lng, cci_shrt)
	draw_rsi(rsi_lng, rsi_shrt)
	plt.draw()
	plt.pause(0.0001)


def init():
	plt.ion()

