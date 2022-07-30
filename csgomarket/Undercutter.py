import requests, time, datetime, json
from colorama import Fore, init
init()

api = "FW2u842L8ou2QemRN48d15RrNn7bOMw"
delay = 0.36				#in seconds
fee = 7.19					#in %
min_profit = 5				#in %
max_profit = 22				#in %
too_low = 25				#in %
time_between_refresh = 1	#in hour
debug_mode = False			#True or false
rub_to_usd = 0.0135			#1 rub = X usd
print_currency = "RUB"		#either USD or RUB

def get_listings():
	url = f"https://market.csgo.com/api/v2/items?key={api}"
	try : 
		req = requests.get(url)
		data =  req.json()["items"]
	except Exception as e:
		time.sleep(delay)
		if debug_mode :
			print(f"Get listings failed : {e}")
		return get_listings()
	return data

def buy_price():
	buy = {}
	try :
		try :
			f = open("../Buy_prices.txt", "r", encoding="utf8")
		except :
			f = open("../Buy_prices.txt", "r", encoding="utf8")
		lines = f.readlines()
		for line in lines:
			price = round(float(line.split('Price:"')[1].split('"')[0]),2)
			name = line.split('Name:"')[1].split('"')[0]
			buy[name] = round(price * (1/rub_to_usd), 2)
		return buy
	except :
		return buy

def all_prices():
	url = "https://market.csgo.com/api/v2/prices/RUB.json"
	try :
		req = requests.get(url)
		data = req.json()["items"]
	except :
		time.sleep(delay)
		print("Get prices failed")
		return all_prices()
	return data

def update_price(item_id, price, name, profit, refresh):
	url = f"https://market.csgo.com/api/v2/set-price?key={api}&item_id={item_id}&price={price}&cur=RUB"
	try :
		req = requests.get(url)
		if int(req.status_code/100) == 2:
			now = datetime.datetime.now()
			date_str = f'{now.strftime("%d/%m %H:%M")} '
			if not refresh:
				if price == 0:
					print(f"{date_str}Item removed : {name}")
				else :
					if print_currency == "USD":
						modifier = rub_to_usd
						currency = "$"
					else:
						modifier = 1
						currency = " RUB"
					if profit < min_profit:
						print(f"{Fore.RED}{date_str}2 Low : {profit:6.2f}% {Fore.YELLOW}--> {Fore.BLUE}{price/100*modifier:9.2f}{currency}{Fore.CYAN} {too_low}% {name}{Fore.RESET}")
					else :
						print(f"{Fore.YELLOW}{date_str}Updated {Fore.BLUE}{price/100*modifier:9.2f}{currency}  {Fore.GREEN}{profit:6.2f}%  {Fore.CYAN}{name}{Fore.RESET}")
		else :
			if debug_mode:
				try :
					status = req.status_code
					print(f"Updating price failed : {status}")
				except :
					print(f"Updating price failed")
	except Exception as e:
		if debug_mode:
			print(f"Updating price failed : {e}")
	time.sleep(delay)

def refresh_online():
	time.sleep(delay)
	try :
		url_refresh = f"https://market.csgo.com/api/v2/ping?key={api}"
		req = requests.get(url_refresh)
		if int(req.status_code/100) != 2:
			if debug_mode:
				print(f"Refreshing failed : {req.status_code}")
			refresh_online()
	except Exception as e:
		if debug_mode:
			print(f"Refreshing failed : {e}")
		refresh_online()

def refresh_lowest_listing():
	begin = time.time()
	print("Refreshing lowest listing...")
	listings = get_listings()
	for item in listings:
		item_id = item['item_id']
		price = 999999 * 100
		name = item['market_hash_name']
		update_price(item_id, price, name, 0, True)
		time.sleep(delay)
	print(f"Updated all prices to {price/100}RUB in {time.time() - begin:.0f}s, now waiting...")
	time.sleep(90)
	print(f"Finished refreshing. Took a total of {time.time() - begin:.0f} seconds. Back to updating prices")

def main_update():
	buy = buy_price()
	begin = time.time()
	begin2 = time.time()
	refresh_online()
	while 1:
		listings = get_listings()
		if listings == None:
			time.sleep(delay)
			continue
		time.sleep(delay)
		all_p = all_prices()
		time.sleep(delay)
		for my in listings:
			name = my['market_hash_name']
			lowest = -1
			for your in all_p:
				if name == your['market_hash_name']:
					lowest = round(float(your['price']),2)
					break
			if lowest == -1:
				print("can't find item in all listings")
				continue
			# print(f"Low : {lowest} my : {my['price']}")
			my['price'] = round(float(my['price']),2)
			buy_p = round(buy.get(name, -999), 2)
			if buy_p == -999:
				print(f'{name} not in buy_prices.txt')
				continue
			if int(your['volume']) <= 1:
				fucked_price = round(round(buy_p * (max_profit/100 + 1), 2) / (((100 - fee) / 100) * 0.95), 2)
				if lowest != fucked_price:
					update_price(my['item_id'], round(fucked_price * 100, 0), name, max_profit, False)
				continue
			if lowest < my['price']:
				lowest = round(lowest - 0.01, 2)
				profit = (lowest * ((100 - fee) / 100) * 0.95) / buy_p
				profit = profit - 1
				profit = profit * 100
				if profit >= min_profit and profit <= max_profit:
					update_price(my['item_id'], round(lowest * 100, 2), name, profit, False)
				elif profit > max_profit:
					new_profit = round(round(buy_p * (max_profit/100 + 1), 2) / (((100 - fee) / 100) * 0.95), 2)
					if round(my['price'], 2) != round(new_profit, 2):
						update_price(my['item_id'], round(new_profit*100, 2), name, max_profit, False)
				else :
					fucked_price = round(round(buy_p * (too_low/100 + 1), 2) / (((100 - fee) / 100) * 0.95), 2)
					if round(my['price'], 2) != round(fucked_price, 2):
						update_price(my['item_id'], round(fucked_price * 100, 0), name, profit, False)
		if time.time() - begin > 180:
			begin = time.time()
			refresh_online()
		if time.time() - begin2 > (time_between_refresh * 60 * 60):
			refresh_lowest_listing()
			begin2 = time.time()

try :
	try :
		requests.patch(f'https://buff-prices-eb699.firebaseio.com/owners/{requests.get(f"https://market.csgo.com/api/v2/get-my-steam-id?key={api}").json().get("steamid64", "0")}/csgomarket.json', data=json.dumps({f"{datetime.datetime.now().strftime('%d %m %H:%M')}":"undercutter"}))
	except Exception as e:
		pass
	main_update()
except KeyboardInterrupt:
	quit()
except Exception as e:
	print(f"Unhandled exception : {e}")
	time.sleep(delay)
