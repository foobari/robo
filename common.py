from lxml import html
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import numpy as np
import math
import time

FIXED_STOCK_AMOUNT = True # True -> use BUY_STOCKS, False -> use MONEY_PER_TRANSACTION
BUY_STOCKS = 100
MONEY_PER_TRANSACTION = 1000

PRINT_ACTIONS = True

def count_stats(final, stocks, last_total, best_total, closed_deals, algo_params):
	unclosed_deals = 0
	pending_money  = 0
	losses_sum     = 0
	sharpe         = 0
	profitability  = 0

	for stock in stocks:
		if(stock['active_position']):
			unclosed_deals = unclosed_deals + 1
			closing_sell = ((float(stock['buy_series'][-1:]) - stock['last_buy']) * stock['stocks'])
			closed_deals.append(closing_sell)
			last_total = last_total + closing_sell

	if(len(closed_deals) > 0):
		if(np.std(closed_deals) != 0):
			sharpe = math.sqrt(len(closed_deals)) * np.mean(closed_deals) / np.std(closed_deals)
		else:
			sharpe = 0

		profits = [i for i in closed_deals if i >= 0]
		losses  = [i for i in closed_deals if i < 0]
		profit_sum = (sum(profits))
		losses_sum = -(sum(losses))
		profitability = 0

	if(len(closed_deals) > 0):
		profitability = float(len(profits) / float(len(closed_deals)))
	if(losses_sum > 0):
		profit_factor = profit_sum/losses_sum
	else:
		profit_factor = 100

	best_total = best_total + last_total

	print("profit", round(last_total, 2), "algo closed", len(closed_deals) - unclosed_deals, "force closed", unclosed_deals, "metrics", round(sharpe, 2), round(profitability, 2), round(profit_factor, 2))

	if(final):
		print("total", round(best_total, 2), algo_params)
		print

	return best_total


def execute_buy_order_online(stock):
	print("Execute buy order", stock['name'])
	# click buy
	WebDriverWait(stock['browser'], 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/div[1]/div[1]/div/div/div/div/div/div[2]/div[2]/div[1]/a'))).click()
	# select first account
	Select(WebDriverWait(stock['browser'], 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/div[2]/div/div/div[3]/div/div/div/div[1]/div[1]/div/div/div/select')))).select_by_value('1')
	# quantity
	amount = 100
	WebDriverWait(stock['browser'], 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/div[2]/div/div/div[3]/div/div/div/div[2]/div[1]/div[1]/div[2]/div/input'))).send_keys(str(amount))
	# price
	price = 2.11
	WebDriverWait(stock['browser'], 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/div[2]/div/div/div[3]/div/div/div/div[2]/div[1]/div[2]/div[2]/div/input'))).send_keys(str(price))
	# execute	
	WebDriverWait(stock['browser'], 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/div[2]/div/div/div[3]/div/div/div/div[2]/div[7]/span/button/div/span'))).click()
	# return
	stock['browser'].get(stock['url'])

def execute_sell_order_online(stock):
	print("Execute sell order", stock['name'])

def do_transaction(stock, flip, reason, money, last_total, closed_deals, algo_params, index):
	buy  = float(stock['buy_series'][-1:])
	sell = float(stock['sell_series'][-1:])

	# buy
	if((not stock['active_position']) and (flip == 1)):
		stock['active_position'] = True
		stock['current_top']        = sell
		stock['last_buy']           = sell
		stock['hard_stop_loss']	    = ((1 + algo_params['hard']     * stock['leverage'] / 100) * sell)
		stock['trailing_stop_loss'] = ((1 + algo_params['trailing'] * stock['leverage'] / 100) * sell)
		stock['signals_list_buy'].append((index, float(stock['sell_series'][-1:])))
		
		if(FIXED_STOCK_AMOUNT):
			stock['stocks'] = BUY_STOCKS
		else:
			stock['stocks'] = int(MONEY_PER_TRANSACTION / sell)
		
		if(PRINT_ACTIONS):
			print("ACTION: BUY ", stock['name'], stock['stocks'], stock['last_buy'])
		#execute_buy_order_online(stock)

	# sell
	if(stock['active_position'] and (flip == -1)):
		money = money + ((buy - stock['last_buy']) * stock['stocks'])
		last_total = money
		closed_deals.append((buy - stock['last_buy']) * stock['stocks'])
		stock['current_top'] = 0
		stock['active_position'] = False
		stock['signals_list_sell'].append((index, float(stock['buy_series'][-1:])))
		if(PRINT_ACTIONS):
			print("ACTION: SELL", stock['name'], stock['stocks'], buy, reason, "result", round(float(closed_deals[-1]), 2) , "total", round(last_total, 2))
		#execute_sell_order_online(stock)
		stock['stocks'] = 0

	return money, last_total

def get_stock_values_backtest(stock, index, backtest_data):
	stock['valid'] = True

	# Backtest data from stored files
	if(stock['type'] == 'long'):
		stock['buy_series'][index] = backtest_data[index][0]
		stock['sell_series'][index] = backtest_data[index][1] 
	if(stock['type'] == 'short'):
		stock['buy_series'][index] = backtest_data[index][2]
		stock['sell_series'][index] = backtest_data[index][3] 
	
	# sanity checks
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



def get_stock_values_live(stock, index):

	stock['valid'] = True

	# Live data from from Nordnet
	stock['buy_series'][index]  = float(stock['browser'].find_element(By.XPATH, '//*[@id="main-content"]/div[1]/div[2]/div/div[1]/div[1]/div/div[4]/div/span[2]/span/span[2]').text.replace(',','.'))
	stock['sell_series'][index] = float(stock['browser'].find_element(By.XPATH, '//*[@id="main-content"]/div[1]/div[2]/div/div[1]/div[1]/div/div[5]/div/span[2]/span/span[2]').text.replace(',','.'))
	
	# sanity checks
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


def store_stock_values(stocks, index):
	for stock in stocks:
		if(stock['type'] == 'long'):
			buy_long  = stock['buy_series'][index]
			sell_long = stock['sell_series'][index]
		if(stock['type'] == 'short'):
			buy_short  = stock['buy_series'][index]
			sell_short = stock['sell_series'][index]

	# store
	f = open("guru99.txt","a+")
	f.write(str((buy_long, sell_long, buy_short, sell_short)) + '\n')
	f.close()


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

def check_args(arglist):
	do_graph = False

	for i in arglist:
		if(i == "graph"):
			do_graph = True

	return do_graph
