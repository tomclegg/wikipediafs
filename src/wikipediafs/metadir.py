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

import os, stat, errno, time
import fuse
from fuse import Fuse
from logger import logger

# This setting is optional, but it ensures that this class will keep
# working after a future API revision
fuse.fuse_python_api = (0, 2)        

class MetaDir(Fuse):
    """
    MetaDir allows to associate one directory with one class.
    Therefore each directory can define its own behaviour in its own class.
    It also creates a higher level API so that we do not have do deal with
    inodes and other low level data structures.
    """
    class Stat(fuse.Stat):
        def __init__(self):
            now = int(time.time())
            self.st_mode = 0
            self.st_ino = 0
            self.st_dev = 0
            self.st_nlink = 0
            self.st_uid = int(os.getuid())
            self.st_gid = int(os.getgid())
            self.st_size = 0
            self.st_atime = now
            self.st_mtime = now
            self.st_ctime = now

    READ = 0
    WRITE = 1            

    def __init__(self, *arr, **dic):
        Fuse.__init__(self, *arr, **dic)
        self.dirs = {}
        self.index = 1

    def set_dir(self, path, directory):
        self.dirs[path] = directory
                           
    def set_root(self, directory):
        self.set_dir('/', directory)

    def get_dir(self, path):
        dirname = os.path.dirname(path)
        if self.dirs.has_key(dirname):
            return self.dirs[dirname]
        elif self.dirs.has_key('/'):
            return self.dirs['/']
        else:
            raise "At least the root class must be defined"

    def getattr(self, path):
        logger.debug("getattr %s" % path)
        
        d = self.get_dir(path)
        st = MetaDir.Stat()
        
        if d.is_directory(path):           
            st.st_mode = stat.S_IFDIR | d.mode(path)
            st.st_nlink = 2
        elif d.is_file(path):            
            st.st_mode = stat.S_IFREG | d.mode(path)
            st.st_nlink = 1
            st.st_size = d.size(path)
        else:
            return -errno.ENOENT # No such file or directory
        return st
                            
    def readdir(self, path, offset):
        logger.debug("readdir %s %d" % (path, offset))

        d = self.get_dir(path)

        dirs = d.contents(path)

        if dirs is None:
            dirs = []

        for e in ('.', '..'):
            if dirs.count(e) == 0:
                dirs.append(e)
                        
        for r in dirs:
            yield fuse.Direntry(r)

    def open(self, path, flags):
        logger.debug("open %s %d" % (path, flags))

        self.buf = ''

        d = self.get_dir(path)
        accmode = os.O_RDONLY | os.O_WRONLY | os.O_RDWR

        if not d.is_file(path):
            return -errno.ENOENT # No such file or directory
        elif (flags & accmode) != os.O_RDONLY:
            return -errno.EACCES # Permission denied

    def read(self, path, size, offset):
        logger.debug("read %s %d %d" % (path, size, offset))

        self.open_mode = self.READ

        d = self.get_dir(path)
        accmode = os.O_RDONLY | os.O_WRONLY | os.O_RDWR

        if not d.is_file(path):
            return -errno.ENOENT # No such file or directory

        if self.buf is not None and len(self.buf) == 0:
            self.buf = d.read_file(path)

        if self.buf is None:
            return -errno.ENOENT # No such file or directory
                    
        slen = len(self.buf)                    
        
        if offset < slen:
            if offset + size > slen:
                size = slen - offset
            return self.buf[offset:offset+size]
        else:
            return ''

    def write(self, path, txt, offset):
        logger.debug("write %s [...] %d" % (path, offset))
        
        self.open_mode = self.WRITE        
        self.buf += txt
        
        return len(txt)

    def release(self, path, flags):
        logger.debug("release %s %d" % (path, flags))

        if self.open_mode == self.WRITE:
            d = self.get_dir(path)
            d.write_to(path, self.buf)
        
        return None

    def mkdir(self, path, mode):
        logger.debug("mkdir %s %d" % (path, mode))

    def unlink(self, path):
        logger.debug("unlink %s" % path)

    def rmdir(self, path):
        logger.debug("rmdir %s" % path)

    def rename(self, path, path1):
        logger.debug("rename %s %s" % (path, path1))

    def utime(self, path, times):
        logger.debug("utime %s %s" % (path, times))
    
if __name__ == "__main__":
    class Root:
        def __init__(self):
            self.hello_file_content = "Hello world, MetaDir powa !\n"

        def contents(self, path):
            if path == '/':
                return ['hello_dir', 'hello_file']
            else:
                return []

        def is_directory(self, path):
            if path == '/hello_dir' or path == '/':
                return True
            else:
                return False

        def is_file(self, path):
            if path == '/hello_file':
                return True
            else:
                return False

        def size(self, path):
            return len(self.hello_file_content)

        def mode(self, path):
            return 0755

        def read_file(self, path):
            if path == '/hello_file':
                return self.hello_file_content
            else:
                return None

        def write_to(self, path, txt):
            if path == '/hello_file':
                self.hello_file_content = txt
            
    class TestFS(MetaDir):
        def __init__(self, *arr, **dic):
            MetaDir.__init__(self, *arr, **dic)
            self.set_root(Root())

    fs = TestFS()
    print fs.getattr('/')
    print fs.readdir('/', 0)
    print fs.getattr('/hello_file')

    fs.open('/hello_file', 32768)    
    print fs.read('/hello_file', 100, 0)
    fs.release('/hello_file', 32768)

    fs.open('/hello_file', 32768)    
    fs.write('/hello_file', 'New string', 0)
    fs.release('/hello_file', 32768)

    fs.open('/hello_file', 32768)
    print fs.read('/hello_file', 100, 0)
    fs.release('/hello_file', 32768)
    