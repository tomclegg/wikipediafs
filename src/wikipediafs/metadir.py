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
from cStringIO import StringIO
import fuse
from fuse import Fuse
from logger import LOGGER

# This setting is optional, but it ensures that this class will keep
# working after a future API revision
fuse.fuse_python_api = (0, 2)        

class MetaDir(Fuse):
    """
    MetaDir allows to associate one directory with one class.
    Therefore each directory can define its own behaviour in its own class.
    It creates a higher level API so that we do not have do deal with
    inodes and other low level data structures.
    It takes care of editor files which can be a pain to deal with otherwise.
    """
    class Stat(fuse.Stat):
        def __init__(self):
            self.st_mode = 0
            self.st_ino = 0
            self.st_dev = 0
            self.st_nlink = 0
            self.st_uid = int(os.getuid())
            self.st_gid = int(os.getgid())
            self.st_size = 0
            self.st_atime = 0
            self.st_mtime = 0
            self.st_ctime = 0

    READ = 0
    WRITE = 1     

    def __init__(self, *arr, **dic):
        Fuse.__init__(self, *arr, **dic)        
        self.dirs = {}
        self.open_mode = None

        # hold files used by the filesystem
        # valid files should be removed from it as soon as they are "released"
        # editor files should be kept
        # (they will be deleted by the editors with unlink)
        self.files = {}

    def set_dir(self, path, directory):
        self.dirs[path] = directory
                           
    def set_root(self, directory):
        self.set_dir('/', directory)

    def get_dir(self, path):
        # Selects fs object on which we will call is_file, is_directory,
        # contents, etc
        dirname = os.path.dirname(path)
                
        if path == '/' and not self.dirs.has_key('/'):
            raise "At least the root class must be defined"
        elif self.dirs.has_key(dirname):
            return self.dirs[dirname]            
        else:
            return self.get_dir(dirname)

    def get_file_buf(self, path):
        if not self.files.has_key(path):           
            self.files[path] = StringIO()
        return self.files[path]

    def remove_file_buf(self, path):
        if self.files.has_key(path):
            self.files.pop(path)

    def has_file_buf(self, path):
        if self.files.has_key(path):
            return True
        else:
            return False                    

    def is_valid_file(self, path):
        name = os.path.basename(path)
        if len(name):            
            if name[0] == ".":# hidden file
                return False
            elif name[-4:] == ".swp": # vi swap file
                return False
            elif name[-1] == "~": # swap file too
                return False
            elif name[0] == "#" or name[0:2] == "s." or \
                 name[0:2] == "p.": # emacs
                return False
            else:
                return True           
        else:
            return True


    def getattr(self, path):
        LOGGER.debug("getattr %s" % path)
        
        d = self.get_dir(path)
        st = MetaDir.Stat()

        if self.files.has_key(path):
            st.st_mode = stat.S_IFREG | 0666
            st.st_nlink = 1
            st.st_size = 0
        elif not self.is_valid_file(path):
            return -errno.ENOENT # No such file or directory
        elif d.is_directory(path):           
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
        LOGGER.debug("readdir %s %d" % (path, offset))

        if path == "/":
            d = self.get_dir(path)
        else:
            d = self.get_dir(path + "/")            

        dirs = d.contents(path)

        if dirs is None:
            dirs = []

        for e in ('.', '..'):
            if dirs.count(e) == 0:
                dirs.append(e)
                        
        for r in dirs:
            yield fuse.Direntry(r)

    def mknod(self, path, mode, dev):
        # Creates a filesystem node
        LOGGER.debug("mknod %s %d %s" % (path, mode, dev))

    def create(self, path, mode, dev):
        # create is called to write a file that does not exist yet
        LOGGER.debug("create %s %d %d" % (path, mode, dev))

        if self.is_valid_file(path):
            d = self.get_dir(path)
            # We also need to check if it is a valid file for the fs
            if dir(d).count("is_valid_file") == 1 and not d.is_valid_file(path):
                return -errno.EACCES # Permission denied
        
        self.get_file_buf(path)
        

    def truncate(self, path, size):
        # Truncate is called just before open when a file is to be written
        # in order to make it empty
        LOGGER.debug("truncate %s %d" % (path, size))

        buf = self.get_file_buf(path)
        
        if self.is_valid_file(path):
            d = self.get_dir(path)           
            txt = d.read_file(path)
            buf.write(txt)
            
        buf.truncate(size)

    def open(self, path, flags):
        LOGGER.debug("open %s %d" % (path, flags))

        if not self.files.has_key(path):
            if self.is_valid_file(path):
                buf = self.get_file_buf(path)
                d = self.get_dir(path)
                txt = d.read_file(path)
                buf.write(txt)

    def read(self, path, size, offset):
        LOGGER.debug("read %s %d %d" % (path, size, offset))

        self.open_mode = self.READ

        buf = self.get_file_buf(path)

        buf.seek(offset)
        return buf.read(size)

    def write(self, path, txt, offset):
        LOGGER.debug("write %s [...] %d" % (path, offset))

        self.open_mode = self.WRITE

        buf = self.get_file_buf(path)

        buf.seek(offset)
        buf.write(txt)
        return len(txt)

    def release(self, path, flags):
        # Called to close the file
        LOGGER.debug("release %s %d" % (path, flags))        

        if self.open_mode == self.WRITE and self.is_valid_file(path):
            # for valid files
            buf = self.get_file_buf(path)
            d = self.get_dir(path)
            d.write_to(path, buf.getvalue())

        if self.is_valid_file(path):
            self.remove_file_buf(path) # Do not keep buffer in memory...

        self.open_mode = None   
        
        return None

    def mkdir(self, path, mode):
        LOGGER.debug("mkdir %s %d" % (path, mode))
        d = self.get_dir(path)
        
        if dir(d).count("mkdir") == 0:
            return -errno.EACCES # Permission denied
        else:
            res = d.mkdir(path)
            if res != True:
                return -errno.EACCES # Permission denied

    def unlink(self, path):
        LOGGER.debug("unlink %s" % path)
        d = self.get_dir(path)

        self.remove_file_buf(path)

        if self.is_valid_file(path):
            if dir(d).count("unlink") == 0:
                return -errno.EACCES # Permission denied
            else:
                res = d.unlink(path)
                if res != True:
                    return -errno.EACCES # Permission denied
            

    def rmdir(self, path):
        LOGGER.debug("rmdir %s" % path)
        d = self.get_dir(path)
        
        if dir(d).count("rmdir") == 0:
            return -errno.EACCES # Permission denied
        else:
            res = d.rmdir(path)
            if res != True:
                return -errno.EACCES # Permission denied

    def rename(self, path, path1):
        # Rename is handled by copying and deleting files...
        LOGGER.debug("rename %s %s" % (path, path1))
        d = self.get_dir(path)

        if self.is_valid_file(path) and d.is_file(path):
            if not self.is_valid_file(path1):
                # from a valid file to an editor file               
                buf = self.get_file_buf(path1)
                buf.write(d.read_file(path))
                # TODO : remove path ?
            else:
                # from a valid file to a valid file
                # if rename is defined 
                # TODO : with unlink method defined in fs
                pass
        elif not self.is_valid_file(path):
            if self.is_valid_file(path1) and d.is_file(path1):
                # from an editor file to a valid file
                buf = self.get_file_buf(path)                
                d.write_to(path1, buf.getvalue())
                self.open_mode = None
                self.remove_file_buf(path)
            elif not self.is_valid_file(path):
                # from an editor file to an editor file
                # TODO
                pass
            

    def utime(self, path, times):
        LOGGER.debug("utime %s %s" % (path, times))
        d = self.get_dir(path)
        
        if dir(d).count("utime") == 0:
            return -errno.ENOSYS # Not implemented
        else:
            return d.utime(path, times)
        
    def chmod(self, path, mode):
        LOGGER.debug("chmod %s %s" % (path,mode))
        return None

    def chown(self, path, user, group):
        LOGGER.debug("chown %s %s %s" % (path,user,group))
        return None

    def fsync(self, path, isfsyncfile):
        LOGGER.info("Fsync %s %s" % (path, isfsyncfile))
        return 0        
    
if __name__ == "__main__":
    class Hello:
        def __init__(self):
            self.hello_file_content = "Hello world, MetaDir powa !"

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
            if path == '/hello_file':
                return len(self.hello_file_content)
            else:
                return 0

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
            self.set_root(Hello())

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

    print fs.mkdir('/new_dir', 32768)
    