import tweepy
import json
from pymongo import MongoClient
from datetime import datetime,date
import time
import sys

import emoji
import re

#sets up MongoDB host
MONGO_HOST = 'mongodb://localhost/twitterdb'


#  please put your credentials below - very important
consumer_key = "Q8JJKByeNa2uWAocFcSHwsI2v"
consumer_secret ="3eLkjKsIltXhP1dxRCJLtvYJLULrw0JdBAgUpy8t1DT2X9tHZM"
access_token ="2506970325-NnZvsAsTdYrcoGtSx7YEldFAc4u1R8cQat3MZnq"
access_token_secret ="Vhmm5rAtuFq53xSD6lBItgW4zQRdD1jW1CfexLgyDXXRq"


auth = tweepy.OAuthHandler(consumer_key, consumer_secret )
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)
if (not api):
    print('Can\'t authenticate')
    print('failed cosumeer id ----------: ', consumer_key )
# set DB DETAILS


# this is to setup local Mongodb
client = MongoClient(MONGO_HOST) #is assigned local port
dbName = "twitterdb" # set-up a MongoDatabase
db = client.twitterdb
collName = 'tweets' # here we create a collection
collection = db[collName] #  This is for the Collection  put in the DB


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

    # print(t)

    # Pull important data from the tweet to store in the database.
    try:
        created = tweet['created_at']
        tweet_id = tweet['id_str']  # The Tweet ID from Twitter in string format
        username = tweet['user']['screen_name']  # The username of the Tweet author
        # followers = t['user']['followers_count']  # The number of followers the Tweet author has
        if 'text' in tweet:
            text = tweet['text']  # The entire body of the Tweet
        else:
            text = tweet['full_text']

        #The below lines deal with duplicate data
        collections = db.collection_names()
        for collection in collections:
            for x in db[collection].find():
                if tweet_id == x['_id']:
                    return None

        #The below lines deal with redundent data

    except Exception as e:
        # if this happens, there is something wrong with JSON, so ignore this tweet
        print(e)
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
    verified = tweet['user']['verified']


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

    retweet = False
    try:
        if (text.startswith('RT')== True):
            retweet = True
    except Exception as e:
        print(e)

    quoteTweet = False
    try:
        if('quoted_status' in tweet):
            quoteTweet = True
    except Exception as e:
        print(e)

    mediaList = False
    photoCount = 0
    videoCount = 0
    gifCount = 0
    if 'extended_entities' in tweet:
        extendedEntities = tweet['extended_entities']
        if ('media' in extendedEntities):
            mediaList = []
            for x in extendedEntities['media']:
                mediaList.append(x['media_url'])
                if x['type'] == 'video':
                    videoCount += 1
                elif x['type'] == 'photo':
                    photoCount += 1
                elif x['type'] == 'animated_gif':
                    gifCount += 1
    score = qualityCheck(tweet)
    redundant = False
    if score < 0.5:
        redundant = True
    tweet1 = {'_id' : tweet_id, 'date': created, 'username': username,  'text' : text,  'geoenabled' : geoenabled,  'coordinates' : coordinates,  'location' : location,  'place_name' : place_name, 'place_country' : place_country, 'country_code': place_countrycode,  'place_coordinates' : place_coordinates, 'hashtags' : hList, 'mentions' : mList, 'source' : source, 'retweet' : retweet, 'quoteTweet' : quoteTweet, 'media' : mediaList, 'photoCount': photoCount, 'videoCount': videoCount, 'gifCount': gifCount, 'redundant': redundant, 'verified':verified}

    return tweet1

def qualityCheck(tweet):
    user = tweet['user']
    if user['verified']:
        weight = 1.5
    else:
        weight = 1.0
    
    verifiedWeight = weight/1.5

    followersCount = user['followers_count']

    if followersCount < 50:
        weight = 0.5
    elif followersCount < 5000:
        weight = 1.0
    elif followersCount < 10000:
        weight = 1.5
    elif followersCount < 100000:
        weight = 2.0
    elif followersCount < 200000:
        weight = 2.5
    elif followersCount > 200000:
        weight = 3.0

    followersWeight= weight/3


    weight =1
    if(user['default_profile_image']):
        weight =0.5
    profileWeight = weight
    today = datetime.now()
    s = datetime.strptime(tweet['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
    daysSince = (today - s).total_seconds()/60/60/24

    if daysSince < 1:
        weight = 0.05
    elif daysSince < 30:
        weight = 0.10
    elif daysSince < 90:
        weight = 0.25
    elif daysSince > 90:
        weight = 1.0
    accountAgeWeight = weight
    
    
    qualityScore = (profileWeight + verifiedWeight + followersWeight + accountAgeWeight)/4
    return qualityScore

class StreamListener(tweepy.StreamListener):
  #This is a class provided by tweepy to access the Twitter Streaming API.

    global geoEnabled
    global geoDisabled
    def on_connect(self):
        # Called initially to connect to the Streaming API
        print("You are now connected to the streaming API.")



    def on_error(self, status_code):
        # On error - if an error occurs, display the error / status code
        print('An Error has occured: ' + repr(status_code))
        return False

    def on_data(self, data):
        #This is where each tweet is collected
        # let us load the  json data
        t = json.loads(data)
        #  now let us process the wteet so that we will deal with cleaned and extracted JSON
        tweet = processTweets(t)
        # print(tweet)
        # now insert it
        #  for this to work you need to start a local mongodb server
        try:
             collection.insert_one(tweet)
        except Exception as e:
             print(e)
            # this means some Mongo db insertion errort




#Set up the listener. The 'wait_on_rate_limit=True' is needed to help with Twitter API rate limiting.

# WORDS = ['manhattan' , 'new york city', 'statue of liberty']
# LOCATIONS = [ -75,40,-72,42] # new york city
Loc_UK = [-10.392627, 49.681847, 1.055039, 61.122019] # UK and Ireland
Words_UK =["Boris", "Prime Minister", "Tories", "UK", "London", "England", "Manchester", "Sheffield", "York", "Southampton", \
 "Wales", "Cardiff", "Swansea" ,"Banff", "Bristol", "Oxford", "Birmingham" ,"Scotland", "Glasgow", "Edinburgh", "Dundee", "Aberdeen", "Highlands" \
"Inverness", "Perth", "St Andrews", "Dumfries", "Ayr" \
"Ireland", "Dublin", "Cork", "Limerick", "Galway", "Belfast"," Derry", "Armagh" \
"BoJo", "Labour", "Liberal Democrats", "SNP", "Conservatives", "First Minister", "Surgeon", "Chancelor" \
"Boris Johnson", "BoJo", "Keith Stramer", "Lockdown", "COVID-19", "coronavirus",  "vaccine", "AstraZeneca" ]

print("Tracking: " + str(Words_UK))
#  here we ste the listener object
listener = StreamListener(api=tweepy.API(wait_on_rate_limit=True))
streamer = tweepy.Stream(auth=auth, listener=listener)
streamer.filter(locations= Loc_UK, track = Words_UK, languages = ['en'], is_async=True) #locations= Loc_UK, track = Words_UK,
#  the following line is for pure 1% sample
# we can only use filter or sample - not both together
# streamer.sample(languages = ['en'])

Place =  'London'
Lat   =  '51.450798'
Long  =  '-0.137842'
geoTerm=Lat+','+Long+','+'10km'
#

last_id =  None
counter =0
sinceID = None

results = True

while results:
    # print(geoTerm)

    if (counter < 180 ):
        try:
            results = api.search(geocode=geoTerm, count=100, lang="en", tweet_mode='extended', max_id=last_id) #, since_id = sinceID)
            #print(results)
        except Exception as e:
            print(e)
        counter += 1
    else:
        #  the following let the crawler to sleep for 15 minutes; to meet the Tiwtter 15 minute restriction
        time.sleep(15*60)
#
