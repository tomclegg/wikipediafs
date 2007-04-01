#!/usr/bin/env python
# -*- coding: utf-8 -*-

# WikipediaFS
# Copyright (C) 2005 - 2006 Mathieu Blondel
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
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import httplib, urllib, re, string, os, socket
from sgmllib import SGMLParser
from wikipediafs.logger import logger

def set_proxy(conn):
    if os.environ.has_key("http_proxy"):
        http_proxy = os.environ["http_proxy"].replace("http://", "").rstrip("/")
        (proxy_host, proxy_port) = http_proxy.split(":")
        proxy_port = int(proxy_port)
        proxy_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxy_sock.connect((proxy_host, proxy_port))
        conn.sock = proxy_sock

class WikipediaArticle(SGMLParser):
    """
    This class mainly deals with getting and setting an article.
    """
    
    def __init__(self,article_name,wikipedia_article_list):
        """
        A WikipediaArticle is defined by its name and
        the WikipediaArticleList it belongs to.
        Moreover, a WikipediaArticle has its own content,
        wpEdittime, edit_page and submit_page.
        """
        
        SGMLParser.__init__(self)
    
        self.name = article_name
        self.content = ""
        self.textarea = False
        self.wpEdittime = 0
        self.wpStarttime = 0
        self.wpEditToken = None
        self.last_open_time = 0
        
        self.host = wikipedia_article_list.host
        
        self.edit_page = 'http://' + self.host + \
                         wikipedia_article_list.basename + \
                         "?title=%s&action=edit" % article_name
                            
        self.submit_page = 'http://' + self.host + \
                            wikipedia_article_list.basename + \
                            "?title=%s&action=submit" % article_name
                               
        self.username = wikipedia_article_list.username
        self.cookie_string = wikipedia_article_list.cookie_string

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
        
        headers = {}        
        if self.cookie_string is not None:
            headers["Cookie"] = self.cookie_string
              
        conn = httplib.HTTPConnection(self.host)
        set_proxy(conn)
        conn.request("GET",self.edit_page,'',headers)
        logger.info("HTTP GET %s" % self.edit_page)
        response = conn.getresponse()        
        
        # Feeds the SGMLparser
        self.feed(response.read())
        conn.close()
        
        content = self.content
        # We delete it not to keep content in memory
        self.content = ""
        
        # Returns content that have been updated by the handle_data method
        return content
              
        
    def set(self,article_data):
        """ 
        Sets the wiki content of the article.
        """
        # Looking for a [[Summary:*]]
        regexp = '((\[\[)((s|S)ummary:)(.*)(\]\])(( )*\n)?)'
        summary = re.search(regexp, article_data)
        if summary is not None:
            wpSummary = summary.group(5)
            article_data = article_data.replace(summary.group(1), '')
        else:
            wpSummary = " "
       
        # wpEdittime is empty if the article is a new article
        params = {"wpTextbox1" : article_data, "wpSummary" : wpSummary, \
        "wpEdittime" : self.wpEdittime, "wpStarttime": self.wpStarttime, "wpSave" : 1}
        
        # Needed for logged in edition
        if self.wpEditToken is not None:
            params["wpEditToken"] = self.wpEditToken
                
        params = urllib.urlencode(params)
        
        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "User-agent" : "WikipediaFS"}
        
        if self.cookie_string is not None:
            headers["Cookie"] = self.cookie_string
        
        conn = httplib.HTTPConnection(self.host)
        set_proxy(conn)
        conn.request("POST",self.submit_page, params, headers)
        logger.info("HTTP POST %s" % self.submit_page)
        response = conn.getresponse()
        
        # Log http response        
        if response.status == 302:
            logger.info("Succesful")
        elif response.status == 200:
            logger.warning("Problems occured %s\n" % response.read())
        else:
            logger.info("%d \n %s " % (response.status,response.read()))

        conn.close()
        
if __name__ == "__main__":
    import random
    from WikipediaArticleList import WikipediaArticleList
    wal = WikipediaArticleList('mblondel.org', 'www.mblondel.org',
                               '/mediawiki/index.php', None, None)
                               
    article = WikipediaArticle('Test', wal)
    print article.get()
    article.set("Test ! (%s)" % \
        str(random.random()))