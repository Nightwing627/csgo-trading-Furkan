import requests, json, time, datetime
from colorama import Fore, init

cookies = '__cfduid=df2a4e0096ad70be4ba942d568e01dc681599604302; _hjid=61ae96e5-c006-426d-9700-3dc7513db2b8; _ga=GA1.2.1285499907.1599604303; _gid=GA1.2.1727944665.1599604303; _hjAbsoluteSessionInProgress=0; data=32d754ae4ef980c229099fbe170cf5d0; PHPSESSID=diadbgl7fdjlg0guf6edn20s0l; do_not_share_this_with_anyone_not_even_staff=5714809_PN1IyyR4zephbIt9ILN1sczMLXlvKeUTKf61Zn2e4ODNe74IKYCWkKmyljLt; __cf_bm=ff5bd05bc18c726a06952fd98f6d5650d35ea7fd-1599604476-1800-AZjeZHRDsydhx4bj4N95WD9eDSrxtNsYxvBT/ykJXRf3'
uuid = '5c15d256-274c-40a6-a199-7155779c7c20'
coin_to_usd_rate = 0.5935
delay = 0.3
empire_headers_withdraw = {'Cookie':cookies, 'content-type':"application/json", "x-empire-device-identifier":uuid}
init()


def buy_price():
	buy = {}
	try :
		f = open("reverse_Buy_prices.txt", "r", encoding="utf8")
		lines = f.readlines()
		for line in lines:
			price = float(line.split('Price:"')[1].split('"')[0])
			name = line.split('Name:"')[1].split('"')[0]
			buy[name] = price
		return buy
	except :
		return buy

def get_empire_inventory():
    my_items_url = "https://csgoempire.com/api/v2/inventory/user?app=730"
    my_items = []
    try :
        req = requests.get(my_items_url, headers= {'Cookie':cookies})
        data = req.json()["data"]
    except:
        print(Fore.RED + "Request to get my items failed" + Fore.RESET)
        return my_items
    return data


def print_actual_profit(inventory, buy):
	for item in inventory:
		if item['tradable']:
			name = item['name']
			buy_p = buy.get(name, -999)
			if buy_p == -999:
				print(f'{name} not in buy_prices.txt')
			try:
				profit = (((item['raw_price'] / 100) / 1.18) / buy_p) * 100
			except:
				profit = (((item['market_value'] / 100) * 0.5935) / buy_p) * 100
			if profit > 100:
				color1 = Fore.GREEN
			else:
				color1 = Fore.RED
			try:
				print(f"{color1}{profit:6.2f}%  {Fore.YELLOW}{item['raw_price']/100/1.18:7.2f}$  {Fore.CYAN}{name}{Fore.RESET}")
			except:
				print(f"{color1}{profit:6.2f}%  {Fore.CYAN}{item['market_value']/100*0.5935:7.2f}$  {Fore.CYAN}{name}{Fore.RESET}")
			if profit > 107:
				try:
					data = json.dumps({"app":730,"hide_unique_attributes":0,"asset_ids":[item["id"]],"custom_prices":{item["id"]:5}})
					#data = {"app":730,"hide_unique_attributes":false,"asset_ids":["19393656833"],"custom_prices":{"19393656833":12}}
					dep_response = requests.post("https://csgoempire.com/api/v2/trade/deposit", data=data, headers=empire_headers_withdraw)
					#print(dep_response.json())
					print("(%5)Trying to create listing for item:", item['name'])
				except:
					print("Request failed to create listing for:", item['name'])
			if profit > 105 and profit <= 107:
				try:
					data = json.dumps({"app":730,"hide_unique_attributes":0,"asset_ids":[item["id"]],"custom_prices":{item["id"]:7}})
					#data = {"app":730,"hide_unique_attributes":false,"asset_ids":["19393656833"],"custom_prices":{"19393656833":12}}
					dep_response = requests.post("https://csgoempire.com/api/v2/trade/deposit", data=data, headers=empire_headers_withdraw)
					#print(dep_response.json())
					print("(%7)Trying to create listing for item:", item['name'])
				except:
					print("Request failed to create listing for:", item['name'])
			if profit > 103 and profit <= 105:
				try:
					data = json.dumps({"app":730,"hide_unique_attributes":0,"asset_ids":[item["id"]],"custom_prices":{item["id"]:9}})
					#data = {"app":730,"hide_unique_attributes":false,"asset_ids":["19393656833"],"custom_prices":{"19393656833":12}}
					dep_response = requests.post("https://csgoempire.com/api/v2/trade/deposit", data=data, headers=empire_headers_withdraw)
					#print(dep_response.json())
					print("(%9)Trying to create listing for item:", item['name'])
				except:
					print("Request failed to create listing for:", item['name'])
			if profit > 99 and profit <= 103:
				try:
					data = json.dumps({"app":730,"hide_unique_attributes":0,"asset_ids":[item["id"]],"custom_prices":{item["id"]:12}})
					#data = {"app":730,"hide_unique_attributes":false,"asset_ids":["19393656833"],"custom_prices":{"19393656833":12}}
					dep_response = requests.post("https://csgoempire.com/api/v2/trade/deposit", data=data, headers=empire_headers_withdraw)
					#print(dep_response.json())
					print("(%12)Trying to create listing for item:", item['name'])
				except:
					print("Request failed to create listing for:", item['name'])


def main():
	buy = buy_price()
	time.sleep(delay)
	inventory = get_empire_inventory()
#    buy = fill_buy_prices(buy, inventory)
	print_actual_profit(inventory, buy)

main()
