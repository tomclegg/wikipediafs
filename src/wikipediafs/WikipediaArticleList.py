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

from wikipediafs.WikipediaArticle import WikipediaArticle
from wikipediafs.logger import logger

class WikipediaArticleList:
    """ 
    A WikipediaArticleList is a list of WikipediaArticle objects.
    Each language has a given list of articles.
    This class deals with adding/removing articles to a list and 
    knowing if a WikipediaArticle exists in the list.
    """

    def __init__(self,list_name,list_host,list_basename,list_cookie_string,
        list_username):
        """
        Inits a WikipediaArticleList for a given language.
        """
        self.name = list_name
        self.list = []
        
        self.host = list_host
        self.basename = list_basename
        self.username = list_username
        self.cookie_string = list_cookie_string
                

        
    def __getitem__(self,article_name):
        """
        Retrieves the WikipediaArticle object.
        """
        return self.list[self.get().index(article_name)]       
        
    def get(self):
        """
        Returns a list of WikipediaArticle names.
        """
        return [article.name for article in self.list]
                
    def hasArticle(self,article_object):
        """
        Checks if article exists.
        """
        if isinstance(article_object,WikipediaArticle):
            name = article_object.name
        else:
            name = str(article_object)
            
        return bool(self.get().count(name))            

    def setArticle(self,article):
        """
        Adds the WikipediaArticle to the list.
        """
        if not isinstance(article,WikipediaArticle):
            article = article = WikipediaArticle(article_name,self)         
        
        self.list.append(article)
    
    def unsetArticle(self,article_name):
        """
        Removes the WikipediaArticle from the list.
        """
        for article_object in self.list:
            if article_object.name == article_name:
                self.list.remove(article_object)           
        
        
