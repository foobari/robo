import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas_datareader as web
import numpy as np
import math
import os,glob
import pdb

fig = plt.figure(figsize=(12,10))
ax1 = fig.add_subplot(311)
ax2 = fig.add_subplot(312)
ax3 = fig.add_subplot(313)


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


	ax.plot(stock['buy_series'], label = stock["name"])
	ax.plot(stock['sma_series_short'], label = "SMA_short", linestyle=':')
	ax.plot(stock['sma_series_long'],  label = "SMA_long", linestyle=':')
	ax.legend(loc="upper left")
	if(float(stock["cci_last"]) > 0):
		color = 'green'
	else:
		color = 'red'
	ax.text(0.01, 0.01, "cci: " + str(stock["cci_last"]), transform=ax.transAxes, color=color)

def draw_money(money):
	global ax3
	ax3.clear()	
	ax3.plot(money, color="green", label = "Money")			
	ax3.legend(loc="upper left")


def draw(stocks, money):
	for stock in stocks:
		draw_stocks(stock)
	draw_money(money)
	plt.draw()
	plt.pause(0.0001)


def init():
	plt.ion()
