#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Raullen Chai
# v1	proof-of-concept version	2012/3/20
# Released under the GPL License
#

from datetime import datetime, date, time
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
import urllib2, base64
import simplejson
import sys, re
import random
from settings import *


#do not add too many records per visit of the page, 500 records consume ~30% quota of Datastore Write Operations on my GAE
#In addition, weibo API also has the limit on the number of APIs to be called per hour
WRITEPERVISIT = 500 



class Users(db.Model):
    """Data Model"""
    id = db.IntegerProperty(default=0)
    screen_name = db.StringProperty(default='NULL')
    name = db.StringProperty(default='NULL')
    province = db.IntegerProperty(default=0)
    city = db.IntegerProperty(default=0)
    location = db.StringProperty(default='NULL')
    gender = db.StringProperty(default='NULL')
    url = db.StringProperty(default='NULL')
    statuses_count = db.IntegerProperty(default=0)
    followers_count = db.IntegerProperty(default=0)
    friends_count = db.IntegerProperty(default=0)
    created_at = db.DateTimeProperty(auto_now_add=True)
    selected = db.IntegerProperty(default=0)
    visited = db.IntegerProperty(default=0)                     #used by the crawler to mark the users visited: 0 unvisited 1 visited


class QueryHandler(webapp.RequestHandler):	
    """Get random users"""
    def get(self):
        users = Users.all()
        cnt = 0
        self.response.out.write('<blockquote>')
        for user in users:
            if cnt>20:
                break
            if random.randint(0,1000) <= 100:  #one record has a certain prob. to be selected
                self.response.out.write('@%s, ' % user.screen_name)
                #print isinstance(user.screen_name, unicode) #user.screen_name is unicode encoded
                cnt += 1
            
        self.response.out.write('</blockquote>')
        

class CountHandler(webapp.RequestHandler):
    """Retrieve the number of entries in DB"""
    def get(self):
        users = Users.all()
        cnt = 0
        for user in users:
            cnt += 1
        self.response.out.write('<blockquote>%d users are stored</blockquote>' % cnt)


class ResetHandler(webapp.RequestHandler):
    """Reset the Database by deleting all entries"""
    def get(self):
        users = Users.all()
        cnt = 0
        for user in users:
            user.delete()
            cnt += 1
        self.response.out.write('<blockquote>%d users has been deleted</blockquote>' % cnt)



def GetFriends(uid, cursor):
    """Get the friends of an user as specified"""
    req = urllib2.Request(WEIBO_URL+"&uid="+str(uid)+"&cursor="+str(cursor))
    sec = base64.encodestring('%s:%s' % (USERNAME, PASSWORD)).replace('\n', '')
    req.add_header('Authorization', 'Basic %s' % sec)
    try:
        return simplejson.load(urllib2.urlopen(req))
    except urllib2.URLError, e:
        #print e.reason
        return None


def GetFollowers(uid, cursor):
    """TODO Get the followers of an user as specified"""
    return True


def Chooseuid():
    """Select one user from the DB to further retrieve his/her friends"""
    uid = 1965240545    #set to a value for the first time exec
    users = db.GqlQuery("SELECT * FROM Users WHERE visited = 0 ORDER BY followers_count DESC LIMIT 1")
    if(users.count() > 0):
        user = users.fetch(limit=1)
        uid = user[0].id
        user = Users(  key_name = str(uid)  )
        user.visited = 1
        user.put()
    return uid



class MainHandler(webapp.RequestHandler):
    def get(self):
        uid = Chooseuid()
        cursor = 0
        cnt = 0;
        
        while True:
            res = GetFriends(uid, cursor)
            if res == None:
                break
            no_friends = len(res[u'users'])
            self.response.out.write('<blockquote>no_friends:%d</blockquote>' % no_friends)

            for i in range(no_friends):
                if cnt>WRITEPERVISIT:
                    break
                user = Users(key_name = str(res[u'users'][i][u'id']) )                  #use the uid as primary key
                user.id = res[u'users'][i][u'id']    
                user.screen_name = res[u'users'][i][u'screen_name']
                user.name = res[u'users'][i][u'name']
                user.province = int(res[u'users'][i][u'province'])
                user.city = int(res[u'users'][i][u'city'])
                user.location = res[u'users'][i][u'location']
                user.gender = res[u'users'][i][u'gender']
                user.url = res[u'users'][i][u'url']
                user.statuses_count = res[u'users'][i][u'statuses_count']
                user.followers_count = res[u'users'][i][u'followers_count']
                user.friends_count = res[u'users'][i][u'friends_count']
                tmp =  re.sub('[+-]\d\d\d\d',"",res[u'users'][i][u'created_at'])
                user.created_at = datetime.strptime(tmp, "%a %b %d %H:%M:%S %Y" )       #Fri Aug 28 00:00:00 +0800 2009
                user.visited = 0
                user.put()
                cnt += 1

            self.response.out.write('<blockquote>next_cursor:%d</blockquote>' % res[u'next_cursor'])
            if res[u'next_cursor'] == 0 or cnt>WRITEPERVISIT:
                break
            cursor = res[u'next_cursor']
        self.response.out.write('<blockquote>users added:%d</blockquote>' % cnt)
    
    
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


def main():
    application = webapp.WSGIApplication([('/', MainHandler),
										  ('/count', CountHandler),
                                          ('/reset', ResetHandler),
                                          ('/randomuser', QueryHandler),
                                          ('/.*', NotFoundHandler)],
                                         debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()