import requests, time

api = "FW2u842L8ou2QemRN48d15RrNn7bOMw"
delay = 0.5
remove_listings = False
list_tradable = True

def add_to_sale(item_id, name):
	url = f"https://market.csgo.com/api/v2/add-to-sale?key={api}&id={item_id}&price={99999900}&cur=RUB"
	req = requests.get(url)
	if int(req.status_code/100) == 2:
		print(f"Added {name}")
		return
	else:
		print("listing item failed")

def get_inventory():
	url = f"https://market.csgo.com/api/v2/my-inventory/?key={api}"
	req = requests.get(url)
	if int(req.status_code/100) == 2:
		return req.json()['items']
	else:
		print("Getting your items failed")

def remove_all_listings():
	url = f"https://market.csgo.com/api/v2/remove-all-from-sale?key={api}"
	req = requests.get(url)
	if int(req.status_code/100) == 2:
		print("Removed all listed items")
		return
	else:
		print("Removing all items failed")

def list_all_tradables():
	inventory = get_inventory()
	for item in inventory:
		add_to_sale(item['id'], item['market_hash_name'])
		time.sleep(delay)

if remove_listings:
	remove_all_listings()
	time.sleep(delay)
if list_tradable:
	list_all_tradables()
