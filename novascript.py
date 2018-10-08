#!/usr/bin/python

import time
import hmac
import hashlib
import base64
import requests
import ast
import datetime
import time
import sys

#*/1 * * * * /usr/bin/python2 /home/cjin/scripts/novascript.py
# https://novaexchange.com/remote/faq/

API_KEY = "PUT KEY HERE"
API_SECRET = "SUPER SECRET KEY HERE"

public_set = set([ "markets", "market/info", "market/orderhistory", "market/openorders" ]) # optional
private_set = set([ "getbalances", "getbalance", "getdeposits", "getwithdrawals", "getnewdepositaddress", "getdepositaddress", "myopenorders", "myopenorders_market", "cancelorder", "withdraw", "trade", "tradehistory", "getdeposithistory", "getwithdrawalhistory", "walletstatus" ])

url = "https://novaexchange.com/remote/v2/"

def api_query( method, req = None ):
	url = "https://novaexchange.com/remote/v2/"
	if not req:
		req = {}
	if method.split('/')[0][0:6] == 'market':
		r = requests.get( url + method + '/', timeout = 60 )
	elif method.split('/')[0] in private_set:
		url += 'private/' + method + '/' + '?nonce=' + str( int( time.time() ) )
		req["apikey"] = API_KEY
		req["signature"] = base64.b64encode( hmac.new( API_SECRET, msg = url, digestmod = hashlib.sha512 ).digest() )
		headers = {'content-type': 'application/x-www-form-urlencoded'}
		r = requests.post( url, data = req, headers = headers, timeout = 60 )
	return r.text

#print(last_sell) #= ast.literal_eval(last_sell)
saved_orderid= None
base="/home/cjin/scripts/"

def get_last_order(bid=0):
	
	try:    	
		#get open orders
		tmp=api_query( "myopenorders" )
		d = ast.literal_eval(tmp)
		if d['items']==[]:
			if debug:
				print("DEBUG: get_last_order()  no order.!")
			tmpstr=getdatetime()+"ERROR(getlastorder) no orders prev orders! \n"
        		savetofile (tmpstr,"loggylog", True)
			lo=bid
		else:
			lo=str(d['items'][0]['orderid'])
		if debug:
			print("DEBUG: get_last_order()  complete!")
	except:
		lo=0
		e = sys.exc_info()[0]
       		tmpstr=getdatetime()+"ERROR(getlastorder):"+str(e)+"\n"
        	savetofile (tmpstr,"loggylog", True)
		print("get_last_order() Excetion ") if debug else ""
	return str(lo)

def get_last_trade(_lastsell):
	_ls_tmp =  ast.literal_eval(_lastsell)
	if _ls_tmp['status'] == "success" and _ls_tmp['tradetype']== "SELL":
		_saved_orderid= _ls_tmp["tradeitems"][0]["orderid"]
	return str(_saved_orderid)

def savetofile(data,fn="sprouts",append=False):
	op="w+"
	if append:
		op="a"	
	with open(base+fn, op) as fh:
		fh.write(data)
	fh.close()
	return True

def readfromfile(fn="sprouts"):
	fh = open(base+fn,"r")
	data=fh.read().replace('\n', '')
	fh.close()
	return str(data)

def getdatetime():
	tmp=time.strftime("%Y-%m-%d %H:%M")
	return str(tmp)

def checkprice(market="DOGE_SPRT"):
    price=0
    try:
        res=api_query("market/info/" + market )
        ls_tmp =  ast.literal_eval(res)
        price=ls_tmp['markets'][0]['bid']
    except:
        e = sys.exc_info()[0]
        tmpstr=getdatetime()+"ERROR(checkprice):"+str(e)+"\n"
        savetofile (tmpstr,"loggylog", True)
        price=0
    return price

#price=0.00082000
#amt=50000000
debug = True

def exectrade(default_price=0.00080,amount=50000000,market="DOGE_SPRT",tradetype="SELL",low_price=0.00061):
    bid=checkprice()
    try:	
	last_order=get_last_order(bid)
        my_current_price=readfromfile("price")
	if debug:
		print("exectrade() got current price from file!")
    except:
        e = sys.exc_info()[0]
        tmpstr=getdatetime()+"ERROR(setting my_current_price-exectrade): "+str(e)+"\n"
        savetofile (tmpstr,"loggylog", True) #log error
        my_current_price=default_price #adjust current price
        savetofile(str(my_current_price), "price") #fix for next time
	if debug:
		print("exectrade() exception getting my_current_price")
    #if float(my_current_price) < float(1):
    #	my_current_price = default_price
    if float(my_current_price) < float(low_price):
        my_current_price = low_price
    
    print(bid) if debug else ""
    print(my_current_price) if debug else ""
    
    
    if float(bid) < float(low_price):
        tmpstr=str(getdatetime()+": Nothing to change. bid too low("+str(bid)+"). last order:"+last_order+"\n")
    
    elif float(bid) > float(my_current_price):
        my_current_price = bid ####  adjust curr price upward
        savetofile(str(bid), "price")  ##### NEW PRICE
        last_sell=api_query( "trade/" + market, { 'tradebase': 0, 'tradetype': tradetype, 'tradeprice': my_current_price, 'tradeamount': amount } )
        last_order=get_last_trade(last_sell) 
	tmpstr=str(getdatetime()+": trade! bid > lp   p("+ str(my_current_price) +") last order:"+str(last_order)+"\n")
	savetofile(last_order) #save to sprouts file
	
    elif last_order != readfromfile() and float(bid) >= float(low_price):
        ##### bid is somewhere between low price and current price. trade saved price or default
	my_current_price = float(bid) + .000001
        last_sell=api_query( "trade/" + market, { 'tradebase': 0, 'tradetype': tradetype, 'tradeprice': my_current_price, 'tradeamount': amount } )
        last_order=get_last_trade(last_sell)
	savetofile(str(my_current_price), "price") ##### NEW PRICE
	tmpstr=str(getdatetime()+": trade! no order  p("+ str(my_current_price) +") last order:"+str(last_order)+"\n")
	savetofile(last_order) #save to sprouts file
		
    else:
        #### bid didnt go up nor is it too low and theres already an order out there
        tmpstr=str(getdatetime()+": Nothing to change.  last order:"+last_order+"\n")
    
    savetofile (tmpstr,"loggylog", True)
    #savetofile(last_order) #save to sprouts file
    return True

exectrade()
 
