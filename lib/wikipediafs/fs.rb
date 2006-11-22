# WikipediaFS
# Copyright (C) 2005 - 2006  Mathieu Blondel
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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

require 'gettext'

module WikipediaFS

module PathUtils

    def split_path(path)
        dirname = File.dirname(path)
        basename = File.basename(path)
        if dirname == basename
            ["/", "."]
        else
            [dirname, basename]
        end
    end

    def scan_path(path)
        path.scan(/[^\/]+/)
    end

end

SwapFile = Struct.new(:str)

class Directory
    include PathUtils

    attr_accessor :name
    attr_reader :parent

    def initialize(site=nil)
        @site = site
        @files = {"." => self}
        @swap_files = {}
    end

    def parent=(par)
        @parent = par
        @files[".."] = par
    end

    def dir_directory?(filename)
        not @files[filename].nil? and @files[filename].kind_of? Directory
    end

    def [](filename)
        @files[filename]
    end

    def dir_files
        names = @files.keys.sort
        names.find_all do |n| 
            n != "." and n != ".." and not @files[n].kind_of? SwapFile
        end
    end

    def dir_file?(filename)
        if @files[filename].nil?
            if filename =~ /\.mw$/
                # If file is a .mw file and but does not exist,
                # we get the page and check if it has content or not
                page_name = filename[0..-4]
                page = Page.new(@site, page_name)

                if page.str.empty?
                    false
                else
                    @files[filename] = page
                    true
                end
            else
                false
            end
        else
            not @files[filename].kind_of?(Directory)
        end
    end

    def dir_read_file(filename)
        @files[filename].str
    end

    def dir_size(filename)
        @files[filename].str.length
    end

    def dir_can_write?(filename)
        if /\.mw$/ =~ filename or /\~$/ =~ filename or \
           /\.swp$/ =~ filename or /^\./ =~ filename
            true
        else
            false
        end
    end

    def dir_write_to(filename, str)
        unless @files.include? filename
            if /\.mw$/ =~ filename
                page_name = filename[0..-4]
                @files[filename] = Page.new(@site, page_name)
            else
                @files[filename] = SwapFile.new
            end
        end

        unless str.strip.empty?
            @files[filename].str = str
        end
    end

    def dir_can_mkdir?(filename)
        false
    end

    def dir_mkdir(dirname)
    end

    def dir_mkdir_obj(dirname, dir_obj)
        @files[dirname] = dir_obj
        @files[dirname].parent = self
    end

    def dir_can_delete?(filename)
        true
    end

    def dir_delete(filename)
        @files.delete(filename) if @files.include? filename
    end

end

class Root < Directory
    include GetText

    def initialize
        super
        parent = self
        @conf = Config.instance
        @log = Logger.instance

        @conf.sites.each do |dirname, site|
            dir_mkdir_obj(dirname, Directory.new(site))
        end
    end
  
    def get_file(path)
        dirs = scan_path(path)

        last = self
        dirs.each do |dir|
            last = last[dir]
            return nil if last == nil
        end
        last
    end
    private :get_file

    def get_parent_directory(path)
        dirname, basename = split_path(path)
        get_file(dirname)
    end
    private :get_parent_directory

    def directory?(path)
        dirname, basename = split_path(path)
        dir = get_parent_directory(path)
        ret = dir.dir_directory?(basename)
        @log.info(_("Checking if %s is a directory (%s)") % [path, ret])
        ret
    end

    def contents(path)
        @log.info(_("Listing files at %s") % path)
        get_file(path).dir_files
    end

    def file?(path)
        dirname, basename = split_path(path)
        dir = get_parent_directory(path)
        ret = dir.dir_file?(basename)
        @log.info(_("Checking if %s is a file (%s)") % [path, ret])
        ret
    end

    def read_file(path)
        @log.info(_("Reading file %s") % path)
        dirname, basename = split_path(path)
        get_parent_directory(path).dir_read_file(basename)
    end

    def size(path)
        dirname, basename = split_path(path)
        dir = get_parent_directory(path)      
        ret = dir.dir_size(basename)
        @log.info(_("Getting size of %s (%d)") % [path, ret])
        ret
    end

    def can_write?(path)
        dirname, basename = split_path(path)
        dir = get_parent_directory(path)      
        ret = dir.dir_can_write?(basename)
        @log.info(_("Checking if can write %s (%s)") % [path, ret])
        ret
    end

    def write_to(path, str)
        @log.info(_("Writing to %s") % path)
        dirname, basename = split_path(path)
        dir = get_parent_directory(path)
        dir.dir_write_to(basename, str)
    end

    def can_delete?(path)
        dirname, basename = split_path(path)
        dir = get_parent_directory(path)      
        ret = dir.dir_can_delete?(basename)
        @log.info(_("Checking if can delete %s (%s)") % [path, ret])
        ret
    end

    def delete(path)
        @log.info(_("Writing to %s") % path)
        dirname, basename = split_path(path)
        dir = get_parent_directory(path)
        dir.dir_delete(basename)
    end

    def can_mkdir?(path)
        dirname, basename = split_path(path)
        dir = get_parent_directory(path)
        ret = dir.dir_can_mkdir?(basename)
        @log.info(_("Checking if can make dir %s (%s)") % [path, ret])
        ret
    end

    def mkdir(path)
        @log.info(_("Writing to %s") % path)
        dirname, basename = split_path(path)
        dir = get_parent_directory(path)
        dir.dir_mkdir(basename)
    end

    def can_rmdir?(path)
        dirname, basename = split_path(path)
        dir = get_parent_directory(path)
        ret = dir.dir_can_rmdir?(basename)
        @log.info(_("Checking if can remove dir %s (%s)") % [path, ret])
        ret
    end

    def rmdir(path)
        @log.info(_("Removing dir %s") % path)
        dirname, basename = split_path(path)
        dir = get_parent_directory(path)
        dir.dir_rmdir(basename)
    end

end

end

if __FILE__ == $0
    require './config'
    require './logger'
    require './page'
    require 'pp'

    root = WikipediaFS::Root.new
    pp root.contents("/mblondel.org")
    pp root.file?("/mblondel.org/Japon")
    pp root.file?("/mblondel.org/Japon.mw")
    pp root.read_file("/mblondel.org/Japon.mw")
end