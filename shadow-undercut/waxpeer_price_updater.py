import requests, json
import time, datetime
import asyncio, sys
from colorama import Fore, init
init()

waxpeer_key = "46e39b4494c29a7b22eb3d2ee2cf699783922b35acc31d6fd23ef464199ec392"
coin_to_usd_rate = 0.5932
min_profit = 7
delay = 20
show_times = 0
steam_price = -5

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
				print("Goal is to save prices as usd. When writing prices, write a 'c' at the end to use csgoempire coins, 'u' for usd.")
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

def get_my_items():
	my_items_url = "https://api.waxpeer.com/v1/list-items-steam?api=" + waxpeer_key
	my_items = []
	try :
		req = requests.get(my_items_url)
		data = req.json()
	except:
		print(Fore.RED + "Request to get my items failed" + Fore.RESET)
		return my_items
	if req.status_code != 200:
		print(Fore.RED + f"Request to get my items failed, error code : {req.status_code}" + Fore.RESET)
		return my_items
	for item in data["items"]:
		item_id = int(item["item_id"])
		item_price = float(item["price"])/1000
		name = item["name"]
		flag = 0
		for x in my_items:
			if name == x["name"]:
				flag = 1
				break
		if flag == 0:
			steam = (item["steam_price"]["average"]/1000)
			steam = (1 + (steam_price / 100)) * steam
			my_items.append({"name":name, "price":item_price, "id":item_id, "steam":steam})
	return my_items

def get_lowest_prices(item):
	item_name = item["name"]
	max_price = item["steam"]
	url_item_name = item["name"]
	if " | " in item["name"]:
		url_item_name = url_item_name.replace(" | ", " ")
	if " (" in url_item_name:
		url_item_name = url_item_name.split(" (")[0]
	if " " in url_item_name:
		url_item_name = url_item_name.replace(" ", "%20")
	all_listing_url = "https://api.waxpeer.com/v1/get-items-list?api=" + waxpeer_key + "&skip=0&search=" + url_item_name + "&limit=100&sort=desc&minified=0&game=csgo"
	time.sleep(1)
	try :
		req = requests.get(all_listing_url)
		data = req.json()
	except:
		print(Fore.RED + f"Request to get {item['name']} lowest price failed" + Fore.RESET)
		item["lowest"] = -1
		return
	if req.status_code != 200:
		print(Fore.RED + f"Request to get {item['name']} lowest price failed, error code : {req.status_code}" + Fore.RESET)
		item["lowest"] = -1
		return
	temp_prices = []
	# if "Hand" in item['name']:
	# 	print(temp_prices)
	for x in data["items"]:
		if int(x["item_id"]) == item["id"]:
			continue
		name = x["name"]
		if name != item_name:
			continue
		if (float(x["price"])/1000) < max_price:
			temp_prices.append(float(x["price"] / 1000))
	if len(temp_prices) <= 0:
		item["lowest"] = item["steam"]
		return
	lowests = sorted(temp_prices, reverse=False)
	item["lowest"] = lowests[0]

async def append_lowest():
	begin = time.time()
	my_items = get_my_items()
	if show_times == 1:
		print(f"time to get my items : {time.time() - begin}s")
	if len(my_items) <= 0:
		return -1
	loop = asyncio.get_event_loop()  #maybe this one
	futures = []
	for my_item in my_items:
		futures.append(loop.run_in_executor(None, get_lowest_prices, my_item))
	for future in futures:
		await future
	return my_items

def append_purchased():
	begin = time.time()
	loop = asyncio.get_event_loop()
	my_items = loop.run_until_complete(append_lowest())
	if show_times == 1:
		print(f"time to get lowest : {time.time() - begin}s")
	if my_items == -1:
		return -1
	withdrawn = buy_price()
	withdrawn = fill_buy_prices(withdrawn, my_items)
	for item in my_items:
		item["purchased"] = withdrawn[item['name']]
	return my_items

def update_waxpeer_price(item, price, profit, steam):
	# print("updating price")
	edit_price_url = "https://api.waxpeer.com/v1/edit-items?api=" + waxpeer_key
	edit_headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
	price = price * 1000
	edit_payload = "{ \"items\": [ { \"item_id\": " + str(item["id"]) + ", \"price\": " + str(price) + " } ]}"
	try :
		req = requests.post(edit_price_url, data=edit_payload, headers=edit_headers)
	except:
		print(Fore.RED + "Request to update price failed." + Fore.RESET)
		return
	price = price / 1000
	if req.status_code == 200:
		date = datetime.datetime.now()
		if steam == 0:
			print(Fore.CYAN + date.strftime("%d-%m %H:%M:%S") + " Updated price to : " + Fore.GREEN + "%8.3f " %(price) + f" {profit:.2f}%  " + Fore.YELLOW + item["name"] + Fore.RESET)
		else :
			print(Fore.CYAN + date.strftime("%d-%m %H:%M:%S") + " Profit was 2 low : " + Fore.GREEN + "%8.3f " %(price) + f" {profit:.2f}%  " + Fore.YELLOW + item["name"] + Fore.RESET)
	else:
		print(Fore.RED + f"Updating price failed : {req.status_code}" + Fore.RESET)
	# print("finished")

def round_waxpeer(items):
	for item in items:
		item["price"] = round(item["price"], 3)
		item["steam"] = round(item["steam"], 3)
		item["lowest"] = round(item["lowest"], 3)
	return items
	
def update_waxpeer_prices():
	items = append_purchased()
	if (items == -1):
		return
	begin = time.time()
	items = round_waxpeer(items)
	for item in items:
		if item["lowest"] == -1:
			continue
		lowest = round(item["lowest"] - 0.001, 3)
		profit = lowest - lowest * 0.059
		profit = (((profit - profit * 0.02) / item["purchased"]) - 1) * 100
		if lowest != item["price"] and profit >= min_profit:
			update_waxpeer_price(item, lowest, profit, 0)
			continue
		if profit < min_profit and round(item["steam"] - 0.001, 3) != item["price"]:
			lowest = round(item["steam"] - 0.001, 3)
			profit = lowest - lowest * 0.059
			profit = (((profit - profit * 0.02) / item["purchased"]) - 1) * 100
			# if "Night" in item['name']:
			# print(
			update_waxpeer_price(item, lowest, profit, 1)
	if show_times == 1:
		print(f"time to update (async) : {time.time() - begin}s")

def update_waxpeer_main():
	print(Fore.MAGENTA + "Waxpeer price updater started" + Fore.RESET)
	while 1:
		try :
			update_waxpeer_prices()
		except Exception as e:
			print("error\n", e)
			time.sleep(3)

update_waxpeer_main()
