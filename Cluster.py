import pymongo
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
from sklearn.feature_extraction import text
import numpy


def getText(tweet_collection):
    text = []
    alldata = tweet_collection.find()
    for tweet in alldata:
        tlower = str(tweet['text']).lower()
        #quality check 
        text.append(tlower)

    return text

# def remove_stop_words(texts,stop_words):
#     texts_no_sw = []
#     for text in texts:
#         text_tokens = word_tokenize(text)
#         tokens_without_sw = [word for word in text_tokens if not word in stop_words]
#         filtered_sentence = (" ").join(tokens_without_sw)
#         texts_no_sw.append(filtered_sentence)

#     return texts_no_sw


def cluster(texts):
    my_stop_words = text.ENGLISH_STOP_WORDS.union(["https", "rt", "retweet", "didn","amp"])
    # texts = remove_stop_words(texts,my_stop_words)
    # clusters = []
    # clusterCounter = 0
    # for text in texts:
    #     if clusterCounter==0:
    #         #create new cluster
    #         clusters.append(newCluster(text))
    #     else:
    #         #check similarity with existing clusters
    #         #take max similarity
    #         #if greater than threshold
    #             #add to cluster
    #         #else
    #             #create new cluster
    vectorizer = TfidfVectorizer(stop_words=my_stop_words)
    n = 8

    text_vector = vectorizer.fit_transform(texts)
    text_cluster = KMeans(n_clusters=n,init='k-means++',max_iter=300,n_init=3)
    text_cluster.fit_predict(text_vector)

    return vectorizer,text_cluster

def topResult(vectorizer,group):
    n = 8
    unique, counts = numpy.unique(group.labels_, return_counts=True)
    print(dict(zip(unique, counts)))
    centroids = group.cluster_centers_.argsort()[:,::-1]
    text = vectorizer.get_feature_names()
    for centre_num in range(n):
        print ("CLUSTER %d:" % centre_num)
        for i in centroids[centre_num,:5]:
            print (' %s' % text[i])

if __name__ == "__main__":
    MONGO_HOST = 'mongodb://localhost/twitterdb'
    client = pymongo.MongoClient(MONGO_HOST)
    db = client.twitterdb
    tweet_collection = db.tweets

    t = getText(tweet_collection)
    vec,tK = cluster(t)


    # print("++++ USERNAME CLUSTERS ++++")
    # topResult(vec,scK)
    # print("++++ HASHTAG CLUSTERS ++++")
    # topResult(vec,htK)
    # print("++++ TEXT CLUSTERS ++++")
    topResult(vec,tK)
