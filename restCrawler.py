import tweepy
import json
from pymongo import MongoClient
from datetime import datetime
import time
import sys

import emoji
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score

#sets up MongoDB host
MONGO_HOST = 'mongodb://localhost/twitterdb'


#  please put your credentials below - very important
consumer_key = "Y7Yv9GWbovGLcVfXqui9GRqkC"
consumer_secret ="3bgadhXK5UX81liQdMb7mwVeBgAy9A2xgFTNT8ViIi3TeQOVXZ"
access_token ="901441890670829568-jMxcpuH2vLuNtE0PQGBq5cse1tcIpqx"
access_token_secret ="8v3ymcUyE648hm1ucyUD9aRjcyCtwLDUPMz4rlZvIYevZ"


auth = tweepy.OAuthHandler(consumer_key, consumer_secret )
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth,parser=tweepy.parsers.JSONParser())
if (not api):
    print('Can\'t authenticate')
    print('failed cosumeer id ----------: ', consumer_key )
# set DB DETAILS


# this is to setup local Mongodb
client = MongoClient(MONGO_HOST) #is assigned local port
dbName = "twitterdb" # set-up a MongoDatabase
db = client.twitterdb
collName = 'tweets' # here we create a collection
tweet_collection = db[collName] #  This is for the Collection  put in the DB


def strip_emoji(text):
    #  copied from web - don't remeber the actual link
    new_text = re.sub(emoji.get_emoji_regexp(), r"", text)
    return new_text

def cleanList(text):
    #  copied from web - don't remeber the actual link
    #remove emoji it works
    text = strip_emoji(text)
    text.encode("ascii", errors="ignore").decode()

    return text

def processTweets(tweet):
    #  this module is for cleaning text and also extracting relevant twitter feilds
    # initialise placeholders
    place_countrycode  =None
    place_name  =None
    place_country =None
    place_coordinates =None
    source =None
    exactcoord =None
    place=None
    qtweet=False
    retweet=False

    # Pull important data from the tweet to store in the database.
    try:
        created = tweet['created_at']
        tweet_id = tweet['id_str']  # The Tweet ID from Twitter in string format
        username = tweet['user']['screen_name']  # The username of the Tweet author
        # followers = t['user']['followers_count']  # The number of followers the Tweet author has
        text = tweet['full_text']  # The entire body of the Tweet
    except Exception as e:
        # if this happens, there is something wrong with JSON, so ignore this tweet
        print("bad tweet")
        return None

    try:
        # // deal with truncated
        if(tweet['truncated'] == True):
            text = tweet['extended_tweet']['full_text']
        elif(text.startswith('RT') == True):
            # print(' tweet starts with RT **********')
            # print(text)
            try:
                if( tweet['retweeted_status']['truncated'] == True):
                    # print("in .... tweet.retweeted_status.truncated == True ")
                    text = tweet['retweeted_status']['extended_tweet']['full_text']
                    # print(text)
                else:
                    text = tweet['retweeted_status']['full_text']

            except Exception as e:
                pass

    except Exception as e:
        print(e)
    # print(text)
    text = cleanList(text)
    # print(text)
    entities = tweet['entities']
    # print(entities)
    mentions =entities['user_mentions']
    mList = []

    for x in mentions:
        # print(x['screen_name'])
        mList.append(x['screen_name'])
    hashtags = entities['hashtags']  # Any hashtags used in the Tweet
    hList =[]
    for x in hashtags:
        # print(x['screen_name'])
        hList.append(x['text'])
    # if hashtags == []:
    #     hashtags =''
    # else:
    #     hashtags = str(hashtags).strip('[]')
    source = tweet['source']

    exactcoord = tweet['coordinates']
    coordinates = None
    if(exactcoord):
        # print(exactcoord)
        coordinates = exactcoord['coordinates']
        # print(coordinates)
    geoenabled = tweet['user']['geo_enabled']
    location = tweet['user']['location']


    if ((geoenabled) and (text.startswith('RT') == False)):
        # print(tweet)
        # sys.exit() # (tweet['geo']):
        try:
            if(tweet['place']):
                # print(tweet['place'])
                place_name = tweet['place']['full_name']
                place_country = tweet['place']['country']
                place_countrycode   = tweet['place']['country_code']
                place_coordinates   = tweet['place']['bounding_box']['coordinates']
        except Exception as e:
            print(e)
            print('error from place details - maybe AttributeError: ... NoneType ... object has no attribute ..full_name ...')
    try:
        if(text.startswith('RT') == True):
            retweet = True
    except Exception as e:
        print(e)

    try:
        if(tweet['quoted_status']):
            qtweet = True
    except Exception as e:
        print(e)
    tweet1 = {'_id' : tweet_id, 'date': created, 'username': username,  'text' : text,  'geoenabled' : geoenabled,  'coordinates' : coordinates,  'location' : location,  'place_name' : place_name, 'place_country' : place_country, 'country_code': place_countrycode,  'place_coordinates' : place_coordinates, 'hashtags' : hList, 'mentions' : mList, 'source' : source, 'retweet':retweet, 'quote_tweet':qtweet}
    return tweet1

def getText(tweet_collection):
    usernames,hashtags,text = [],[],[]
    alldata = tweet_collection.find()
    for tweet in alldata:

        ulower = str(tweet['username']).lower()
        htlower = str(tweet['hashtags']).lower()
        tlower = str(tweet['text']).lower()
        usernames.append(ulower)
        hashtags.append(htlower)
        text.append(tlower)

    return usernames,hashtags,text
    
def cluster(usernames,hashtags,texts):
    vectorizer = TfidfVectorizer(stop_words='english')
    n = 12

    username_vector = vectorizer.fit_transform(usernames)
    hashtag_vector = vectorizer.fit_transform(hashtags)
    text_vector = vectorizer.fit_transform(texts)

    usernames_cluster = KMeans(n_clusters=n,init='k-means++',max_iter=100,n_init=1)
    usernames_cluster.fit(username_vector)

    hashtags_cluster = KMeans(n_clusters=n,init='k-means++',max_iter=100,n_init=1)
    hashtags_cluster.fit(hashtag_vector)

    text_cluster = KMeans(n_clusters=n,init='k-means++',max_iter=100,n_init=1)
    text_cluster.fit(text_vector)

    return vectorizer,usernames_cluster,hashtags_cluster,text_cluster

def clusterize(vectorizer,group):
    n = 12
    centroids = group.cluster_centers_.argsort()[:,::-1]
    text = vectorizer.get_feature_names()
    clusters = []
    for centre in range(n):
        print ("CLUSTER %d:" % centre)
        cluster = []
        for i in centroids[centre, :5]:
            print (' %s' % text[i])
            cluster.append(text[i])
        clusters.append(cluster)
    return clusters




#Set up the listener. The 'wait_on_rate_limit=True' is needed to help with Twitter API rate limiting.

# WORDS = ['manhattan' , 'new york city', 'statue of liberty']
# LOCATIONS = [ -75,40,-72,42] # new york city
#Loc_UK = [-10.392627, 49.681847, 1.055039, 61.122019] # UK and Ireland
# Words_UK =["Boris", "Prime Minister", "Tories", "UK", "London", "England", "Manchester", "Sheffield", "York", "Southampton", \
#  "Wales", "Cardiff", "Swansea" ,"Banff", "Bristol", "Oxford", "Birmingham" ,"Scotland", "Glasgow", "Edinburgh", "Dundee", "Aberdeen", "Highlands" \
# "Inverness", "Perth", "St Andrews", "Dumfries", "Ayr" \
# "Ireland", "Dublin", "Cork", "Limerick", "Galway", "Belfast"," Derry", "Armagh" \
# "BoJo", "Labour", "Liberal Democrats", "SNP", "Conservatives", "First Minister", "Surgeon", "Chancelor" \
# "Boris Johnson", "BoJo", "Keith Stramer"]

# print("Tracking: " + str(Words_UK))
#  here we ste the listener object
# listener = StreamListener(api=tweepy.API(wait_on_rate_limit=True))
# streamer = tweepy.Stream(auth=auth, listener=listener)
# streamer.filter(locations= Loc_UK, track = Words_UK, languages = ['en'], is_async=True) #locations= Loc_UK, track = Words_UK,
#  the following line is for pure 1% sample
# we can only use filter or sample - not both together
# streamer.sample(languages = ['en'])

# Place =  'London'
Lat   =  '51.450798'
Long  =  '-0.137842'
geoTerm=Lat+','+Long+','+'10km'
#

last_id =  None
# counter =0
# sinceID = None

# results = True

# while results:
#     # print(geoTerm)

#     if (counter < 180 ):
#         try:
#             results = api.search(geocode=geoTerm, count=100, lang="en", tweet_mode='extended', max_id=last_id) #, since_id = sinceID)
#             print(results)
#         except Exception as e:
#             print(e)
#         counter += 1
#     else:
#         #  the following let the crawler to sleep for 15 minutes; to meet the Tiwtter 15 minute restriction
#         time.sleep(15*60)
#
sc,ht,t = getText(tweet_collection)
vec,scK,htK,tK = cluster(sc,ht,t)

clusters = clusterize(vec,tK)

for cluster in clusters:
    name = ""
    for word in cluster:
        name = name + " " + word

    collection = db[name]
    for word in cluster:
        results = api.search(q=word,geocode=geoTerm, count=10, lang="en", tweet_mode='extended', max_id=last_id) #, since_id = sinceID)
        for tweet in results["statuses"]:
            try:
                collection.insert_one(processTweets(tweet))
            except Exception as e:
                print(e)
