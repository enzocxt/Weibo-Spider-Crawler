A spider/crawler for weibo.com, which extracts/stores the users' records for further business intelligence analysis.

This program is to be deployed on GAE(Google App Engine) v1.6.

A live demo of this project can be found here.

    http://weibospider.appspot.com

However, due to the limited quota provided by GAE, it is not guaranteed that it will keep alive at any time for any one.

This project is released under GPL license

    Copyright (C) 2012 Raullen Chai

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

Please free to contact me if you have any question.


Release Notes:

# v2	2012/3/21
	1. The appstats (http://code.google.com/appengine/docs/python/tools/appstats.html) is enabled to give more monitoring of this GAE app.
	2. Reset function is cancled as it is too dangerous
	3. This app is swtiched to use Google Cloud SQL as the GAE Datastore is too limited.
	4. A pool of username/password/appkey is used to avoid reaching, for a single acount, the weibo API limit.
	5. Due to the above improvement, we can now reach a rate of capturing around 125 entires per minute per instance.
	
# v1	2012/3/20
	proof-of-concept version
