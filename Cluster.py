import pymongo
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score


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

def topResult(vectorizer,group):
    n = 12
    centroids = group.cluster_centers_.argsort()[:,::-1]
    text = vectorizer.get_feature_names()
    for centre in range(n):
        print ("CLUSTER %d:" % centre)
        for i in centroids[centre, :5]:
            print (' %s' % text[i])

if __name__ == "__main__":
    MONGO_HOST = 'mongodb://localhost/twitterdb'
    client = pymongo.MongoClient(MONGO_HOST)
    db = client.twitterdb
    tweet_collection = db.tweets

    sc,ht,t = getText(tweet_collection)
    vec,scK,htK,tK = cluster(sc,ht,t)



    print("++++ USERNAME CLUSTERS ++++")
    topResult(vec,scK)
    print("++++ HASHTAG CLUSTERS ++++")
    topResult(vec,htK)
    print("++++ TEXT CLUSTERS ++++")
    topResult(vec,tK)