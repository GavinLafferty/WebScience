from pymongo import MongoClient
import requests # to get image from the web
import shutil # to save it locally


MONGO_HOST = 'mongodb://localhost/twitterdb'
client = MongoClient(MONGO_HOST) #is assigned local port
dbName = "twitterdb" # set-up a MongoDatabase
db = client.twitterdb
collName = 'tweets' # here we create a collection
collection = db[collName] #  This is for the Collection  put in the DB

# For each tweet in collection
for x in collection.find():
    # If there is media attached
    if x['media']:
        # For each piece of media
        for i in range(len(x['media'])):
            img_url = x['media'][i]
            # Name for file
            filename = img_url.split("/")[-1]
            # Get image from url
            r = requests.get(img_url, stream = True)

            # Check if the image was retrieved successfully
            if r.status_code == 200:
                # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
                r.raw.decode_content = True
                
                # Open a local file with wb ( write binary ) permission.
                with open(filename,'wb') as f:
                    shutil.copyfileobj(r.raw, f)
                    
                print('Image sucessfully Downloaded: ',filename)
                
            else:
                print('Image Couldn\'t be retreived')