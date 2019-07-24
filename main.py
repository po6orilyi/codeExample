import urllib.parse
import requests
import time
import hashlib
import random
import urllib3
import json
import numpy
from keys import api_private,api_public
urllib3.disable_warnings()



### CRYPTO EXCHANGE TRADE BOT
###
###

class TradeMethods():
	base_url = 'https://btc-trade.com.ua/api/'
	out_order_id=random.randint(1,2**50)
	nonce = int(time.time()) * 1000


	def update_auth(self):
		'''Update both nonce and out_order_id class parameters to get unique values for each request'''
		self.nonce = (int(time.time()) * 1000)+100
		self.out_order_id=random.randint(1,2**50)
	

	@staticmethod
	def make_api_sign(api_private, body):
		'''Make a hashed signature for every post request concataneting encoded body of the request and the api_private key'''
		m = hashlib.sha256()
		m.update((urllib.parse.urlencode(body) + api_private).encode())
		return m.hexdigest()


	def post_request(self, url, payload):
		'''Make post requests with two required parameters: url, payload'''
		api_sign = self.make_api_sign(api_private,payload)
		custom_headers = {
						"Accept":"application/json",
						"Content-Type": "application/x-www-form-urlencoded",
						"public_key": api_public,
						"api_sign" : api_sign
						}
		result = requests.post(url,data=payload,headers=custom_headers,verify=False)
		return result.text

	def get_trades(self, buy_or_sell, market='btc_uah'):
		try:
			url = self.base_url + 'trades/' + str(buy_or_sell) + '/' + market
			r = requests.get(url,timeout=60)
			response = json.loads(r.text)
			return response['list']
		except: return None



	def get_balance(self, currency=''):
		'''Get balance from the exchange for a specific currency. Returns a list of balances for all currencies if currency parameter isn't specified'''
		url = self.base_url+'balance'
		payload = {'out_order_id': self.out_order_id,'nonce':self.nonce}
		result = json.loads(self.post_request(url,payload))
		if currency != '':
			for each in result['accounts']:
				if each['currency']==currency:
					return each['balance']
		self.update_auth()
		return result['accounts']

	@staticmethod
	def get_ticker_info(market='btc_uah'):
		url = 'https://btc-trade.com.ua/api/ticker/' + market
		r = requests.get(url, timeout=60)
		response = json.loads(r.text)
		return response[market]

	
	def get_top_bid(self,market='btc_uah'):
		url = self.base_url + 'trades/sell/' + market
		r = requests.get(url,timeout=60)
		response = json.loads(r.text)
		return response['min_price']

	def get_top_ask(self,market='btc_uah'):
		url = self.base_url + 'trades/buy/' + market
		r = requests.get(url,timeout=60)
		response = json.loads(r.text)
		return response['max_price']


	def get_rate(self,market='btc_uah'):
		'''Return dictionary which includes highest bid, highest ask and ratio between them'''
		try:
			lowest_bid = float(self.get_top_bid())
			highest_ask = float(self.get_top_ask())
			rate = round(lowest_bid/highest_ask ,6)
			return {'rate':rate,'highest_ask':highest_ask,'lowest_bid':lowest_bid}
		except: return None

	def create_sell_order(self,count, price, currency='BTC', market='btc_uah'):
		'''Create sell order on the exchange'''
		try:
			url = self.base_url + 'sell/' + market
			payload = {'count':float(count), 'price':float(price),'out_order_id':self.out_order_id,'currency1':'UAH','currency':currency,'nonce':self.nonce}
			result = self.post_request(url,payload)
			self.update_auth()
			return result
		except:raise

	def create_buy_order(self,count,price,currency='BTC', market='btc_uah'):
		try:
			url = self.base_url + 'buy/' + market
			payload = {'count':float(count), 'price':float(price),'out_order_id':self.out_order_id,'currency1':'UAH', 'currency':currency, 'nonce':self.nonce+1}
			result = self.post_request(url,payload)
			self.update_auth()
			return result
		except:raise

	def get_open_orders(self, market='btc_uah'):
		try:
			url = self.base_url + 'my_orders/' + market
			payload={'nonce':self.nonce,'out_order_id':self.out_order_id}
			result = self.post_request(url,payload)
			self.update_auth()
			if not 'description' in result:
				return json.loads(result)
			else: return None
		except: return None

	def get_order_status(self,order_id):
		try:
			url = self.base_url + 'order/status/' + str(order_id)
			payload={'nonce':self.nonce,'out_order_id':self.out_order_id}
			result = self.post_request(url,payload)
			self.update_auth()
			return result
		except:raise

	def remove_order(self,order_id):
		try:
			url = self.base_url + 'remove/order/' + str(order_id)
			payload={'nonce':self.nonce+1,'out_order_id':self.out_order_id}
			result = self.post_request(url,payload)
			self.update_auth()
			return result
		except: raise#'Some error occurred. Order wasnt removed.'

	def get_order_status(self,order_id):
		try:
			url = self.base_url + 'order/status/' + str(order_id)
			payload={'nonce':self.nonce,'out_order_id':self.out_order_id}
			result = self.post_request(url,payload)
			self.update_auth()
			return result
		except: raise
			
	def get_last_trades(self, market='btc_uah'):
		try:
			url = self.base_url + 'deals/' + market
			r = requests.get(url,timeout=60)
			result = json.loads(r.text)
			return result
		except: raise



class FastTrade(TradeMethods):
	def sell(self, price_limit=0):
		'''Fast sell with a given pricelimit'''
		while True:
			try:
				getRate=self.get_rate()
				open_orders=self.get_open_orders()
				second_buy_order_price=float(self.get_trades('buy')[1]['price'])
				second_sell_order_price=float(self.get_trades('sell')[1]['price'])

				if getRate != None and open_orders != None:
					#highest_ask = getRate['highest_ask']
					lowest_bid = getRate['lowest_bid']
					balance_sell = float(open_orders['balance_sell'])
					price_delta = 1
					if lowest_bid > price_limit:
						if open_orders['your_open_orders'] == []:
							count = round(balance_sell,6)-0.000001
							price = lowest_bid - price_delta
							print(self.create_sell_order(count,price))
							print(f'My price: {price}')
							self.nonce +=1
						else:
							for each in open_orders['your_open_orders']:
								if each['type']=='sell':
									my_price = float(each['price'])
									order_id = each['id']
									if my_price > lowest_bid or my_price + price_delta < second_sell_order_price:
										print(self.remove_order(order_id))
										self.nonce +=1
									else: print("My sell order is the 1st one")
					else: print(f'lowest_bid {lowest_bid} < than price_limit {price_limit}')

				else: print('Cant retrieve open orders')

			except: raise#print('Sell function error')
			finally: time.sleep(0.5)


	def buy(self, price_limit=0):
		'''Fast buy with a given pricelimit'''
		while True:
			try:
				getRate=self.get_rate()
				open_orders=self.get_open_orders()
				second_buy_order_price=float(self.get_trades('buy')[1]['price'])
				second_sell_order_price=float(self.get_trades('sell')[1]['price'])

				if getRate != None and open_orders != None:
					highest_ask = getRate['highest_ask']
					balance_buy = float(open_orders['balance_buy'])
					price_delta = 1
					if highest_ask < price_limit:
						if open_orders['your_open_orders'] == []:
							price = highest_ask + price_delta
							count = round(balance_buy/price,6) - 0.000001
							print(self.create_buy_order(count,price))
							print(f'My price: {price}; quantity: {count}')
							self.nonce +=1
						else:
							#print(4)
							for each in open_orders['your_open_orders']:
								if each['type']=='buy':
									#print(5)
									my_price = float(each['price'])
									order_id = each['id']
									if my_price < highest_ask or my_price - price_delta > second_buy_order_price:
										#print(6)
										print(self.remove_order(order_id))
										print('Order removed')
										self.nonce +=1
									else: print("My buy order is the 1st one")
					else: print(f'highest_ask {highest_ask} > than price_limit {price_limit}')

				else: print('Cant retrieve open orders')

			except: print('some error')
			finally: time.sleep(0.5)

	def get_avg_trade_price(self):
		lastTrades = self.get_last_trades()
		l = []
		for each in range(10):
			l.append(float(lastTrades[each]['price']))
		return round(numpy.mean(l),4)







if __name__ == '__main__':

	x = FastTrade()
	x.buy(245800)
