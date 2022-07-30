import requests, time
from colorama import Fore, init
init()

api = "FW2u842L8ou2QemRN48d15RrNn7bOMw" #your api key in between ""
delay = 0.26
fee = 9				#in %
rub_to_usd = 0.0135
too_low = 28			#Set it to the same value as Undercutter.py to have sorted formatting
debug_mode = False

def get_listings():
	url = f"https://market.csgo.com/api/v2/items?key={api}"
	try : 
		req = requests.get(url)
		data =  req.json()["items"]
		try :
			len(data)
		except :
			return []
	except Exception as e:
		time.sleep(delay)
		if debug_mode:
			print(f"Get listings failed : {e}")
		return get_listings()
	return data

def buy_price():
	buy = {}
	try :
		f = open("../Buy_prices.txt", "r", encoding="utf8")
		lines = f.readlines()
		for line in lines:
			price = float(line.split('Price:"')[1].split('"')[0])
			name = line.split('Name:"')[1].split('"')[0]
			buy[name] = price
		return buy
	except :
		return buy

def append_buy(name):
	try :
		f = open("../Buy_prices.txt", "a", encoding="utf8")
		price = input(f"Price for {name} : ")
		if "u" in price :
			price = float(price.split('u')[0])
		elif "c" in price :
			price = float(price.split('c')[0]) * 0.5932
		elif "r" in price :
			price =	float(price.split('r')[0]) * 0.588
		else :
			price = float(price) * 0.5932
		f.write(f'Price:"{price:.2f}" Name:"{name}"\n')
	except Exception as e :
		print(f"Error while appending price : {e}")
		append_buy(name)

def fill_buy_prices(buy, listings):
	flag = False
	for item in listings:
		name = item['market_hash_name']
		if buy.get(name, 0) == 0:
			if not flag:
				print("Goal is to save prices as usd. When writing prices, write a 'c' at the end to use csgoempire coins, 'r' for rollbit or 'u' for usd.")
			append_buy(name)
			flag = True
	if flag:
		buy = buy_price()
	return buy

def print_actual_profit(listings, buy, real):
	for item in listings:
		name = item['market_hash_name']
		buy_p = buy.get(name, -999) * (1/rub_to_usd)
		if buy_p == -999:
			print(f'{name} not in buy_prices.txt')
		buy_p = round(buy_p, 2)
		profit = (item['price'] * ((100 - fee) / 100) * 0.95) / buy_p
		profit = profit - 1
		profit = profit * 100
		if real:
			if round(profit, 2) == round(too_low, 2):
				continue
		else:
			if round(profit, 2) != round(too_low, 2):
				continue
		if profit > 0:
			color = Fore.GREEN
		else :
			color = Fore.RED
		print(f"{color}{profit:6.2f}%  {Fore.YELLOW}{item['price']*rub_to_usd:7.2f}$  {Fore.CYAN}{name}{Fore.RESET}")

def main():
	buy = buy_price()
	time.sleep(delay)
	listings = get_listings()
	buy = fill_buy_prices(buy, listings)
	print_actual_profit(listings, buy, True)
	print_actual_profit(listings, buy, False)
	
main()
