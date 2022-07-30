import time
import datetime
import requests, json

steam_api = '8FCD1975824BBD3345351B72C9DB5C61'


        
def warn_new():
        time.sleep(3)
        requests.post('https://api.pushover.net/1/messages.json?token=amqbxbk5mpnsgxs2pth9rx3b8zr9up&user=ujdktvvczqkreuruqputs5evtinm6u&device=bk-iPhone&title=CSGO-TRADER-BK+-+SQL1&message=tradeofferfound.&priority=1')
    

	
while(True):
	time.sleep(8)
	req = requests.get('https://api.steampowered.com/IEconService/GetTradeOffers/v1/?key=' + steam_api + '&format=json&get_sent_offers=1&get_received_offers=0&get_descriptions=1&active_only=1&historical_only=0')
	data = req.json()
	try:
		for x in data['response']['trade_offers_sent']:
			if data['response']['trade_offers_sent'][0]['trade_offer_state'] == 9:
				print("Confirm mobile quick and go back to sleep : ")
				warn_new()
	except:
		print("notradeofferwasfound")
