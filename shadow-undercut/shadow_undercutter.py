import requests, json, time, datetime
from colorama import Fore, init
init()

cookie = "__cfduid=d341b30506eed885b47c86710a82eca611600371576; currency_rate=1; csrf_token=d19a513826654e125d949a4476196681; _ga=GA1.2.1928750781.1600371577; _gid=GA1.2.647987887.1600371577; currency=USD; _hjid=555227b2-9a0d-4d8f-b30e-6923ea0c286f; _hjIncludedInSessionSample=0; _hjAbsoluteSessionInProgress=0; lang=en; shadowpay_session=82f03d04b67861710c2014e144aec592d441f3d5; maxtf=1; maxtu=06cab78973efde3e653d08a193dd9948; maxtv=1600372044; csrf_cookie=c13fd7dc81563a0391e6ae5377d35dac; maxtp=3:10"
csrf_token = "c13fd7dc81563a0391e6ae5377d35dac"
min_profit = 5
delay = 1
steam_price = -5


def be_online_shadow():
	url = "https://shadowpay.com/en/profile/set_user_offline_state?state=0"
	try:
		req = requests.get(url, headers = shadowpay_headers)
	except :
		print("Shadow online failed")
	if req.status_code != 200:
		print("Shadow online failed : ", req.status_code)

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
		name = item['name']
		if buy.get(name, 0) == 0:
			if not flag:
				print("Goal is to save prices as usd. When writing prices, write a 'c' at the end to use csgoempire coins, 'r' for rollbit or 'u' for usd.")
			append_buy(name)
			flag = True
	if flag:
		buy = buy_price()
	return buy

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

def my_item_price():
	try :
		req = requests.get(my_items_url, headers = shadowpay_headers)
	except :
		print("Shadow get my items failed")
	if req.status_code != 200:
		print("Shadow get my items : ", req.status_code)
	data = req.json()
	index = 0
	my_items = []
	items_id = []
	for item in data["items"]:
		if item["item_id"] not in items_id:
			items_id.append(item["item_id"])
			price = float(item["price_market"])
			name = item["steam_market_hash_name"]
			item_id = item["id"]
			my_items.append({"name":name, "price":price, "id":item_id, "steam_price":0})
	# for item in my_items:
	# 	if "flip" in item["name"].lower():
	# print(item)
	return my_items

def	get_prices(my_item):
	name = my_item["name"] .replace(" ", "+")
	# print(name)
	# name = my_item["name"].replace("|", "%%7C")
	# url = "https://shadowpay.com/api/market/get_items?types=[]&exteriors=[]&rarities=[]&price_from=0.00&price_to=100000.00&count_stickers=[]&short_name=&search=" + name + "&stack=false&sort=asc&sort_column=price&limit=100&offset=0"
	url = "https://shadowpay.com/api/market/get_items?types=[]&exteriors=[]&rarities=[]&price_from=0&price_to=3100&game=csgo&count_stickers=[]&short_name=&search=" + name+ "&stack=false&sort=asc&sort_column=price&limit=500&offset=0"
	# print(url)
	try:
		req = requests.get(url, headers = shadowpay_headers)
	except :
		print(f"Shadow prices failed {my_item['name']}")
	if req.status_code != 200:
		print(f"Shadow prices failed {my_item['name']} : ", req.status_code)
	data = req.json()
	# print(data)
	prices = []
	for item in data["items"]:
		market_name = item["steam_market_hash_name"]
		# print(market_name, my_item['name'])
		if market_name == my_item["name"]:
			my_item["steam_price"] = float(item["steam_price_en"])
			if item["id"] != my_item["id"] and float(item["price_market"]) <= my_item["steam_price"]:
				prices.append(float(item["price_market"]))
	return prices

def update_price(price, my_item, market, profit):
	payload_s = f"id={my_item['id']}&price={price}&csrf_token={csrf_token}"
	headers = {'Cookie':cookie, 'Content-Type':'application/x-www-form-urlencoded'}
	#print(payload_s)
	try:	
		req = requests.post(update_url, headers = headers, data = payload_s)
	except :
		print(f"Shadow price update failed {my_item['name']}")
	if req.status_code != 200:
		print(f"Shadow price update failed {my_item['name']} : ", req.status_code)
	if req.json()["status"] == "success":
		date = datetime.datetime.now()
		if market == 1:
			print(Fore.YELLOW + date.strftime("%d-%m %H:%M:%S") + " Profit was 2 low :  " + Fore.GREEN + "%7.2f " %(price) + f" {profit:.2f}%  " + Fore.CYAN + my_item["name"] + Fore.RESET)
		if market == 0:
			print(Fore.YELLOW + date.strftime("%d-%m %H:%M:%S") + " Price updated to :  " + Fore.GREEN + "%7.2f " %(price)+ f" {profit:.2f}%  " + Fore.CYAN + my_item["name"] + Fore.RESET)
	else :
		print(f"{Fore.RED} Error : {Fore.RESET}{req.json()}")

def	main_update():
	global update_url, my_items_url, shadowpay_headers
	update_url = "https://shadowpay.com/api/market/save_item_price"
	my_items_url = "https://shadowpay.com/api/market/list_items"
	shadowpay_headers = {'Cookie':cookie}
	my_prices = my_item_price()
	buy = buy_price()
	withdrawn_items = fill_buy_prices(buy, my_prices)
	for item in my_prices:
		prices = get_prices(item)
		prices.sort(reverse=False)
		bought_price = withdrawn_items.get(item['name'], -1)
		if bought_price == -1:
			print(f"Item not in bought prices : {item['name']}")
			quit()
		if (len(prices) == 0 and item["price"] != round(item["steam_price"] - 0.01, 2)):
			print(item["steam_price"])
			price = round(item["steam_price"] - 0.01, 2)
			profit = (((price - 0.1 * price) / bought_price) - 1) * 100
			update_price(round(item["steam_price"] - 0.01, 2), item, 0, profit)
			continue
		elif (len(prices) > 0):
			flag = 0
			for price in prices:
				profit = (((price - 0.1 * price) / bought_price) - 1) * 100
				# print(f"name : {item['name']}, profit: {profit:.2f}%")
				if profit >= min_profit:
					if round(price - 0.01, 2) != item["price"]:
						update_price(round(price - 0.01, 2), item, 0, profit)
					flag = 1
					break
				else :
					break
			if flag == 0:
				if (item["price"] != round(item["steam_price"] - 0.01, 2)):
					price = round(item["steam_price"] - 0.01, 2)
					profit = (((price - 0.1 * price) / bought_price) - 1) * 100
					update_price(round(item["steam_price"] - 0.01, 2), item, 1, profit)

def main():
	print(f"{Fore.MAGENTA}Starting shadopay updater...{Fore.RESET}")
	begin = time.time()
	while (True):
		try :
			main_update()
			if time.time() - begin > 600:
				begin = time.time()
				be_online_shadow()
			time.sleep(delay)
		except KeyboardInterrupt:
			print(Fore.RED + "B" + Fore.GREEN + "y" + Fore.BLUE + "e" + Fore.RESET)
			quit()
		except Exception as e:
			print(f"{Fore.RED}Unhandled error : {e}{Fore.RESET}")
			time.sleep(delay)

main()
