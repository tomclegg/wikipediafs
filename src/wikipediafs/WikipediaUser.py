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

import os, httplib, urllib, re
from xml.dom import minidom
from wikipediafs.logger import logger
from wikipediafs.WikipediaArticle import set_proxy

class WikipediaUser:
    """
    A WikipediaUser is an anonymous or identified wikipedia user.
    This class deals with everything which is user specific :
        articles cache, login, etc.
    """

    default_config = """\
<?xml version="1.0" encoding="UTF-8"?>
<wfs-config>
    <general>
        <!-- Cache time in seconds -->
        <article-cache-time>300</article-cache-time>
    </general>
    <sites>
        <!-- <site>
            <dirname>wikipedia-fr</dirname>
            <host>fr.wikipedia.org</host>
            <basename>/w/index.php</basename>
            <username>Username</username>
            <password>Password</password>
        </site>-->
        <site>
            <dirname>mblondel.org</dirname>
            <host>www.mblondel.org</host>
            <basename>/mediawiki/index.php</basename>
        </site>
    </sites>
</wfs-config>
        """
    
    def __init__(self, config_str=False):
        """
        Inits the WikipediaUser.
        The XML config string can be passed as a parameter mainly for
        test purpose.
        """
        
        self.home_dir = os.environ['HOME'] + "/.wikipediafs"
        self.cache_dir = self.home_dir + "/.cache"
        self.conf_file = self.home_dir + "/config.xml"
        self.wikipedia_article_list_infos = []

        # Creates .wikipediafs. in HOME if needed
        if not os.path.exists(self.home_dir):
            os.mkdir(self.home_dir,0700)

        # Creates .cache/ in .wikipediafs/ if needed
        if not os.path.exists(self.cache_dir):
            os.mkdir(self.cache_dir,0700)
            
        # Loads the config from a file or from a string    
        if(not config_str):            
            # Loads configuration file
            if not os.path.exists(self.conf_file):
                self.__setDefaultConfigFile()
        
            self.config = minidom.parse(self.conf_file).documentElement
        else:
            self.config = minidom.parseString(config_str).documentElement
                             
        try:                     
            self.article_cache_time = self.__getConfigCacheTime(self.config)
        except:
            self.article_cache_time = 300
            
        for site in self.__getConfigSiteList(self.config):
            self.wikipedia_article_list_infos.append(              
                      self.__getConfigSiteDict(site))
            
        # Sets cache dirs if don't exist yet
        for info in self.wikipedia_article_list_infos:
            dir = self.cache_dir + '/' + info["list_name"]
            if not os.path.exists(dir):
                os.mkdir(dir,0700)
            else:
                # remove cache from previous sessions
                for cache_file in os.listdir(dir):
                    try:
                        os.remove(os.path.join(dir, cache_file))
                    except:
                        pass
            
    def setCacheArticle(self,path,article_data):
        """
        Sets article_data in cache.
        """
        file = open(self.cache_dir + "/" + path,"w")
        file.write(article_data)
        file.close()
        
    def getCacheArticle(self,path):
        """
        Gets data in cache.
        """
        file = open(self.cache_dir + "/" + path,"r")
        ret = file.read()
        file.close()
        return ret

    def cacheExists(self, path):
        return os.path.exists(self.cache_dir + "/" + path)

    def cacheMtime(self, path):
        return os.path.getmtime(self.cache_dir + "/" + path)
    
    def createCacheDir(self,name):
        """
        Creates a lang cache directory.
        """
        name = self.cache_dir + "/" + name
        if not os.path.exists(name):
            return os.mkdir(name, 0700)
    
    def deleteCacheDir(self,name):
        """
        Deletes a lang cache directory.
        """
        name = self.cache_dir + "/" + name
        if os.path.exists(name):
            return os.removedirs(name)
            
    def isAvailable(self,lang):
        """
        Checks wether a site is configured but not used.
        """
        for site in self.__getConfigSiteList(self.config):
            if lang in \
                site.getElementsByTagName("dirname")[0].firstChild.nodeValue:
                return True
            else:
                return False
    
    def retrieveSite(self,lang):
        """
        Retrieves infos for the site nammed lang.
        """
        for site in self.__getConfigSiteList(self.config):
            first_child = site.getElementsByTagName("dirname")[0].firstChild
            if lang == first_child.nodeValue:
                self.wikipedia_article_list_infos.append(
                    self.__getConfigSiteDict(site))
        return self.wikipedia_article_list_infos[-1]
        
    def __getCookie(self,host,username,password,login_page):
        """ 
        Login to Wikipedia and Return the cookie.
        """
        # wpEdittime is empty if the article is a new article         
        params = {"wpName":username, "wpPassword":password,
                  "wpLoginattempt":"Identification", "wpRemember":"1"}
                
        params = urllib.urlencode(params)
        
        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "User-agent" : "WikipediaFS"}
        
        conn = httplib.HTTPConnection(host)
        set_proxy(conn)
        conn.request("POST",login_page, params, headers)
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
            return "; ".join(cookie_list)
        else:
            return None
        
    def __setDefaultConfigFile(self):
        file = open(self.conf_file,"w",0700)
        file.write(WikipediaUser.default_config)
        file.close()
        
    def __getConfigCacheTime(self,config):
        element = config.getElementsByTagName("article-cache-time")[0]
        first_child = element.firstChild
        return int(str(first_child.nodeValue))
        
    def __getConfigSiteList(self,config):
        return config.getElementsByTagName("site")
        
    def __getConfigSiteDict(self,site):
        dict = {}
        
        dirname_child = site.getElementsByTagName("dirname")[0].firstChild
        dict["list_name"] = dirname_child.nodeValue.encode("utf-8")
            
        host_child = site.getElementsByTagName("host")[0].firstChild    
        dict["host"] = host_child.nodeValue.encode("utf-8")
        
        basename_child = site.getElementsByTagName("basename")[0].firstChild
        dict["basename"] = basename_child.nodeValue.encode("utf-8")

        login_page = 'http://' + dict["host"] + dict["basename"] + \
            "?title=Special:Userlogin&action=submit&returnto=Special:Userlogin"
        
        username = site.getElementsByTagName("username")
        password = site.getElementsByTagName("password")
        
        if username.length == 1:
            dict["username"] = username[0].firstChild.nodeValue.encode("utf-8")
        else:
            dict["username"] = None

        if password.length == 1:
            password = password[0].firstChild.nodeValue.encode("utf-8")
        else:
            password = None
        
        if dict["username"] and password:        
            logger.info("Logging to %s as %s" % (dict["host"],dict["username"]))

            dict["cookie_string"] = \
            self.__getCookie(dict["host"], dict["username"],
                             password, login_page)
        else:
            dict["cookie_string"] = None
                                  
        return dict
        
        
if __name__ == "__main__":
    config_test = """\
<?xml version="1.0" encoding="UTF-8"?>
<wfs-config>
    <general>
        <!-- Cache time in seconds -->
        <article-cache-time>300</article-cache-time>
    </general>
    <sites>
        <!--
        <site>
            <dirname>wikipedia-fr</dirname>
            <host>fr.wikipedia.org</host>
            <basename>/w/index.php</basename>
            <username>Username</username>
            <password>Password</password>
        </site>
        -->
        <site>
            <dirname>mblondel.org</dirname>
            <host>www.mblondel.org</host>
            <basename>/mediawiki/index.php</basename>
        </site>
    </sites>
</wfs-config>
    """
    
    user = WikipediaUser(config_test)
    print user.wikipedia_article_list_infos