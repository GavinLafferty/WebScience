import nltk
from pymongo import MongoClient
from gensim import corpora, models
from nltk.corpus import stopwords
import re
from collections import Counter
from itertools import repeat, chain



MONGO_HOST = 'mongodb://localhost/twitterdb'
client = MongoClient(MONGO_HOST)  # is assigned local port
dbName = "twitterdb"  # set-up a MongoDatabase
db = client.twitterdb
collName = 'tweets'  # here we create a collection
collection = db[collName]  # This is for the Collection  put in the DB
# collections = db.collection_names()

# The below function tokenises each tweet in the database


def tokenize():
    tokens = []
    collections = db.list_collection_names()
    for collection in collections:
        for x in db[collection].find():
            text = x['text']
            tokens.append(nltk.word_tokenize(text))
    return(tokens)

#The below function removes stop words from the tokens passed in
def remove_stop_words(stop_words, tokens):  
     texts_no_sw = []
     for token in tokens:
        tokens_without_sw = [word for word in token if not word in stop_words]
        filtered_sentence = (" ").join(tokens_without_sw)
        texts_no_sw.append(tokens_without_sw)

     return texts_no_sw


def geoLocalisation(lda_model, num_topics):
    places = []
    
    for i, topic in lda_model.show_topics(formatted=True, num_topics=num_topics, num_words=10):
        topic = re.sub(r'[^\w]', ' ', topic)#removes special characters
        topic = re.sub(r'\d+', '', topic)#removes numbers
        topicList = list(topic)
        collections = db.list_collection_names()
        for collection in collections:
            for x in db[collection].find():
                if any(word in x['text']for word in topicList):
                    if(x['geoenabled'] and x['place_name'] != None):
                        places.append(x['place_name'])
    
    
    sortedPlaces = Counter(places).most_common()
    print(sortedPlaces)
    
    
        

def eventDetect():
    # Tokenise and remove stop words
    stop_words = set(stopwords.words('english'))
    stop_words = stop_words.union(["https", "rt", "retweet", "didn","amp", "RT", ";", ",", "&", "|", "#", ""])
    tokens = tokenize()
    tokensWithoutSW = remove_stop_words(stop_words, tokens)
    
    # Create dictionary and corpus
    LDA_Dict = corpora.Dictionary(tokensWithoutSW)
    LDA_Dict.filter_extremes(no_below=3)
    corpus = [LDA_Dict.doc2bow(token) for token in tokens]

    num_topics = 20
    # LDA model implements the Latent Dirichlet Allocation in order to identify events from the provided tokens
    # Code adapted from https://towardsdatascience.com/the-complete-guide-for-topics-extraction-in-python-a6aaa6cedbb
    lda_model = models.LdaModel(corpus, num_topics=num_topics, \
                                    id2word=LDA_Dict, \
                                    passes=4, alpha=[0.01]*num_topics, \
                                    eta=[0.01]*len(LDA_Dict.keys()))
    
    # Print each event
    for i,topic in lda_model.show_topics(formatted=True, num_topics=num_topics, num_words=10):
        print(str(i)+": "+ topic)
        print()

    geoLocalisation(lda_model, num_topics)
        

eventDetect()
