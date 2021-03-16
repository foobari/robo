from binance.client import Client
from binance.enums import *
from lxml import html
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import numpy as np
import os
import math
import time
import json
import pandas as pd
import getopt
import sys

binance_client = []

def execute_buy_order_online(stock):
	global binance_client

	print("Execute buy order", stock['name'])

	if(stock['url'] == 'binance_api'):
		if(stock['name'] == "DOGEUSDT"):
			amount = stock['transaction_size']
			order = binance_client.order_market_buy(symbol='DOGEUSDT', quantity = amount)
			print order
			print
		else:
			print "not supported", stock['name']

	else:

		# click buy
		WebDriverWait(stock['browser'], 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/div[1]/div[1]/div/div/div/div/div/div[2]/div[2]/div[1]/a'))).click()
		print("buy", stock['name'])

		# select account
		time.sleep(0.1)
		Select(WebDriverWait(stock['browser'], 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/div[2]/div/div/div[3]/div/div/div/div[1]/div[1]/div/div/div/select')))).select_by_value(stock['account'])
		print("account", stock['account'])
		
		# quantity
		time.sleep(0.1)
		amount = stock['transaction_size']
		WebDriverWait(stock['browser'], 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/div[2]/div/div/div[3]/div/div/div/div[2]/div[1]/div[1]/div[2]/div/input'))).send_keys(str(amount))
		print("amount", str(amount))

		# price
		# price = 2.11
		# WebDriverWait(stock['browser'], 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/div[2]/div/div/div[3]/div/div/div/div[2]/div[1]/div[2]/div[2]/div/input'))).send_keys(str(price))

		# execute	
		time.sleep(0.5)
		WebDriverWait(stock['browser'], 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/div[2]/div/div/div[3]/div/div/div/div[2]/div[7]/span/button/div/span'))).click()
		print("execute")

		# return
		time.sleep(0.1)
		stock['browser'].get(stock['url'])

	
def execute_sell_order_online(stock):
	global binance_client
	
	print("Execute sell order", stock['name'])

	if(stock['url'] == 'binance_api'):
		if(stock['name'] == "DOGEUSDT"):
			amount = stock['transaction_size']
			order = binance_client.order_market_sell(symbol = 'DOGEUSDT', quantity = amount)
			print order
			print "------------------------"
		else:
			print "not supported", stock['name']

	else:
		# click sell
		WebDriverWait(stock['browser'], 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/div[1]/div[1]/div/div/div/div/div/div[2]/div[2]/div[2]/a'))).click()
		print("sell", stock['name'])

		# select account
		time.sleep(0.1)
		Select(WebDriverWait(stock['browser'], 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/div[2]/div/div/div[3]/div/div/div/div[1]/div[1]/div/div/div/select')))).select_by_value(stock['account'])
		print("account", stock['account'])

		# quantity
		time.sleep(0.1)
		amount = stock['transaction_size']
		WebDriverWait(stock['browser'], 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/div[2]/div/div/div[3]/div/div/div/div[2]/div[1]/div[1]/div[2]/div/input'))).send_keys(str(amount))
		print("amount", str(amount))

		# price
		#price = 4.00
		#WebDriverWait(stock['browser'], 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/div[2]/div/div/div[3]/div/div/div/div[2]/div[1]/div[2]/div[2]/div/input'))).send_keys(u'\ue009' + u'\ue003')
		#WebDriverWait(stock['browser'], 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/div[2]/div/div/div[3]/div/div/div/div[2]/div[1]/div[2]/div[2]/div/input'))).send_keys(str(price))

		#execute
		time.sleep(0.5)
		WebDriverWait(stock['browser'], 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/div[2]/div/div/div[3]/div/div/div/div[2]/div[7]/span/button/div/span'))).click()
		print("execute")

		# return
		time.sleep(0.1)
		stock['browser'].get(stock['url'])
	

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
			spread = 1.0025
			sell = buy * spread
			stock['buy_series'].append(buy)
			stock['sell_series'].append(sell)
		# Nordnet
		else:
			buy  = float(stock['browser'].find_element(By.XPATH, '//*[@id="main-content"]/div[1]/div[2]/div/div[1]/div[1]/div/div[4]/div/span[2]/span/span[2]').text.replace(',','.'))
			sell = float(stock['browser'].find_element(By.XPATH, '//*[@id="main-content"]/div[1]/div[2]/div/div[1]/div[1]/div/div[5]/div/span[2]/span/span[2]').text.replace(',','.'))

			if(index == 0 and (buy < 0.01 or sell < 0.01)):
				raise Exception("First value zero")
			stock['buy_series'].append(buy)
			stock['sell_series'].append(sell)
			stock_sanity_check(stock,index)
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
	else:
		options = webdriver.ChromeOptions()
		options.add_argument("--DBUS_SESSION_BUS_ADDRESS=/dev/null ")
		stock['browser'] = webdriver.Chrome(options = options)
		stock['browser'].get('https://classic.nordnet.fi/mux/login/startFI.html')
		username = WebDriverWait(stock['browser'], 10).until(EC.presence_of_element_located((By.ID, 'username')))
		username.send_keys(creds['username'])
		password = WebDriverWait(stock['browser'], 10).until(EC.presence_of_element_located((By.ID, 'password')))
		password.send_keys(creds['password'])
		nextButton = stock['browser'].find_element_by_class_name('button')
		nextButton.click()
		time.sleep(1)
		stock['browser'].get(stock['url'])
		print("login", stock['name'], stock['url'])

def logout(stock):
	if(stock['url'] != 'binance_api'):
		stock['browser'].close()

def refresh(stock):
	if(stock['url'] != 'binance_api'):
		print("refresh", stock['name'])
		stock['browser'].refresh()

