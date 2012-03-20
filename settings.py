#one need to input a weibo's account info (username & password) here
#one need to get the app key for this account as well

USERNAME = 'noreply@literhub.com'
PASSWORD = '1224213qqq'
APP_KEY = '1498737208'
WEIBO_URL = 'https://api.weibo.com/2/friendships/followers.json?source='+APP_KEY+'&count=200'

#do not add too many records per visit of the page, 500 records consume ~30% quota of Datastore Write Operations on my GAE
#In addition, weibo API also has the limit on the number of APIs to be called per hour
WRITEPERVISIT = 500 