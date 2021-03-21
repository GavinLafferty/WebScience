import nltk
from pymongo import MongoClient
from gensim import corpora, models
from nltk.corpus import stopwords


MONGO_HOST = 'mongodb://localhost/twitterdb'
client = MongoClient(MONGO_HOST) #is assigned local port
dbName = "twitterdb" # set-up a MongoDatabase
db = client.twitterdb
collName = 'tweets' # here we create a collection
collection = db[collName] #  This is for the Collection  put in the DB
#collections = db.collection_names()

#The below function tokenises each tweet in the database
def tokenize():
    tokens = []
    collections = db.collection_names()
    for collection in collections:
        for x in db[collection].find():
            text = x['text']
            tokens.append(nltk.word_tokenize(text))
    return(tokens)

#The below function removes sto words from the tokens passed in
def remove_stop_words(stop_words, tokens):  
     texts_no_sw = []
     for token in tokens:
        tokens_without_sw = [word for word in token if not word in stop_words]
        filtered_sentence = (" ").join(tokens_without_sw)
        texts_no_sw.append(tokens_without_sw)

     return texts_no_sw

def eventDetect():
    stop_words = set(stopwords.words('english'))
    stop_words = stop_words.union(["https", "rt", "retweet", "didn","amp", "RT", ";", ",", "&", "|"])
    tokens = tokenize()
    tokensWithoutSW = remove_stop_words(stop_words, tokens)
    
    LDA_Dict = corpora.Dictionary(tokensWithoutSW)
    LDA_Dict.filter_extremes(no_below=3)
    corpus = [LDA_Dict.doc2bow(token) for token in tokens]

    num_topics = 20
    #LDA model implements the Latent Dirichlet Allocation in order to identify events from the provided tokens
    lda_model = models.LdaModel(corpus, num_topics=num_topics, \
                                    id2word=LDA_Dict, \
                                    passes=4, alpha=[0.01]*num_topics, \
                                    eta=[0.01]*len(LDA_Dict.keys()))
    
    for i,topic in lda_model.show_topics(formatted=True, num_topics=num_topics, num_words=10):
        print(str(i)+": "+ topic)
        print()

    def qualityCheck():
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
        if(User['default_profile_image']):
            weight =0.5
        profileWeight = weight

        createdAt = user['created_at']
        today = date.today()

        d1 = datetime.strptime(createdAt, "%Y-%m-%d")
        d2 = datetime.strptime(today, "%Y-%m-%d")
        daysSince = abs((d2 - d1).days)

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


eventDetect()