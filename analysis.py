import tweepy
import json
from pymongo import MongoClient
from datetime import datetime
import time
import sys
import numpy
import emoji
import re

MONGO_HOST = 'mongodb://localhost/twitterdb'
client = MongoClient(MONGO_HOST) #is assigned local port
dbName = "twitterdb" # set-up a MongoDatabase
db = client.twitterdb
collName = 'tweets' # here we create a collection
collection = db[collName] #  This is for the Collection  put in the DB

images = 0
videos = 0
gifs = 0
retweets = 0
quotes = 0
geoenabled = 0
coords = 0
twitter_place = 0
generic_location = 0
redundant = 0
verified = 0

#collections = db.collection_names()
#for collection in collections:
for x in db["tweets"].find():
    images += x["photoCount"]
    videos += x["videoCount"]
    gifs += x["gifCount"]
    
    if x["retweet"] == True:
        retweets += 1

    if x["quoteTweet"] == True:
        quotes += 1

    if x["redundant"] == True:
        redundant += 1

    if x["geoenabled"] == True:
        geoenabled += 1

    if x["verified"] == True:
        verified += 1

    if x["coordinates"] != None:
        coords += 1
    elif x["place_name"] != None:
        twitter_place += 1
    elif x["location"] != None:
        generic_location += 1
        
print("images - " + str(images))
print("videos - " + str(videos))
print("gifs - " + str(gifs))
print("verified - " + str(verified))
print("retweets - " + str(retweets))
print("quotes - " + str(quotes))
print("redundant - " + str(redundant))
print("geoenabled - " + str(geoenabled))
print("coordinates - " + str(coords))
print("place objects - " + str(twitter_place))
print("Generic - " + str(generic_location))