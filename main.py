#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Raullen Chai
# Released under the GPL License


from datetime import datetime, date, time
from google.appengine.api import rdbms
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
import urllib2, base64
import simplejson
import sys, re
import random
from settings import *

#do not add too many records per visit of the page, 500 records consume ~30% quota of Datastore Write Operations on my GAE
WRITEPERVISIT = 2000





##############################################################################################################
#Google Cloud SQL Configuration
"""
#1. In Google API Console -> Google Cloud SQL, create an instance.
#2. Add your appname into the instance
#3. Within that instance, create database/table as below.
CREATE DATABASE weibo_info;
CREATE TABLE users (id INT NOT NULL, screen_name VARCHAR(255), name VARCHAR(255), province INT, city INT, location VARCHAR(255), gender  VARCHAR(8), url VARCHAR(255), statuses_count INT, followers_count INT, friends_count INT, created_at DATE, visited INT, visited_at DATE, reserved0 INT, reserved1 VARCHAR(255), reserved2 VARCHAR(255), PRIMARY KEY(id));
"""

_INSTANCE_NAME = 'weibousers:weibousers10g'
_DATABASE_NAME = 'weibo_info'
_TABLE_NAME = 'users'








##############################################################################################################
#Sina Weibo API Configuration is defined in settings.py like below
"""
USERNAME = list(['user1','user2','user3','user4'])
PASSWORD = list(['password1','password2','password3','password4'])
APP_KEY = list(['appkey1','appkey2','appkey3','appkey4'])
"""








##############################################################################################################
"""Choose random users to display"""
class QueryHandler(webapp.RequestHandler):	

    def get(self):
        conn = rdbms.connect(instance=_INSTANCE_NAME, database=_DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM '+_TABLE_NAME+' ORDER by RAND() LIMIT 20')
        self.response.out.write('<blockquote>')
        for row in cursor.fetchall():
			self.response.out.write('@%s, ' % row[1])
        self.response.out.write('</blockquote>')
        conn.close()

		
		
		
		
		
		
		
		
##############################################################################################################
"""Retrieve the number of entries in DB"""
class StatusHandler(webapp.RequestHandler):

    def get(self):
        conn = rdbms.connect(instance=_INSTANCE_NAME, database=_DATABASE_NAME)
		#total number of users
        cursor = conn.cursor()
        cursor.execute('SELECT count(*) FROM ' + _TABLE_NAME)
        total_cnt = 0
        for row in cursor.fetchall():
			total_cnt = row
			self.response.out.write('<blockquote>%d users are stored</blockquote>' % total_cnt)
			
		#number of female/male users
        cursor = conn.cursor()
        cursor.execute('SELECT count(*) FROM ' + _TABLE_NAME + ' WHERE gender="f"')
        female_cnt = 0
        for row in cursor.fetchall():
			female_cnt = row
			self.response.out.write('<blockquote>%d  users are female</blockquote>' % female_cnt)
			
        cursor = conn.cursor()
        cursor.execute('SELECT count(*) FROM ' + _TABLE_NAME + ' WHERE gender="m"')
        male_cnt = 0
        for row in cursor.fetchall():
			male_cnt = row
			self.response.out.write('<blockquote>%d  users are male</blockquote>' % male_cnt)			
			
        conn.close()

		
		
##############################################################################################################
"""TODO: Check if the API reaches their limits"""
class APIStatusHandler(webapp.RequestHandler):

    def get(self):
		return True


##############################################################################################################
"""TODO: Update the user info stored in the database reguarly"""

class MaintainHandler(webapp.RequestHandler):

    def get(self):
		return True


		
##############################################################################################################
"""Get the friends of an user as specified"""
def getfriends(uid, cursor):

	#choose one account from the pool to avoid to reach the limit of weibo API
    index = random.randint(0, len(APP_KEY)-1)
    req = urllib2.Request('https://api.weibo.com/2/friendships/followers.json?source='+APP_KEY[index]+'&count=200'+"&uid="+str(uid)+"&cursor="+str(cursor))
    sec = base64.encodestring('%s:%s' % (USERNAME[index], PASSWORD[index])).replace('\n', '')
    req.add_header('Authorization', 'Basic %s' % sec)
    try:
        return simplejson.load(urllib2.urlopen(req))
    except urllib2.URLError, e:
        #print e.reason
        return None

"""TODO Get the followers of an user as specified"""
def getfollowers(uid, cursor):

    return True


"""Crawl the friends of users and store in Google Cloud SQL"""
class MainHandler(webapp.RequestHandler):

    def get(self):

        conn = rdbms.connect(instance=_INSTANCE_NAME, database=_DATABASE_NAME)
        cursor = conn.cursor()
		
        #Select one user from the DB to further retrieve his/her friends
        uid = 1965240545    #set to a value to bootstrap
        cursor.execute('SELECT id FROM ' + _TABLE_NAME + ' WHERE visited = 0 ORDER BY followers_count DESC LIMIT 1')
        for row in cursor.fetchall():
            uid = int(row[0])

        if uid != 1965240545:
            cursor = conn.cursor()
            cursor.execute('UPDATE ' + _TABLE_NAME + ' SET visited = 1 WHERE id=' + str(uid))
        #self.response.out.write('<blockquote>uid:%d</blockquote>' % uid)

        weibo_cursor = 0
        cnt = 0;
        while True:
            res = getfriends(uid, weibo_cursor)
            if res == None:
                break
            no_friends = len(res[u'users'])
            #self.response.out.write('<blockquote>no_friends:%d</blockquote>' % no_friends)

            for i in range(no_friends):
                if cnt>WRITEPERVISIT:
                    break
                cursor = conn.cursor()
                user_id = res[u'users'][i][u'id']    
                user_screen_name = res[u'users'][i][u'screen_name']
                user_name = res[u'users'][i][u'name']
                user_province = int(res[u'users'][i][u'province'])
                user_city = int(res[u'users'][i][u'city'])
                user_location = res[u'users'][i][u'location']
                user_gender = res[u'users'][i][u'gender']
                user_url = res[u'users'][i][u'url']
                user_statuses_count = res[u'users'][i][u'statuses_count']
                user_followers_count = res[u'users'][i][u'followers_count']
                user_friends_count = res[u'users'][i][u'friends_count']
                tmp =  re.sub('[+-]\d\d\d\d',"",res[u'users'][i][u'created_at'])
                user_created_at = datetime.strptime(tmp, "%a %b %d %H:%M:%S %Y" )       #Fri Aug 28 00:00:00 +0800 2009
                user_visited = 0
                visited_at = datetime.now()
				
                print 'I got one'
                # use 'INSERT IGNORE INTO' to ignore the error raised by duplicate entries 
                cursor.execute('INSERT IGNORE INTO ' + _TABLE_NAME + ' (id, screen_name, name, province, city, location, gender, url, statuses_count, followers_count, friends_count, created_at, visited, visited_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (user_id, user_screen_name, user_name, user_province, user_city, user_location, user_gender, user_url, user_statuses_count, user_followers_count, user_friends_count, user_created_at, user_visited, visited_at))
                conn.commit()
                cnt += 1

            #self.response.out.write('<blockquote>next_cursor:%d</blockquote>' % res[u'next_cursor'])
            if res[u'next_cursor'] == 0 or cnt>WRITEPERVISIT:
                break
            weibo_cursor = res[u'next_cursor']
        self.response.out.write('<blockquote>users added:%d</blockquote>' % cnt)
        conn.close()

    
##############################################################################################################
class NotFoundHandler(webapp.RequestHandler):
  def get(self):    
    self.response.out.write("""
    <table border="0" cellspacing="0" cellpadding="0" width="100%" class="hit-layout">
    <tr>
    <td id="hit-a">
        <div class="hit-content">
        <h3>The Page You Requested Is Not Found</h3>
        </div>
    </td>
    </tr>
    </table>
    """)


##############################################################################################################
def main():
    application = webapp.WSGIApplication([('/', MainHandler),
										  ('/status', StatusHandler),
										  ('/api', APIStatusHandler),
                                          ('/randomuser', QueryHandler),
                                          ('/.*', NotFoundHandler)],
                                         debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()