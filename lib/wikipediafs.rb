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

require 'fusefs'

begin
    require 'gettext'
rescue LoadError
    require 'wikipediafs/gettext'
end

require 'wikipediafs/config'
require 'wikipediafs/logger'
require 'wikipediafs/page'
require 'wikipediafs/fs'

module WikipediaFS

    def self.main
        FuseFS.set_root(Root.new)
        FuseFS.mount_under ARGV.shift
        FuseFS.handle_editor = false
        FuseFS.run
    end

end