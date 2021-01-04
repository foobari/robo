from lxml import html
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import numpy as np
import math
import time
import json
import pandas as pd
import getopt
import sys


def execute_buy_order_online(stock):
	print("Execute buy order", stock['name'])
	# click buy
	WebDriverWait(stock['browser'], 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/div[1]/div[1]/div/div/div/div/div/div[2]/div[2]/div[1]/a'))).click()

	# select account
	Select(WebDriverWait(stock['browser'], 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/div[2]/div/div/div[3]/div/div/div/div[1]/div[1]/div/div/div/select')))).select_by_value(stock['account'])

	# quantity
	amount = stock['stocks']
	WebDriverWait(stock['browser'], 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/div[2]/div/div/div[3]/div/div/div/div[2]/div[1]/div[1]/div[2]/div/input'))).send_keys(str(amount))

	# price
	# price = 2.11
	# WebDriverWait(stock['browser'], 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/div[2]/div/div/div[3]/div/div/div/div[2]/div[1]/div[2]/div[2]/div/input'))).send_keys(str(price))

	# execute	
	time.sleep(0.5)
	WebDriverWait(stock['browser'], 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/div[2]/div/div/div[3]/div/div/div/div[2]/div[7]/span/button/div/span'))).click()
	# return
	stock['browser'].get(stock['url'])


def execute_sell_order_online(stock):
	print("Execute sell order", stock['name'])
	# click sell
	WebDriverWait(stock['browser'], 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/div[1]/div[1]/div/div/div/div/div/div[2]/div[2]/div[2]/a'))).click()

	# select account
	Select(WebDriverWait(stock['browser'], 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/div[2]/div/div/div[3]/div/div/div/div[1]/div[1]/div/div/div/select')))).select_by_value(stock['account'])

	# quantity
	amount = stock['stocks']
	WebDriverWait(stock['browser'], 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/div[2]/div/div/div[3]/div/div/div/div[2]/div[1]/div[1]/div[2]/div/input'))).send_keys(str(amount))

	# price
	#price = 4.00
	#WebDriverWait(stock['browser'], 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/div[2]/div/div/div[3]/div/div/div/div[2]/div[1]/div[2]/div[2]/div/input'))).send_keys(u'\ue009' + u'\ue003')
	#WebDriverWait(stock['browser'], 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/div[2]/div/div/div[3]/div/div/div/div[2]/div[1]/div[2]/div[2]/div/input'))).send_keys(str(price))

	#execute
	time.sleep(0.5)
	WebDriverWait(stock['browser'], 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/div[2]/div/div/div[3]/div/div/div/div[2]/div[7]/span/button/div/span'))).click()

	# return
	stock['browser'].get(stock['url'])


def stock_sanity_check(stock, index):
	if((stock['buy_series'][index] == 0)):
		print(stock['name'], "buy read zero, copy last")
		stock['valid'] = False
		if(index > 0):
			stock['buy_series'][index]  = stock['buy_series'][index - 1]
	if((stock['sell_series'][index] == 0)):
		stock['valid'] = False
		print(stock['name'], "sell read zero, copy last")
		if(index > 0):
			stock['sell_series'][index] = stock['sell_series'][index - 1]
	if((stock['sell_series'][index] - stock['buy_series'][index]) > stock['spread']):
		stock['valid'] = False
		if(index > 0):
			print(stock['name'], "spread too big, copy last")
			stock['buy_series'][index]  = stock['buy_series'][index - 1]
			stock['sell_series'][index] = stock['sell_series'][index - 1]



def get_stock_values(stock, index, backtest_data=None):
	stock['valid'] = True

	if(backtest_data == None):
		buy  = float(stock['browser'].find_element(By.XPATH, '//*[@id="main-content"]/div[1]/div[2]/div/div[1]/div[1]/div/div[4]/div/span[2]/span/span[2]').text.replace(',','.'))
		sell = float(stock['browser'].find_element(By.XPATH, '//*[@id="main-content"]/div[1]/div[2]/div/div[1]/div[1]/div/div[5]/div/span[2]/span/span[2]').text.replace(',','.'))

		if(index == 0 and (buy < 0.01 or sell < 0.01)):
			raise Exception("First value zero")
		stock['buy_series'][index]  = buy
		stock['sell_series'][index] = sell
	else:
		if(stock['type'] == 'long'):
			if(index == 0 and (backtest_data[index][0] < 0.01 or backtest_data[index][1] < 0.01)):
				raise Exception("First value zero")
			stock['buy_series'][index] = backtest_data[index][0]
			stock['sell_series'][index] = backtest_data[index][1] 
		if(stock['type'] == 'short'):
			if(index == 0 and (backtest_data[index][2] < 0.01 or backtest_data[index][3] < 0.01)):
				raise Exception("First value zero")
			stock['buy_series'][index] = backtest_data[index][2]
			stock['sell_series'][index] = backtest_data[index][3] 

	stock_sanity_check(stock,index)

def login(stock, creds):
	print("Login")
	stock['browser'] = webdriver.Chrome()
	stock['browser'].get('https://classic.nordnet.fi/mux/login/startFI.html')
	username = WebDriverWait(stock['browser'], 10).until(EC.presence_of_element_located((By.ID, 'username')))
	username.send_keys(creds['username'])
	password = WebDriverWait(stock['browser'], 10).until(EC.presence_of_element_located((By.ID, 'password')))
	password.send_keys(creds['password'])
	nextButton = stock['browser'].find_element_by_class_name('button')
	nextButton.click()
	time.sleep(1)
	stock['browser'].get(stock['url'])
	print(stock['name'], stock['url'])

def logout(stock):
	stock['browser'].close()

