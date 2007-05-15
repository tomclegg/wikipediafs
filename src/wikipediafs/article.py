#!/usr/bin/env python
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

import urllib, re, os
from sgmllib import SGMLParser
from http import ExtendedHTTPConnection

class Article(SGMLParser):
    """
    Gets and sets an article.
    """
    
    def __init__(self,
                 name,
                 host,
                 basename,
                 cookie_str=None,
                 https=False,
                 port=None,
                 httpauth_username=None,
                 httpauth_password=None
                 ):
        SGMLParser.__init__(self)
    
        self.name = name
        self.host = host
        self.basename = basename
        self.cookie_str = cookie_str
        self.https = https
        self.port = port
        self.httpauth_username = httpauth_username
        self.httpauth_password = httpauth_password
                 
        self.content = ""
        self.textarea = False
        self.wpEdittime = 0
        self.wpStarttime = 0
        self.wpEditToken = None
        self.last_open_time = 0

        # url patterns        
        self.edit_page = "%s?title=%s&action=edit" % \
                            (self.basename, self.name)
                            # basename must include a leading /
        
        self.submit_page = "%s?title=%s&action=submit" % \
                            (self.basename, self.name)                          

    def start_textarea(self,attrs):
        """
        Called when a textarea is entered.
        """
        self.textarea = True
    
    def start_input(self,attrs):
        """
        Called when an input is entered.
        """
        # To set an article, we need to now its wpEdittime first.
        
        if len(attrs) == 3 and attrs[2][1] == "wpEdittime":
            self.wpEdittime = attrs[1][1]
        elif len(attrs) == 3 and attrs[2][1] == "wpEditToken":
            self.wpEditToken = attrs[1][1]            
        elif len(attrs) == 3 and attrs[2][1] == "wpStarttime":
            self.wpStarttime = attrs[1][1]            
            
    def end_textarea(self):
        """
        Called when a textarea is left.
        """
        self.textarea = False
        
    def handle_data(self,data):
        """
        Called when data is parsed.
        """            
        # We add the parsed data to self.content when the data parsed
        # is in a textarea
        if self.textarea == True:
            self.content += data

    def get(self): 
        """
        Gets the wiki content (not the whole html page).
        """
        
        headers = {"User-agent" : "WikipediaFS"}
          
        if self.cookie_str is not None:
            headers["Cookie"] = self.cookie_str
              
        conn = ExtendedHTTPConnection(self.host, self.port, self.https)

        conn.set_proxy()

        if self.httpauth_username and self.httpauth_password:
            conn.http_auth(httpauth_username, httpauth_password)

        conn.add_headers(headers)
        conn.request(self.edit_page)
        #logger.info("HTTP GET %s" % self.edit_page)
        response = conn.getresponse()        
        
        # Feeds the SGMLparser
        self.feed(response.read())
        conn.close()

        return self.content
              
        
    def set(self, text):
        # Looking for a [[Summary:*]]
        regexp = '((\[\[)((s|S)ummary:)(.*)(\]\])(( )*\n)?)'
        summary = re.search(regexp, text)
        if summary is not None:
            wpSummary = summary.group(5)
            text = text.replace(summary.group(1), '')
        else:
            wpSummary = " "
        
        # wpEdittime is empty if the article is a new article
        params = {
            "wpTextbox1" : text,
            "wpSummary" : wpSummary,
            "wpEdittime" : self.wpEdittime,
            "wpStarttime": self.wpStarttime,
            "wpSave" : 1
        }
        
        # Needed for logged in edition
        if self.wpEditToken is not None:
            params["wpEditToken"] = self.wpEditToken
                
        params = urllib.urlencode(params)
        
        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "User-agent" : "WikipediaFS"}
        
        if self.cookie_str is not None:
            headers["Cookie"] = self.cookie_str
        
        conn = ExtendedHTTPConnection(self.host, self.port, self.https)
        conn.set_proxy()

        conn.add_headers(headers)
        conn.add_data(params)
        conn.request(self.submit_page)
        #logger.info("HTTP POST %s" % self.submit_page)
        response = conn.getresponse()
        
        # Log http response        
        #if response.status == 302:
        #    logger.info("Succesful")
        #elif response.status == 200:
        #    logger.warning("Problems occured %s\n" % response.read())
        #else:
        #    logger.info("%d \n %s " % (response.status,response.read()))

        conn.close()


if __name__ == "__main__":
    import random
    import sys
    from user import User
    
    params = {
        "host" : "www.mblondel.org",
        "basename" : "/mediawiki/index.php",
        "https" : True
    }

    # Used username and password if any
    if len(sys.argv) == 3:
        user = User(sys.argv[1], sys.argv[2], **params)
        params["cookie_str"] = user.getCookieString()
    
    art = Article("Test", **params)
    print art.get()

    art.set("Test ! (%s)" % str(random.random()))
    