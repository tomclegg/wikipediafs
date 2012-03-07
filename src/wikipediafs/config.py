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

import os
from xml.dom import minidom

class Config:
    """
    Converts the XML configuration file into a Python structure.
    Creates the configuration files if needed.
    """

    DEFAULT = """\
<?xml version="1.0" encoding="UTF-8"?>
<wfs-config>
    <general>
        <!-- Cache time in seconds -->
        <article-cache-time>30</article-cache-time>
        <login-cache-time>7200</login-cache-time>
    </general>
    <sites>
        <!-- 
        Minimalist site entry sample:
        <site>
            <dirname>wikipedia-fr</dirname>
            <host>fr.wikipedia.org</host>
            <basename>/w/index.php</basename>
        </site>
        And another one with all possible options:
        <site>
            <dirname>wikipedia-fr</dirname>
            <host>fr.wikipedia.org</host>
            <port>443</port>
            <basename>/w/index.php</basename>
            <username>Username</username>
            <password>Password</password>
            <https />
            <httpauth_username>Username</httpauth_username>
            <httpauth_password>Password</httpauth_password>
            <cookie_str>cookie_name=cookie_value</cookie_str>
            <domain>DOMAIN (if using LDAP/AD Authentication extension)</domain>
        </site>
        -->        
        <!--
            Below a Mediawiki test site.
            Feel free to use it!
        --> 
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
        The XML config string can be passed as a parameter mainly for
        test purpose.
        """
        
        self.home_dir = os.environ['HOME'] + "/.wikipediafs"
        self.conf_file = self.home_dir + "/config.xml"

        self.__initConfigDir()
            
        # Loads the config from a file or from a string    
        if(not config_str):            
            self.__config = minidom.parse(self.conf_file).documentElement
        else:
            self.__config = minidom.parseString(config_str).documentElement
                            
        self.__setCacheTimes()

        self.__setDebug()
            
        self.__setSites()
            

    def __initConfigDir(self):
        # Creates .wikipediafs. in HOME if needed
        if not os.path.exists(self.home_dir):
            os.mkdir(self.home_dir,0700)

        # Creates default configuration file if needed
        if not os.path.exists(self.conf_file):
            file = open(self.conf_file,"w",0700)
            file.write(Config.DEFAULT)
            file.close()    

    def __setSites(self):
        self.sites = {}
        sites = self.__config.getElementsByTagName("site")
        for site in sites:
             dic = {}
             for ele in ("dirname", "host", "basename", "username",
             "password", "https", "port", "domain", "httpauth_username",
             "httpauth_password", "cookie_str"):
                node = site.getElementsByTagName(ele)
                if node.length == 1:
                    if node[0].firstChild:
                        dic[ele] = node[0].firstChild.nodeValue.encode("utf-8")
                    else:
                        dic[ele] = True # for elements like <https />
                else:
                    dic[ele] = None
                    
             self.sites[dic["dirname"]] = dic


    def __setCacheTimes(self):
        element = self.__config.getElementsByTagName("article-cache-time")
        if element.length == 0:
            self.cache_time = 30
        else:
            self.cache_time = int(str(element[0].firstChild.nodeValue))
        element = self.__config.getElementsByTagName("login-cache-time")
        if element.length == 0:
            self.login_cache_time = 7200
        else:
            self.login_cache_time = int(str(element[0].firstChild.nodeValue))

    def __setDebug(self):
        element = self.__config.getElementsByTagName("debug")
        if element.length == 0:
            self.debug_mode = False
        else:
            self.debug_mode = True                        
        
        
if __name__ != "__main__":
    CONFIG = Config()
else:    
    config_test = """\
<?xml version="1.0" encoding="UTF-8"?>
<wfs-config>
    <general>
        <!-- Cache time in seconds -->
        <article-cache-time>30</article-cache-time>
        <login-cache-time>7200</login-cache-time>
        <debug />
    </general>
    <sites>        
        <site>
            <dirname>wikipedia-fr</dirname>
            <host>fr.wikipedia.org</host>
            <basename>/w/index.php</basename>
            <username>Username</username>
            <password>Password</password>
        </site>        
        <site>
            <dirname>mblondel.org</dirname>
            <host>www.mblondel.org</host>
            <basename>/mediawiki/index.php</basename>
            <https />
            <port>8080</port>
        </site>
    </sites>
</wfs-config>
    """
    
    config = Config(config_test)
    print "cache time:", config.cache_time
    print "debug:", config.debug_mode
    for k, v in config.sites.items():
        print k, v        
