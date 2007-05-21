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

import os.path, re
from metadir import MetaDir
from config import CONFIG
from article import Article
from logger import LOGGER

class ArticleDir:
    def __init__(self, fs, config):
        self.fs = fs
        self.config = config

        self.files = {}
        self.dirs = {}

    def get_article_full_name(self, path):
        # Returns article name. This can include subpages.
        return '/'.join(path.split("/")[2:])

    def get_article_file_name(self, path):
        # File name as used in the directory i.e. without the subpages.
        return os.path.basename(path)

    def is_valid_file(self, path):
        file_name = self.get_article_file_name(path)
        if file_name[-3:] == ".mw":
            return True
        else:
            return False

    def contents(self, path):
        arr = self.dirs.keys()
        for k in self.files.keys():
            if not self.files[k].is_empty:
                arr.append(k)
        return arr
            
    def is_directory(self, path):
        name = self.get_article_file_name(path)
        return self.dirs.has_key(name)

    def is_file(self, path):
        if self.is_valid_file(path):
            txt = self.read_file(path)
            if len(txt.strip()) == 0:
                return False
            else:
                return True
        else:
            return False

    def read_file(self, path):
        file_name = self.get_article_file_name(path)
        full_name = self.get_article_full_name(path)
        if self.files.has_key(file_name):
            art = self.files[file_name]
        else:
            art = Article(full_name[0:-3], # removes .mw from the name
                          cache_time=CONFIG.cache_time,
                          logger = LOGGER,
                          **self.config)
            txt = art.get()
            self.files[file_name] = art
        return art.get()

    def write_to(self, path, txt):
        file_name = self.get_article_file_name(path)
        full_name = self.get_article_full_name(path)
        if self.files.has_key(file_name):
            art = self.files[file_name]
        else:
            art = Article(full_name[0:-3],
                          cache_time=CONFIG.cache_time,
                          logger = LOGGER,
                          **self.config)
            self.files[file_name] = art
        art.set(txt)

    def size(self, path):
        return len(self.read_file(path))
                    
    def mode(self, path):
        return 0755
                 
    def unlink(self, path):
        file_name = self.get_article_file_name(path)
        if self.files.has_key(file_name):
            self.files.pop(file_name)
            return True # succeeded
        else:
            return False
                            
    def mkdir(self, path):
        name = self.get_article_file_name(path)
        self.dirs[name] = True        
        self.fs.set_dir(path, ArticleDir(self.fs, self.config))
        return True                               

class Root:
    def __init__(self, fs):
        self.fs = fs
        self.dirs = {}

        self.regexp = "(wikipedia|wiktionary|wikiquote|wikibooks|wikisource)"
        self.regexp += "\-([a-z]{2})"
        self.regexp = re.compile(self.regexp, re.IGNORECASE)

        for dirname, config in CONFIG.sites.items():
            self.dirs[dirname] = True
            self.fs.set_dir("/" + dirname, ArticleDir(self.fs, config))

    def contents(self, path):
        if path == "/":
            return self.dirs.keys()
        else:
            return []

    def is_directory(self, path):
        basename = os.path.basename(path)
        if path == "/" or self.dirs.has_key(basename):
            return True
        else:
            return False

    def is_file(self, path):
        return False # There is no file at the root

    def mode(self, path):
        return 0755

    def mkdir(self, path):
        # add a site from the wikimedia foundation
        basename = os.path.basename(path)
        match = self.regexp.match(basename)

        # add it only if a directory with the same name does not exist yet
        if match and not self.is_directory(path):
            lang = match.group(2)
            site = match.group(1)
            config = {
                "host": "%s.%s.org" % (lang, site),
                "basename" : "/w/index.php"
            }
            self.dirs[basename] = True
            self.fs.set_dir("/" + basename, ArticleDir(self.fs, config))

            return True
        else:
            return False


class WikipediaFS(MetaDir):
    def __init__(self, *arr, **dic):
        MetaDir.__init__(self, *arr, **dic)
        self.set_root(Root(self))


if __name__ == "__main__":
    server = WikipediaFS(version="%prog VERSION",
                     usage='blabla',
                     dash_s_do='setsingle')

    server.parse(errex=1)
    server.multithreaded = 0
    server.main()