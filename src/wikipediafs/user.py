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
from logger import printlog

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
                 domain=None,
                 httpauth_username=None,
                 httpauth_password=None,
                 logger = None,
                 # Not actually needed, just here for compatibility
                 name=None,
                 cookie_str=None,
                 dirname=None
                 ):

        self.username = username
        self.password = password
        self.host = host
        self.basename = basename
        self.https = https
        self.port = port
        self.domain = domain
        self.httpauth_username = httpauth_username
        self.httpauth_password = httpauth_password
        self.logger = logger

        # url pattern
        self.login_page = "%s?title=Special:Userlogin" % self.basename
        self.login_page += "&action=submit"

    def getCookieString(self):
        """
        Gets user's cookie string.
        It will then have to be passed to an Article.
        """

        printlog(self.logger, "debug", "Logging in with username %s." % self.username)
        self.logintoken = None
        cookie_list = []
        conn = ExtendedHTTPConnection(self.host, self.port, self.https)

        if self.httpauth_username and self.httpauth_password:
            conn.http_auth(self.httpauth_username, self.httpauth_password)

        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "User-agent" : "WikipediaFS"}
        conn.add_headers(headers)

        # get login page body to receive logintoken and session cookie
        conn.request(self.login_page)
        response = conn.getresponse()

        printlog(self.logger, "debug", "URL: %s, response status: %d, text: %s" % (self.login_page, response.status, response.read()))
        while response.status == 301 or response.status == 302: # follow redirects; would be better to check for status 301 and 302
            printlog(self.logger, "debug", "Redirecting to %s due to status of %d." % (response.getheader("Location"), response.status))
            response.read()
            conn.request(response.getheader("Location"))
            response = conn.getresponse()
            printlog(self.logger, "debug", "Redirected: Status %d." % (response.status))

        match = re.search('wpLoginToken"\s*value="(\w*)"',
                                response.read())
        printlog(self.logger, "debug", "Token Match: %s." % (match))

        if match:
            self.logintoken = match.group(1)
            printlog(self.logger, "debug", "Login Token: %s." % (self.logintoken))

        # post login data and receive login cookies

        # If we have a login token, then we also need to send the cookie from the initial connection.
        # If we don't, then doing so breaks the login.

        token_session = re.search('(.*?);', response.getheader("Set-Cookie")).group(1)
        if self.logintoken:
            headers["Cookie"] = token_session
            cookie_list.append(token_session)

        printlog(self.logger, "debug", "Headers:")
        printlog(self.logger, "debug", headers)

        params = {"wpName":self.username, "wpPassword":self.password,
                  "wpRemember":"1", "wpLoginattempt":"Anmelden"}

        if self.logintoken:
            params["wpLoginToken"] = self.logintoken
        if self.domain:
            params["wpDomain"] = self.domain

        params = urllib.urlencode(params)

        conn.add_data(params)
        conn.add_headers(headers)
        conn.request(self.login_page)
        response = conn.getresponse()
        printlog(self.logger, "debug", "URL: %s, response status: %d, text: %s" % (self.login_page, response.status, response.read()))

        in_cookie = re.compile(': (.*?);')

        for cookie_value in response.msg.getallmatchingheaders("set-cookie"):
            it_matches = in_cookie.search(cookie_value)

            if it_matches:
                cookie_list.append(it_matches.group(1))

        conn.close()

        printlog(self.logger, "debug", "cookie_list:")
        printlog(self.logger, "debug", cookie_list)

        if len(cookie_list) == 4:
            cookie_list.pop()
            printlog(self.logger, "info",
                     "Logged in successfully with username %s" % self.username)
                #self.logger.info("; ".join(cookie_list))
            return "; ".join(cookie_list)
        else:
            printlog(self.logger, "warning",
                     "Could not log in with username %s: %s" % self.username)
            return None


if __name__ == "__main__":
    import sys
    import getpass
    import logging

    if len(sys.argv) < 4:
        print "python user.py host urlbase username "
    else:
        if len(sys.argv) == 4:
            https = False
        else:
            https = True

        logger = logging.getLogger("mydebuglogger")
        logger.setLevel(logging.DEBUG)
        hdlr = logging.StreamHandler()
        hdlr.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)

        params = {
            "host" : sys.argv[1], # e.g. www.mblondel.org
            "basename" : sys.argv[2], # e.g. /mediawiki/index.php
            "https" : https,
            "logger": logger
        }

        password = getpass.getpass()

        user = User(sys.argv[3], password, **params)
        user.getCookieString()

