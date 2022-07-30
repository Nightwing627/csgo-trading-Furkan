from colorama import Fore, init
import requests, asyncio, websocket
import time, traceback, json, datetime
init()

def reverse_print_refresh():
	reverse_content = ""
	for line in reversed(list(open("../Buy_prices.txt",encoding="utf8"))):
		reverse_content += line.rstrip()+"\n"
	f = open('../reverse_Buy_prices.txt', 'w', encoding="utf8")
	f.write(reverse_content)
	f.close()

	reverse_content_trash = ""
	for line_trash in reversed(list(open("../Buy_prices_trash.txt",encoding="utf8"))):
		reverse_content_trash += line_trash.rstrip()+"\n"
	f = open('../trash_reverse_Buy_prices.txt', 'w', encoding="utf8")
	f.write(reverse_content_trash)
	f.close()



def	rollbit_withdraw(item, profit, profit2, count, name, price):
	item_payload = "{\"refs\": [\"" + item["ref"] + "\"]}"
	try :
		withdraw_response = requests.post(url_rollbit_w, data=item_payload, headers=rollbit_headers_withdraw)
		withdraw_json = withdraw_response.json()
	except :
		print(f"{Fore.RED}Request to withdraw {name} failed, trying again{Fore.RESET}")
		time.sleep(delay)
		return (rollbit_withdraw(item, profit, profit2, count, name, price))
	to_print = print_item(item, name, price, profit, profit2, count, Fore.GREEN)+ f"{Fore.MAGENTA}Trying to withdraw...\n{Fore.RESET}"
	if "success" in withdraw_json and withdraw_json["success"]:
		to_print += f"{Fore.GREEN}Item successfully withdrawn{Fore.RESET}\n"
		print_tracked({'market_value':price*100, 'market_name':name + " Rollbit", 'custom_price':item.get('markup',0)}, profit, profit2)
		reverse_print_refresh()
		if withdraw_once:
			exclude_item({'market_name':name})
	else:
		if "message" in withdraw_json:
			to_print += f'{Fore.RED}{withdraw_json["message"]}{Fore.RESET}\n'
		else:
			to_print += f'{Fore.RED}{withdraw_json}{Fore.RESET}\n'
	return to_print

def on_message(ws, message):
	try :
		if print_delays:
			begin = time.time()
		data = json.loads(message)
		if data[0] == "steam/market":
			if data[1]["state"] == "listed":
				if custom_price or data[1].get('markup', 0) < 0:
					if not custom_price or data[1].get('markup', 0) <= max_custom:
						price = data[1]['price']
						if not skip_ofr or (price >= min_coin and price <= max_coin):
							print(advanced_filtering(data[1], price, data[1]["items"][0]["name"]), end="")
							if print_delays:
								print(f'Time to treat : {(time.time()-begin)*1000:.3f}ms')
	except Exception as e:
		print(f"{Fore.RED}Unhandled exception caught : {e}{Fore.RESET}")

def on_error(ws, error):
	if (len(str(error))) != 0:
		print(Fore.RED + "Websocket error : " + Fore.RESET)
		print(error)

def on_close(ws):
	print("Websocket connection closed. Retrying in 5 seconds.")
	try :
		time.sleep(5)
	except KeyboardInterrupt:
		quit()

def rollbit_main():
	rollbit_origin = "https://www.rollbit.com"
	ws_url = "wss://ws.rollbit.com/"
	wh_url = "redacted"
	ws_user_agent = "User-Agent: " + rollbit_useragent
	websocket.enableTrace(False)
	ws = websocket.WebSocketApp(ws_url, header=[ws_user_agent], on_message=on_message, on_error=on_error, on_close=on_close, cookie = rollbit_cookies)
	while True:
		ws.run_forever(origin = rollbit_origin)

def empire_ws_identify(ws):
	try:
		data_url = "https://csgoempire.com/api/v2/metadata"
		user_data = requests.get(data_url, headers= {'Cookie':cookies}).json()
		to_send = '42/notifications,["identify",'
		to_send += '{' + f'"uid":{user_data["user"]["id"]},"model":'
		to_send += json.dumps(user_data['user'])
		to_send += f',"authorizationToken":"{user_data["socket_token"]}","signature":"{user_data["socket_signature"]}", "uuid":"{uuid}"'
		to_send += "}]"
		ws.send(to_send)
	except Exception as e:
		print(f'{Fore.RED}Error Authentificating to the WS, this should not happen : {Fore.RESET}{e}')

def on_open(ws):
	global ping, token_timer, price_source_timer
	refresh_token()
	ping = time.time()
	token_timer = time.time()
	price_source_timer = time.time()
	ws.send("40/notifications,")
	time.sleep(3)
	empire_ws_identify(ws)
	time.sleep(3)
	ws.send('42/notifications,["p2p/new-items/subscribe",1]')
	if debug_mode :
		print("Authentificated to the WS")

def empire_message(ws, message):
	if print_delays:
		how = time.time()

	flag = False
	data = message.split("42/notifications,")[1]
	data = json.loads(data)
	try:
		if data[0] == "p2p_new_item":
			flag = True
			data =json.loads(data[1])
			if custom_price or data.get('custom_price', 0) == 0:
				if not custom_price or data.get('custom_price', 0) <= max_custom:
					price = data['market_value']/100
					if not skip_ofr or (price >= min_coin and price <= max_coin):
						print(advanced_filtering(data, price, data['market_name']), end="")
	except Exception as e:
		if debug_mode:
			print(e)
	if print_delays:
		if flag:
			print(f"took {(time.time() - how) *1000:.3f}ms")
	global ping, token_timer, price_source_timer
	temp = time.time()
	if temp - ping > 50:
		ws.send("2")
		ping = time.time()
	
	if temp - token_timer > 540:
		refresh_token()
		token_timer = time.time()
	
	if temp - price_source_timer > 3600:
		if price_source:
			get_prices()
		price_source_timer = time.time()

def empire_ws_main():
	empire_origin = "https://csgoempire.com"
	ws_url = "wss://roulette.csgoempire.com/s/?EIO=3&transport=websocket"
	ws_user_agent = "User-Agent: " + "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:79.0) Gecko/20100101 Firefox/79.0"
	websocket.enableTrace(False)
	ws = websocket.WebSocketApp(ws_url, on_message=empire_message, on_error=on_error, on_close=on_close, header=[ws_user_agent])
	ws.on_open = on_open
	while True:
		ws.run_forever(origin = empire_origin)

def clear_first_items():
	items = fetch_items(1)
	if items == -1:
		time.sleep(delay)
		return clear_first_items()
	for item in items:
		already_fetched[item['assetid']] = 1
	if debug_mode :
		print("Cleared first items fetch")

def rate_limited(url, req):
	while 1:
		retry_after = int(req.headers.get('Retry-After', 0))
		if retry_after == 0:
			print()
			time.sleep(1)
			return
		print(f"\033[KRatelimited, restarting in {retry_after}sec\r", end="")
		time.sleep(1)
		req = requests.get(url)

def increase_index(index):
	if domain == "com" or domain == ".com":
		return 1
	if domain == "gg" or domain == ".gg":
		return 3
	index += 1
	if index == 16:
		index = 1
	return index

def exclude_item(item):
	item_name = item['market_name']
	if "★" in item_name:
		item_name = item_name.replace("★ ", "")
	try :
		f = open('settings.json', 'r', encoding="utf8")
		previous = f.readlines()
		f.close()
		if previous[5][-4] == '"':
			char = ", "
		else :
			char = "" 
		modify = previous[5][0:-3] + f'{char}"{item_name}"],\n'
		previous[5] = modify
		f = open('settings.json', 'w+', encoding="utf8")
		for line in previous:
			f.write(line)
		f.close()
		default_settings()
	except Exception as e:
		print(f"Couldn't exclude item name. Error : {e}")

def unexclude_item(item):
	item_name = item['market_name']
	if "★" in item_name:
		item_name = item_name.replace("★ ", "")
	try :
		f = open('settings.json', 'r', encoding="utf8")
		previous = f.readlines()
		f.close()
		modify = previous[5]
		if f', "{item_name}"' in modify:
			modify = modify.replace(f', "{item_name}"', '')
		else :
			modify = modify.replace(f'"{item_name}"', '')
		previous[5] = modify
		f = open('settings.json', 'w+', encoding="utf8")
		for line in previous:
			f.write(line)
		f.close()
		default_settings()
	except Exception as e:
		print(f"Couldn't unexclude item name. Error : {e}")
	
def default_settings():
	try :
		f = open("settings.json", "r")
	except :
		print(f"{Fore.RED}Settings file not detected. Creating default one...{Fore.RESET}")
		f = open("settings.json", "w+")
		f.write('{\n	"Autowithdraw": {\n		"Min_coin": 30,\n		"Max_coin": 1000,\n		"Included_name": [],\n		"Excluded_name": [],\n		"Bypass_included": [],\n		"Custom_price": true,\n		"Max_custom_price": 12,\n		"Min_waxpeer_listings" : 3,\n		"Min_wax_profit" : 20,\n		"Min_buff_profit" : 10,\n		"Max_profit" : 40,\n		"Price_source" : "buff-waxpeer"\n	},\n	"Settings": {\n		"Debug_mode" : true,\n		"Print_delays" : false,\n		"Print_date" : true,\n		"Delay" : 0.85,\n		"Skip_out_of_range" : true,\n		"Withdraw_only_once" : true,\n		"Skip_first_load" : true,\n		"Coin_to_usd" : 0.6197,\n		"Yuan_to_usd" : 0.143139\n	},\n	"Authentification": {\n		"Empire_cookies" : "Replace your cookies here",\n		"Empire_pin" : 1511,\n		"Empire_uuid" : "Replace uuid here"\n	}\n}\n')

def get_settings():
	try :
		f = open('settings.json', 'r')
		settings = json.load(f)
		global min_coin, max_coin, included_name, excluded_name, bypass_included, custom_price, max_custom, waxpeer_lists, min_wax_profit, min_buff_profit, min_market_profit, market_list, market_fee, max_profit, price_source
		min_coin =			settings['Autowithdraw']['Min_coin']
		max_coin =			settings['Autowithdraw']['Max_coin']
		included_name =		settings['Autowithdraw']['Included_name']
		excluded_name =		settings['Autowithdraw']['Excluded_name']
		bypass_included =	settings['Autowithdraw']['Bypass_included']
		custom_price = 		settings['Autowithdraw']['Custom_price']
		max_custom =		settings['Autowithdraw']['Max_custom_price']
		waxpeer_lists =		settings['Autowithdraw']['Min_waxpeer_listings']
		min_wax_profit =	settings['Autowithdraw']['Min_wax_profit']
		min_buff_profit =	settings['Autowithdraw']['Min_buff_profit']
		min_market_profit =	settings['Autowithdraw']['Min_market_profit']
		market_list =		settings['Autowithdraw']['Min_market_listings']
		market_fee =		settings['Autowithdraw']['Market_fee']
		max_profit =		settings['Autowithdraw']['Max_profit']
		price_source =		settings['Autowithdraw']['Price_source']
		if price_source == "waxpeer":
			price_source = 1
		elif price_source == "buff":
			price_source = 2
		elif price_source == "buff-waxpeer":
			price_source = 3
		elif price_source == "buff-market":
			price_source = 4
		else:
			price_source = 0

		global website, domain, abuse, buff_fee, buff_price_s, debug_mode, print_delays, delay, timeout_s, skip_ofr, skip_unw, withdraw_once, skip_first, p_date, coin_to_usd, yuan_to_usd
		website =			settings['Settings']['Website']
		domain =			settings['Settings']['Domain']
		buff_fee =			settings['Settings']['Buff_fee']
		buff_price_s =		settings['Settings']['Buff_price']
		debug_mode =		settings['Settings']['Debug_mode']
		print_delays =		settings['Settings']['Print_delays']
		p_date =			settings['Settings']['Print_date']
		delay =				settings['Settings']['Delay']
		timeout_s =			settings['Settings']['Timeout']
		skip_ofr =			settings['Settings']['Skip_out_of_range']
		skip_unw =			settings['Settings']['Skip_unwanted']
		withdraw_once =		settings['Settings']['Withdraw_only_once']
		skip_first =		settings['Settings']['Skip_first_load']
		coin_to_usd = 		settings['Settings']['Coin_to_usd']
		yuan_to_usd =		settings['Settings']['Yuan_to_usd']

		global uuid, cookies, pin_code, rollbit_cookies, rollbit_useragent
		cookies =			settings['Authentification']['Empire_cookies']
		# cookies = f'PHPSESSID{cookies.split("PHPSESSID")[1].split(";")[0]}; do_not_share_this_with_anyone_not_even_staff{cookies.split("do_not_share_this_with_anyone_not_even_staff")[1].split(";")[0]};'
		pin_code =			settings['Authentification']['Empire_pin']
		uuid =				settings['Authentification']['Empire_uuid']
		rollbit_cookies =	settings['Authentification']['Rollbit_cookies']
		rollbit_useragent =	settings['Authentification']['Rollbit_useragent']

		global com_f_url, gg_f_url, url_withdraw, url_token, empire_headers_withdraw, already_fetched, url_inventory, url_buff_db, url_rollbit_w, url_user, rollbit_headers_withdraw, url_market
		if website == "csgoempire-abuse":
			url = "3"
		else :
			url = "1"
		com_f_url = f"https://csgoempire.com/api/v2/p2p/inventory/{url}"
		gg_f_url = f"https://csgoempire.gg/api/v2/p2p/inventory/{url}"
		url_withdraw = "https://csgoempire.com/api/v2/trade/withdraw"
		url_token = "https://csgoempire.com/api/v2/user/security/token"
		url_inventory = "https://csgoempire.com/api/v2/inventory/user?app=730"
		url_buff_db = "https://buff-prices-eb699.firebaseio.com/buff-prices-2/.json"
		url_rollbit_w = "https://api.rollbit.com/steam/withdraw"
		url_user = "https://csgoempire.com/api/v2/user"
		url_market = "https://market.csgo.com/api/v2/prices/USD.json"
		empire_headers_withdraw = {'Cookie':cookies, 'content-type':"application/json"}
		rollbit_headers_withdraw = {'Cookie':rollbit_cookies, 'User-Agent': rollbit_useragent, 'Content-Type': 'application/json; charset=UTF-8'}
		already_fetched = {}

	except KeyboardInterrupt:
		quit()
	except Exception as e:
		print(f"{Fore.RED}Error parsing settings : {Fore.RESET}", e)
		print("\nTraceback : \n\n")
		traceback.print_exc()
		default_settings()
		quit()

def refresh_token():
	global token
	token_payload = json.dumps({"code":pin_code, "uuid":uuid})
	try :
		token_response= requests.post(url_token,data=token_payload, headers=empire_headers_withdraw)
		token_json = token_response.json()
	except Exception as e:
		if debug_mode:
			print(f"Getting the token request failed, error code : {e}")
		time.sleep(delay)
		refresh_token()
		return
	try :
		if int(token_response.status_code/100) != 2:
			print(f"{Fore.RED}Getting the token failed. Status code : {token_response.status_code}{Fore.RESET}")
			time.sleep(delay)
			refresh_token()
		token = token_json["token"]
	except Exception as e:
		print(f"{Fore.RED}Problem while acquiring Token. raw data :{Fore.RESET}")
		print(token_json)
		time.sleep(delay)
		refresh_token()
		return
	if debug_mode :
		print("Refreshed token")

def get_waxpeer_profit(item_name, price):
	if len(waxpeer_prices) <= 0:
		return -1000, 0 
	try :
		item_price = waxpeer_prices[item_name][0]
		count = waxpeer_prices[item_name][1]
	except :
		return -999, 0
	price *= coin_to_usd
	profit = (item_price * 0.941 * 0.98) / price
	profit = (profit - 1) * 100
	return int(profit), int(count)

def get_waxpeer_prices():
	global waxpeer_prices
	url = f"https://api.waxpeer.com/v1/prices?game=csgo&min_price=0&max_price=9999999999999"
	try:
		req = requests.get(url)
		data = req.json()
	except :
		print(Fore.RED + "Getting waxpeer prices request failed." + Fore.RESET)
		time.sleep(3)
		get_waxpeer_prices()
		return
	if (req.status_code != 200):
		print(Fore.RED + f"Getting waxpeer prices request failed. status code : {req.status_code}" + Fore.RESET)
		time.sleep(3)
		get_waxpeer_prices()
		return 
	if "success" not in data or (data["success"] != True):
		print(Fore.RED + f"Getting waxpeer prices request failed, content : {data}" + Fore.RESET)
		time.sleep(3)
		get_waxpeer_prices()
		return
	waxpeer_prices = {}
	for item in data["items"]:
		waxpeer_prices.update({item["name"]:[float(item["min"])/1000, float(item['count'])]})
	if debug_mode :
		print("Acquired all waxpeer lowest prices")

def get_buff_profit(item_name, price):
	if len(buff_prices) <= 0:
		return -1000
	try :
		if buff_price_s == "sell":
			item_price = buff_prices[item_name][0]
		else :
			item_price = buff_prices[item_name][1]		
	except :
		return -999
	if buff_fee:
		fee = 0.975
	else :
		fee = 1
	profit = item_price * yuan_to_usd * fee / (price * coin_to_usd)
	profit = (profit - 1) * 100
	return int(profit)

	buff_fee
	buff_price_s

def get_buff_prices():
	global buff_prices
	try:
		req = requests.get(url_buff_db)
		buff_prices = req.json()
	except Exception as e:
		print(Fore.RED + "Getting buff prices request failed." + Fore.RESET)
		print(e)
		time.sleep(3)
		get_buff_prices()
		return
	if (req.status_code != 200):
		print(Fore.RED + f"Getting buff prices request failed. status code : {req.status_code}" + Fore.RESET)
		time.sleep(3)
		get_buff_prices()
		return 
	if debug_mode :
		print("Acquired all buff lowest listings from database")

def get_market_profit(item_name, price):
	if len(market_prices) <= 0:
		return -1000, 0 
	try :
		item_price = market_prices[item_name][0]
		count = market_prices[item_name][1]
	except :
		return -999, 0
	price *= coin_to_usd
	profit = (item_price * (1 - (market_fee / 100)) * 0.95) / price
	profit = (profit - 1) * 100
	return int(profit), int(count)

def get_market_prices():
	global market_prices
	try:
		req = requests.get(url_market)
		market_prices = req.json()
	except Exception as e:
		print(Fore.RED + "Getting market prices request failed." + Fore.RESET)
		print(e)
		time.sleep(3)
		get_market_prices()
		return
	if int(req.status_code/100) != 2:
		print(Fore.RED + f"Getting market prices request failed. status code : {req.status_code}" + Fore.RESET)
		time.sleep(3)
		get_market_prices()
		return
	try :
		temp = market_prices['items']
		market_prices = {}
		for item in temp:
			market_prices[item['market_hash_name']] = [round(float(item['price']), 3), int(item['volume'])]
	except Exception as e:
		print(Fore.RED + f"Formating market prices failed : {e}" + Fore.RESET)
	if debug_mode :
		print("Acquired all market lowest listings")

def get_prices():
	if price_source == 1:
		get_waxpeer_prices()
	elif price_source == 2:
		get_buff_prices()
	elif price_source == 3:
		get_buff_prices()
		get_waxpeer_prices()
	elif price_source == 4:
		get_buff_prices()
		get_market_prices()

def print_item(item, name, price, profit, profit_2, count, color):
	if custom_price:
		if website == "rollbit":
			custom_string = f" {item.get('markup', 0)}%"
		else :
			custom_string = f" {item.get('custom_price', 0)}%"
	else:
		custom_string = ""
	if p_date :
		now = datetime.datetime.now()
		date_str = f'{now.strftime("%d/%m %H:%M")} '
	else:
		date_str = ""
	if price_source == 2:
		profit_str = f' {profit:3.0f}%'
	elif price_source == 1:
		profit_str = f' {profit:3.0f}% {count:3.0f}l'
	elif price_source == 3 or price_source == 4:
		profit_str = f' {profit:3.0f}% {count:3.0f}l {profit_2:3.0f}%'
	else:
		profit_str = ""
	to_print = f"{date_str}{color}{price:7.2f}{profit_str} {name}{custom_string}\n{Fore.RESET}"
	return to_print

def print_tracked(pruchased_item, profit, profit_2):
	try :
		f = open("../Buy_prices.txt", "a", encoding="utf8")
		price = pruchased_item['market_value']/100
		if custom_price:
			custom_string = f" Custom price : {pruchased_item.get('custom_price', 0)}%"
		else:
			custom_string = ""
		if p_date :
			now = datetime.datetime.now()
			date_str = f'{now.strftime("%d/%m %H:%M")} '
		else:
			date_str = ""
		if price_source == 1 or price_source == 2:
			profit_str = f' Excpected profit : {profit:3.0f}%'
		elif price_source == 3:
			profit_str = f' Excpected profit : {profit:3.0f}%W {profit_2:3.0f}%B'
		elif price_source == 4:
			profit_str = f' Excpected profit : {profit:3.0f}%M {profit_2:3.0f}%B'
		else:
			profit_str = ""
		to_write = f'{date_str} Price:"{price*coin_to_usd:.2f}" Name:"{pruchased_item["market_name"]}"{profit_str}{custom_string} Website : {website}\n'
		f.write(to_write)
	except Exception as e:
		print(f"{Fore.RED}Error while printing the item withdrawn : \n{Fore.RESET}{str(e)}")
		traceback.print_exc()

def print_tracked_2(pruchased_item, profit, profit_2):
	try :
		f = open("../Buy_prices_trash.txt", "a", encoding="utf8")
		price = pruchased_item['market_value']/100
		if custom_price:
			custom_string = f" Custom price : {pruchased_item.get('custom_price', 0)}%"
		else:
			custom_string = ""
		if p_date :
			now = datetime.datetime.now()
			date_str = f'{now.strftime("%d/%m %H:%M")} '
		else:
			date_str = ""
		if price_source == 1 or price_source == 2:
			profit_str = f' Excpected profit : {profit:3.0f}%'
		elif price_source == 3:
			profit_str = f' Excpected profit : {profit:3.0f}%W {profit_2:3.0f}%B'
		elif price_source == 4:
			profit_str = f' Excpected profit : {profit:3.0f}%M {profit_2:3.0f}%B'
		else:
			profit_str = ""
		to_write = f'{date_str} Price:"{price*coin_to_usd:.2f}" Name:"{pruchased_item["market_name"]}"{profit_str}{custom_string} Website : {website}\n'
		f.write(to_write)
	except Exception as e:
		print(f"{Fore.RED}Error while printing the item withdrawn : \n{Fore.RESET}{str(e)}")
		traceback.print_exc()

def withdraw_tracking(purchased_item, profit, profit_2):
	total_time = 0
	if withdraw_once:
		exclude_item(purchased_item)
	while 1:
		try :
			req = requests.get(url_inventory, headers={'Cookie':cookies})
			current_inv = req.json()['data']
			current_ids = []
			for item in current_inv:
				current_ids.append(item.get('asset_id', 0))
			break
		except :
			time.sleep(15)
			continue
	while 1:
		try :
			begin = time.time()
			req = requests.get(url_inventory, headers={'Cookie':cookies})
			new_inv = req.json()['data']
			for item in new_inv:
				if item.get('asset_id', 0) not in current_ids:
					if item['market_name'] == purchased_item['market_name']:
						print_tracked(purchased_item, profit, profit_2)
						reverse_print_refresh()

						return
					current_ids.append(item.get('asset_id', 0))
			time.sleep(15)
			total_time += time.time() - begin
			if total_time >= 720:
				unexclude_item(purchased_item)
				return
		except :
			time.sleep(15)
			continue

def	empire_withdraw(item, profit, profit_2, count, name, price):
	item_payload = json.dumps({"item_ids": [item["id"]],"bot_id":item["bot_id"],"security_token": token})
	try :
		withdraw_response = requests.post(url_withdraw,data=item_payload, headers=empire_headers_withdraw)
		withdraw_json = withdraw_response.json()
	except :
		print(f"{Fore.RED}Request to withdraw {item['name']} failed, trying again{Fore.RESET}")
		time.sleep(delay)
		return (empire_withdraw(item, profit, profit_2, count, name, price))
	to_print = print_item(item, name, price, profit, profit_2, count, Fore.GREEN)+ f"{Fore.MAGENTA}Trying to withdraw...\n{Fore.RESET}"
	if withdraw_json.get("success", False):
		to_print += f"{Fore.GREEN}Item successfully withdrawn{Fore.RESET}\n"
		loop = asyncio.get_event_loop()
		loop.run_in_executor(None, withdraw_tracking, item, profit, profit_2)
		print_tracked_2(item, profit, profit_2)
		reverse_print_refresh()
	else:
		to_print += Fore.RED
		if "message" in withdraw_json:
			to_print += f"{withdraw_json.get('message', 'failed without message (bug)')}\n"
		else:
			to_print += f"{withdraw_json}\n"
		to_print += Fore.RESET
	return to_print

def advanced_filtering(item, price, name):
	profit = 0
	profit_2 = 0
	count = 0
	if price_source == 1:
		profit, count = get_waxpeer_profit(name, price)
		if profit == -1000:
			return f"{Fore.RED}Waxpeer database is empty.\n{Fore.RESET}"
		if profit == -999:
			if not skip_unw:
				return f"{Fore.CYAN}Item not in waxpeer database : {name}{Fore.RESET}\n"
			return ""
		if (profit >= min_wax_profit and profit <= max_profit) and count > waxpeer_lists:
			profitable = True
		else:
			profitable = False
	if price_source == 2:
		profit = get_buff_profit(name, price)
		if profit == -999:
			if not skip_unw:
				return f"{Fore.CYAN}Item not in buff database : {name}{Fore.RESET}\n"
			return ""
		if profit == -1000:
			return f"{Fore.RED}Buff database is empty.\n{Fore.RESET}"
		if (profit >= min_buff_profit and profit <= max_profit):
			profitable = True
		else:
			profitable = False
	if price_source == 3:
		profit, count = get_waxpeer_profit(name, price)
		if profit == -1000:
			return f"{Fore.RED}Waxpeer database is empty.\n{Fore.RESET}"
		if profit == -999:
			if not skip_unw:
				return f"{Fore.CYAN}Item not in waxpeer database : {name}{Fore.RESET}\n"
			return ""
		profit_2 = get_buff_profit(name, price)
		if profit_2 == -999:
			if not skip_unw:
				return f"{Fore.CYAN}Item not in buff database : {name}{Fore.RESET}\n"
			return ""
		if profit_2 == -1000:
			return f"{Fore.RED}Buff database is empty.\n{Fore.RESET}"
		if (profit >= min_wax_profit and profit <= max_profit) and count > waxpeer_lists and (profit_2 >= min_buff_profit and profit_2 <= max_profit):
			profitable = True
		else:
			profitable = False
	if price_source == 4:
		profit, count = get_market_profit(name, price)
		if profit == -1000:
			return f"{Fore.RED}Market database is empty.\n{Fore.RESET}"
		if profit == -999:
			if not skip_unw:
				return f"{Fore.CYAN}Item not in market database : {name}{Fore.RESET}\n"
			return ""
		profit_2 = get_buff_profit(name, price)
		if profit_2 == -999:
			if not skip_unw:
				return f"{Fore.CYAN}Item not in buff database : {name}{Fore.RESET}\n"
			return ""
		if profit_2 == -1000:
			return f"{Fore.RED}Buff database is empty.\n{Fore.RESET}"
		if (profit >= min_market_profit and profit <= max_profit) and count > market_list and (profit_2 >= min_buff_profit and profit_2 <= max_profit):
			profitable = True
		else:
			profitable = False
	if "★" in name and "|" not in name:
		name += " | Vanilla"
	
	if ((any(x.lower() in name.lower() for x in included_name) and not any(x.lower() in name.lower() for x in excluded_name)) or any(x.lower() in name.lower() for x in bypass_included)) and (skip_ofr or (price >= min_coin and price <= max_coin)) and (not price_source or profitable):
			if website != "rollbit":
				to_print = empire_withdraw(item, profit, profit_2, count, name, price)
			else :
				to_print = rollbit_withdraw(item, profit, profit_2, count, name, price)
	else:
		if not skip_unw:
			to_print = print_item(item, name, price, profit, profit_2, count, Fore.CYAN)
		else :
			to_print = ""

	return to_print

def basic_filtering(items):
	to_print = ""
	for item in items:
		if already_fetched.get(item['assetid'], 0) == 0:
			if custom_price or item.get('custom_price', 0) == 0:
				if not custom_price or item.get('custom_price', 0) <= max_custom:
					price = item['market_value']/100
					if not skip_ofr or (price >= min_coin and price <= max_coin):
						to_print += advanced_filtering(item, price, item['market_name'])
			already_fetched[item['assetid']] = 1
	if len(to_print) > 0:
		print(to_print, end="")

def fetch_items(index):
	url = com_f_url
	if index % 3 == 0:
		url = gg_f_url
	try :
		if print_delays:
			begin = time.time()
		req = requests.get(url, timeout = timeout_s)
		if print_delays:
			print(f"Time to request items : {(time.time() - begin)*1000:.4f}ms")
	except Exception as e:
		if debug_mode:
			print(f"Fetching items request failed : {e}")
		return -1
	if req.status_code == 200:
		try :
			status = req.headers['CF-Cache-Status']
			# print(status)
			if status == "UPDATING":
				time.sleep(1.2)
			data = req.json()
			return data
		except :
			print(f"{Fore.RED}Request result can't be jsoned, printing raw response{Fore.RESET}")
			print(req.text())
			return -1
	if req.status_code == 429:
		rate_limited(url, req)
		return -1
	if int(req.status_code / 100) != 2:
		print(f"{Fore.RED}Error fetching items, status_code : {req.status_code}{Fore.RESET}")
		return -1

def initialization():
	global debug_mode
	debug_mode = 1
	print("Initialization...")
	reverse_print_refresh()
	print("reverse text file updated")
	get_settings()
	if website == "rollbit":
		if price_source:
			get_prices()
		rollbit_main()
		return
	if website == "csgoempire-ws":
		if price_source:
			get_prices()
		empire_ws_main()
	if skip_first:
		clear_first_items()
	refresh_token()
	if price_source:
		get_prices()

def main():
	global flag
	flag = 0
	index = 1
	total_time = 0
	initialization()
	if website == "rollbit":
		return
	if website == "csgoempire-ws":
		return
	if domain == "gg":
		index = 3
	while 1:
		begin = time.time()
		fetched = fetch_items(index)
		if fetched == -1:
			pass
		else:
			if print_delays:
				time_to_treat = time.time()
			basic_filtering(fetched)
			if print_delays:
				print(f"Time to treat items : {(time.time() - time_to_treat)*1000:.4f}ms")
		index = increase_index(index)
		exec_time = (time.time() - begin)
		sleep = delay - exec_time
		if sleep > 0:
			time.sleep(sleep)
		if print_delays:
			print(f"Loop time : {(time.time() - begin)*1000:.2f}ms")
		if total_time > 540:
			refresh_token()
			if price_source :
				get_prices()
			if not skip_first:
				already_fetched = {}
			total_time = 0
		total_time += time.time() - begin
		flag = 1

def pre_main():
	while 1:
		try :
			main()
			time.sleep(delay)
		except KeyboardInterrupt:
			quit()
		except Exception as e:
			print(f"{Fore.RED}Unhandled exception caught :{Fore.RESET}")
			print(e)
			traceback.print_exc()
			time.sleep(1)

loop = asyncio.get_event_loop()
loop.run_until_complete(pre_main())
quit()
