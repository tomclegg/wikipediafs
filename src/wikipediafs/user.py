# -*- coding: utf-8 -*-

# WikipediaFS
# Copyright (C) 2005 - 2007 Mathieu Blondel
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import urllib, re
from http import ExtendedHTTPConnection

class User:
    """
    Gets user's cookie string
    """

    def __init__(self,
                 username,
                 password,
                 host,
                 basename,
                 https=False,
                 port=None,
                 httpauth_username=None,
                 httpauth_password=None,
                 logger = None,
                 # Not actually needed, just here for compatibility
                 name=None,
                 cookie_str=None,
                 dirname=None                 
                 ):
        logger.info("%s %s" % (username, password))

        self.username = username
        self.password = password
        self.host = host
        self.basename = basename
        self.https = https
        self.port = port
        self.httpauth_username = httpauth_username
        self.httpauth_password = httpauth_password
        self.logger = logger

        # url pattern
        self.login_page = "%s?title=Special:Userlogin" % self.basename
        self.login_page += "&action=submit&returnto=Special:Userlogin"

    def getCookieString(self):
        """
        Gets user's cookie string.
        It will then have to be passed to an Article.
        """

        params = {"wpName":self.username, "wpPassword":self.password,
                  "wpLoginattempt":"Identification", "wpRemember":"1"}
                
        params = urllib.urlencode(params)
        
        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "User-agent" : "WikipediaFS"}
        
        conn = ExtendedHTTPConnection(self.host, self.port, self.https)
        
        if self.httpauth_username and self.httpauth_password:
            conn.http_auth(self.httpauth_username, self.httpauth_password)

        conn.add_data(params)
        conn.add_headers(headers)
        conn.request(self.login_page)
        response = conn.getresponse()
        
        cookie_list = []
        in_cookie = re.compile(': (.*?);')
        
        for cookie_value in response.msg.getallmatchingheaders("set-cookie"):
            it_matches = in_cookie.search(cookie_value)
            
            if it_matches:
                cookie_list.append(it_matches.group(1))

        conn.close()
        
        if len(cookie_list) == 4:
            cookie_list.pop()
            if self.logger:
                self.logger.info("Logged in successfully with username %s" % \
                                 self.username)
                #self.logger.info("; ".join(cookie_list))
            return "; ".join(cookie_list)
        else:
            if self.logger:
                self.logger.warning("Could not log in with username %s" % \
                                    self.username)
            return None

               
if __name__ == "__main__":
    import sys

    params = {
        "host" : "www.mblondel.org",
        "basename" : "/mediawiki/index.php",
        "https" : True
    }

    if(len(sys.argv) != 3):
        print "python user.py username password"
    else:
        user = User(sys.argv[1], sys.argv[2], **params)
        print user.getCookieString()
        