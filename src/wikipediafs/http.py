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

import os, socket, string, base64
from httplib import HTTPConnection, HTTPSConnection

class ExtendedHTTPConnection:
    """
    Transparent support for https, proxy, http auth
    """
    def __init__(self, host, port=None, https=False):
        if https and not port:
            port = 443
        elif not port:
            port = 80
        else:
            port = int(port)

        if https:
            self.conn = HTTPSConnection(host, port)
        else:
            self.conn = HTTPConnection(host, port)

        self.headers = {}
        self.data = None

    def add_header(self, header, value):
        self.headers[header] = value

    def add_headers(self, headers):
        for k, v in headers.items():
            self.add_header(k, v)

    def request(self, url):
        if self.data:
            method = "POST"
        else:
            method = "GET"

        self.conn.request(method, url, self.data, self.headers)

    def getresponse(self, *args):
        return self.conn.getresponse(*args)

    def close(self):
        return self.conn.close()

    def add_data(self, data):
        self.data = data

    def set_proxy(self):
        """
        Sets proxy if needed.
        """
        if os.environ.has_key("http_proxy"):
            http_proxy = os.environ["http_proxy"]
            http_proxy = http_proxy.replace("http://", "").rstrip("/")
            (proxy_host, proxy_port) = http_proxy.split(":")
            proxy_port = int(proxy_port)
            proxy_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            proxy_sock.connect((proxy_host, proxy_port))
            self.sock = proxy_sock

    def http_auth(self, username, password):
        httpbasicauth = "%s:%s" % (username, password)
        add_header("Authorization",
                   "Basic %s" % base64.encodestring(httpbasicauth).strip())
                   