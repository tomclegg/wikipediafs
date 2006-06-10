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
from wikipediafs.WikipediaArticleList import WikipediaArticleList
from wikipediafs.WikipediaUser import WikipediaUser
from wikipediafs.logger import logger

from fuse import Fuse
from errno import *
from stat import *
from time import time,sleep 
import os
import re

class WikipediaFS(Fuse):
    """
    WikipediaFS is a class which defines the behaviour of the file system commands.
    
    Private methods :
    - __getCurrentDirectory(self,path)
    - __getFileName(self,path)
    - __getWikipediaArticleFromPath(self,path)
    - __isValidArticleName(self,name)
    - __createWikipediaArticleListIfNecessary(self,lang)
    - __publishArticle(self,relative_path)
    
    """
             
                
    def __init__(self, *args, **kw):
        """
        Inits the WikipediaFS.
        A WikipediaFS is defined for a given current_WikipediaUser.
        """    
        Fuse.__init__(self, *args, **kw)
        
        self.user = WikipediaUser()
        self.site_dirs = []
        self.article_list = {}
        self.open_mode = {}
        self.last_getattr_time = 0
        self.nb_getattr = 0
        os.chdir(self.user.cache_dir)        
        
        # Let's create all the necessary WikipediaArticleList
        for info in self.user.wikipedia_article_list_infos:
            self.article_list[info["list_name"]] = \
                WikipediaArticleList(info["list_name"],info["host"],\
                info["basename"],info["cookie_string"],info["username"])

            self.site_dirs.append(info["list_name"])

        
    def __getCurrentDirectory(self,path):
        """
        Gets the directory of a document based on its path.
        """
        if path.count("/") > 1:
            return os.path.dirname(path)[2:]
        elif path == "./":
            return None
        else:
            return os.path.basename(path)
        
        
    def __getFileName(self,path):
        """
        Gets the name of a document based on its path.
        """
        return os.path.basename(path)
        
        
    def __getWikipediaArticleFromPath(self,relative_path):
        """
        Gets a WikipediaArticle based on its associated file path.
        """
        current_dir = self.__getCurrentDirectory(relative_path)
        file_name = self.__getFileName(relative_path) 
        return self.article_list[current_dir][file_name]        
    
        
    def __isValidArticleName(self,name):
        """
        Checks whether a name is valid or not.
        """
        if name[:1] == "." or name[:1] == "$" or \
           name.find(".swp") != -1 or name.find("~") != -1 or \
           name.find(".py") != -1 or name.find(".so") != -1:
            logger.warning('filename %s is invalid' % name)
            return False
        else:
            return True
               
            
    def __publishArticle(self,relative_path):
        """
        Publish article based on its cache.
        """
        
        current_dir = self.__getCurrentDirectory(relative_path)
        file_name = self.__getFileName(relative_path)
        
                    
        if self.__isValidArticleName(file_name):
            current_WikipediaArticle = \
                self.__getWikipediaArticleFromPath(relative_path)
            
            if self.open_mode[file_name] == "write":
                # If it was released after having written the file,
                # then we need to update wikipedia
                msg = "Publishing %s on the website " + \
                      "(wpEdittime : %s; User : %s)"
                      
                logger.info(msg % (relative_path,
                                   current_WikipediaArticle.wpEdittime,
                                   current_WikipediaArticle. username)
                           )
                
                # Update wikipedia
                cache_art = self.user.getCacheArticle(relative_path)
                current_WikipediaArticle.set(cache_art)
                
                # Force the article to update its cache next time
                current_WikipediaArticle.last_open_time = 0
        
    def __cacheArticleIfNecessary(self,relative_path):        
        current_dir = self.__getCurrentDirectory(relative_path)
        file_name = self.__getFileName(relative_path)
        
        if self.__isValidArticleName(file_name):
            if not self.article_list[current_dir].hasArticle(file_name):
                       
                # Retrieving and caching the article
                try:
                    curr_list = self.article_list[current_dir]
                    art_obj = WikipediaArticle(file_name, curr_list)
                    art_content = art_obj.get()
                    
                    if len(art_content.strip()) > 0:
                        # Creating a cache file
                        self.user.setCacheArticle(relative_path, art_content)
                        
                        # Updating the last_open_time time
                        art_obj.last_open_time = int(time())
                        
                        # Adding the article to the list                    
                        self.article_list[current_dir].setArticle(art_obj)

                        logger.info("Articles exists, cache created for %s" %   
                                    relative_path)
                    else:
                        logger.info("Article does not exist %s" % relative_path)
                    
                except Exception,msg:
                    logger.warning(msg)
                    
            else:
                # Else we can use the WipediaArticle object
                # that is already in the list
                # We get an instance of the WikipediaArticle Object
                # that have already been created previously
                current_WikipediaArticle = \
                    self.__getWikipediaArticleFromPath(relative_path)
                
                if int(time()) - current_WikipediaArticle.last_open_time\
                    > self.user.article_cache_time:
                    
                    try:
                        self.user.setCacheArticle(relative_path,
                            current_WikipediaArticle.get())
                    
                        # Updating the last_open_time time
                        current_WikipediaArticle.last_open_time = int(time())
                        logger.info("Updating cache for % s" % relative_path)
                        
                    except Exception,msg:
                        logger.warning(msg)
                        
                else:
                    time_cache = self.user.article_cache_time - \
                    (int(time()) - current_WikipediaArticle.last_open_time)

                    logger.info("Using cache file for %s " % relative_path + \
                        "(Still valid for %d seconds)" % time_cache)
                
                
    def getattr(self, path):
        """
        getattr returns informations about the given path.
        It is called everytime the file system needs information about a file.
        An inode is composed of :
            - st_mode (protection bits)
            - st_ino (inode number)
            - st_dev (device)
            - st_nlink (number of hard links)
            - st_uid (user ID of owner)
            - st_gid (group ID of owner)
            - st_size (size of file, in bytes)
            - st_atime (time of most recent access)
            - st_mtime (time of most recent content modification)
            - st_ctime (platform dependent; time of most recent
              metadata change on Unix, or the time of creation on Windows).
        """

        # Since "os.chdir(self.user.cache_dir)" is called in __init__,
        # The following single line makes the path relative to
        # the cache dir   
        path = "." + path
        
        file_name = self.__getFileName(path)
        current_dir = self.__getCurrentDirectory(path)

        in_infinite_loop = False

        # We have to make the fs act as if every file exists
        # This is the only way to be able to get any article
        # Unfortunately, this can leads to problems when some programs
        # attempt to create temp data in file that must not exist yet

        if self.last_getattr_time == 0:
            self.last_getattr_time = int(time())
            self.nb_getattr = 1
        else:
            # If more than 10 files have been getattred in less than 5 seconds,
            # we are in an infinite loop
            if int(time()) - self.last_getattr_time < 5 \
                and self.nb_getattr > 10:
                
                in_infinite_loop = True
                self.last_getattr_time = 0
                self.nb_getattr = 0
                logger.warning("Breaking infinite loop")
                sleep(1)
                
            elif int(time()) - self.last_getattr_time > 5 \
                and self.nb_getattr > 10:
                
                self.last_getattr_time = 0
                self.nb_getattr = 0
            else:
                
                self.nb_getattr = self.nb_getattr + 1
                
        
        if not in_infinite_loop and self.__isValidArticleName(file_name) and \
           self.article_list.has_key(current_dir) and \
           not self.article_list[current_dir].hasArticle(file_name) and \
           path.count("/") == 2:
           
           try:
               int(file_name)
               # Returning fictitious values because file_name is an int
               logger.info("Getting attribute (fictitious values) for %s" % \
                            path)

               # Will cause "a file does not exist" error
               return (33188, 146926L, 774L, 1, 501, 501, 11L, 1110507883,
                       1110507883, 1110507883)
           except:
               logger.info("Getting attribute for %s" % path)
               self.__cacheArticleIfNecessary(path)
               return os.lstat(path)
            

        else:
            logger.info("Getting attribute (root) for %s" % path)
            return os.lstat(path)
            

    def getdir(self, path):
        """
        Lists the content of a directory.
        Called everytime the files contained in a directory are required.
        """
        current_dir = self.__getCurrentDirectory(path)
        
        if path == "/":
            # We just return the site list
            logger.info("Listing root dir / ")
            return map(lambda x: (x,0), self.site_dirs)
            
        elif current_dir in self.site_dirs:
            # We are in a site dir so we return the list of wikipedia
            # articles "virtually" contained in that dir.
            
            logger.info("Listing articles for %s" % path)
            return map(lambda x: (x,0), self.article_list[current_dir].get())
        
        else:
            # We return an empty list
            return map(lambda x: (x,0), [])



    def open(self, path, flags):
        """
        Opens a file.
        Called everytime a file is opened by the file system
        """  
        path = "." + path
        file_name = self.__getFileName(path)      
        logger.info("Opening file %s" % path)
        
        self.__cacheArticleIfNecessary(path)
        
        self.open_mode[file_name] = "read" 
        os.close(os.open(path,flags))
        return 0
    

    def read(self, path, len, offset):
        """
        Reads a file.
        """
        path = "." + path
        logger.info("Opening file : %s (Length: %s, Offset: %s)" %
                    (path,len,offset))
        f = open(path, "r")
        f.seek(offset)
        return f.read(len)


    

    def write(self, path, buf, off):
        """
        Writes a file.
        """
        path = "." + path
        logger.info("Writing file : %s (Offset: %s)" % (path,off))
        
        file_name = self.__getFileName(path)
        self.open_mode[file_name] = "write"
        
        f = open(path, "r+")
        f.seek(off)
        f.write(buf)
        return len(buf)

    

    def release(self, path, flags=0):
        """
        Releases a file after having read or written it.
        """
        path = "." + path
        logger.info("Releasing %s" % path)
        self.__publishArticle(relative_path=path)

        return 0
        
    def utime(self, path, times):
        """
        Sets the access and modified times of the file specified by path. 
        If times is None, then the file's access and modified times
        are set to the current time.
        """
        path = "." + path
        return os.utime(path, times)    
        
    def unlink(self, path):
        """
        Removes path.
        """
        path = "." + path
        logger.info("Removing file %s" % path)
        current_dir = self.__getCurrentDirectory(path)
        file_name = self.__getFileName(path)
        
        self.article_list[current_dir].unsetArticle(file_name)
        os.unlink(path)
        
        return 0
        
    def rmdir(self, path):
        """
        Deletes a wiki directory at the file system's root.
        """
        logger.info("Deleting directory %s" % path)

    def symlink(self, path, path1):
        path = "." + path
        path1 = "." + path1
        logger.info("Creatint a sym link of %s to %s " % (path,path1))
        return os.symlink(path, path1)

    def rename(self, path, path1):
        """
        Renames a file.
        Rename is called by the gedit editor to save an article.
        """
        path = "." + path
        path1 = "." + path1
        logger.info("Renaming %s to %s" % (path, path1))
        
        file_name = self.__getFileName(path1)
        self.open_mode[file_name] = "write"     
        
        rename_result = os.rename(path, path1)
        self.__publishArticle(relative_path=path1)
        return rename_result

    def link(self, path, path1):
        path = "." + path
        path1 = "." + path1
        logger.info("Linking %s with %s" % (path,path1))
        return os.link(path, path1)

    def chmod(self, path, mode):
        path = "." + path
        logger.info("Chmod %s %s" % (path,mode))
        return os.chmod(path, mode)

    def chown(self, path, user, group):
        path = "." + path
        logger.info("Chown %s %s %s" % (path,user,group))
        return os.chown(path, user, group)

    def truncate(self, path, size):
        path = "." + path
        logger.info("Truncating file %s" % path)
        f = open(path, "w+")
        return f.truncate(size)

    def mknod(self, path, mode, dev):
        """ Python has no os.mknod, so we can only do some things """
        path = "." + path
        logger.info("Making node")
        if S_ISREG(mode):
                open(path, "w")
        else:
                return -EINVAL

    def mkdir(self, path, mode):
        """
        Creates a new wiki directory at the file system's root.
        """
        logger.info("Creating directory %s" % path)
    
    def fsync(self, path, isfsyncfile):
        logger.info("Fsyncing path %s (isfsyncfile : %s)" % (path, isfsyncfile))
        return 0
        
    def readlink(self, path):
        path = "." + path
        logger.info("Reading link %s" % path)
        return os.readlink(path)                 
            
    def statfs(self):
        """
        Should return a tuple with the following 6 elements:
            - blocksize - size of file blocks, in bytes
            - totalblocks - total number of blocks in the filesystem
            - freeblocks - number of free blocks
            - totalfiles - total number of file inodes
            - freefiles - nunber of free file inodes
        """
        logger.info("Statfs (returning fictitious values)")
        blocks_size = 0
        blocks = 0
        blocks_free = blocks_avail = 0
        files = 0
        files_free = 0
        namelen = 0
        return (blocks_size, blocks, blocks_free, blocks_avail, files,
                files_free, namelen)
        
def start(mountpoint = None):
    server = WikipediaFS()

    if mountpoint is not None:
        server.mountpoint = mountpoint
        
    server.flags = 0
    server.multithreaded = 0;
    server.main()

if __name__ == '__main__':
    start()