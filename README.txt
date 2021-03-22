Order of running:
1. Run hybridCrawler.py, this will take 1 hour and will use streamer and REST API to gather 
   twitter data
2. Run downloadMedia.py to download media files
3. Run eventDetection.py to detect topics in the cluster


For clustering:
- ensure sklearn is installed, to do this, run 'pip install sklearn'

For downloadMedia:
-ensure requests and shutil are imported and installed

For eventDetection:
- ensure gensim, nltk and re are in stalled. To do this run:
	- 'pip install gensim'
	- 'pip install nltk'
	- 'pip install re'


