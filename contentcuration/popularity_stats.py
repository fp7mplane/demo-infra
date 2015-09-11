import time
#from sets import Set
import pymysql
from collections import defaultdict
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
from urllib.parse import urlparse

def popularity(hours,number,kanony):
	hours = int(hours)
	number = int(number)
	kanony = int(kanony)
	duration=hours*3600
	now=time.time()
	url_to_popularity_duration=defaultdict(int)
	#print("begin to read the database",time.time())
	db = pymysql.connect(host="127.0.0.1",user="root",passwd="root", db="url_pop2")
	cur = db.cursor()
	cur.execute("USE url_pop2")
	#sql= "SELECT * FROM url_timestamp"
	sql= "SELECT * FROM url_timestamp WHERE timestamp>%s"
	cur.execute(sql,now-duration)
	data=cur.fetchall()
	for dtuple in data:
		url=dtuple[0]
		parsed=urlparse(url)
		timestamp=float(dtuple[1])
		if parsed.hostname is not None and  "." in parsed.hostname  and parsed.hostname.split('.')[-2]=="polito":
			continue
		if now-timestamp<(duration): #the URL is within duration observation period
			url_to_popularity_duration[url]+=1
		if now-timestamp > duration: #the URL is not within duration observation period
			break
	print("database read",len(url_to_popularity_duration))
	counter=0
	list_pop = []
	for k,v in sorted(list(url_to_popularity_duration.items()), key=lambda k_v:(k_v[1],k_v[0]),reverse=True ):
		if v<kanony:
			continue	
		if counter>number:
			break
		list_pop.append(k)
		counter+=1
	print("popularity capability stats done")
	return list_pop
