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

$KCODE = "u"

require 'singleton'
require 'rexml/document'

module WikipediaFS

class Config < REXML::Document
    include Singleton

    SITE_VARIABLES_NAMES = [:dirname, :host, :port, :basename, 
                            :username, :password, :https,
                            :httpauth_username, :httpauth_password,
                            :cookie_string]

    Site = Struct.new(*SITE_VARIABLES_NAMES)

DEFAULT_CONFIG = <<EOS
<?xml version="1.0" encoding="UTF-8"?>
<wfs-config>
    <general>
        <!-- Cache time in seconds -->
        <article-cache-time>300</article-cache-time>
    </general>
    <sites>
        <!-- 
        Minimalist site entry sample:
        <site>
            <dirname>wikipedia-fr</dirname>
            <host>fr.wikipedia.org</host>
            <basename>/w/index.php</basename>
        </site>
        And another one with all possible informations:
        <site>
            <dirname>wikipedia-fr</dirname>
            <host>fr.wikipedia.org</host>
            <port>443</port>
            <basename>/w/index.php</basename>
            <username>Username</username>
            <password>Password</password>
            <https />
            <httpauth-username>Username</httpauth-username>
            <httpauth-password>Password</httpauth-password>
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
EOS

    attr_accessor :article_cache_time, :sites

    def initialize
        @config_dir = File.join(ENV['HOME'], ".wikipediafs")
        @cache_dir = File.join(@config_dir, ".cache")
        @config_file = File.join(@config_dir, "config.xml")    

        initialize_config_dir

        # Start reading config
        super(File.new(@config_file))

        general = root.elements['general']
        @article_cache_time = general.elements['article-cache-time'].text.to_i
        @article_cache_time = 300 if @article_cache_time.nil?

        # The following code build a Hash which 
        # keys are dirnames and values are Site objects
        @sites = {}
        elements.each("wfs-config/sites/site") do |site|
            site_variables_elements = site.elements
            
            site_variables = SITE_VARIABLES_NAMES.collect do |var_name|
                var_name = var_name.to_s.gsub("_", "-")
                variable = site_variables_elements[var_name]
                if variable.nil?
                    # Variable is set to nil if not found
                    nil
                elsif variable.has_text?
                    # Variable is set to its text if has text
                    variable.text
                else
                    # Variable is set to true if has not text (e.g <https />)
                    true
                end
            end

            @sites[site_variables[0]] = Site.new(*site_variables)
            
            if @sites[site_variables[0]].https.nil? and \
               @sites[site_variables[0]].port.nil?

               @sites[site_variables[0]].port = 80

            elsif @sites[site_variables[0]].https == true and \

                  @sites[site_variables[0]].port.nil?
                  @sites[site_variables[0]].port = 443
            end
        end
    end

    def initialize_config_dir
        unless File.exist?(@config_dir)
            Dir.mkdir(@config_dir, 0700)
        end

        unless File.exist?(@cache_dir)
            Dir.mkdir(@cache_dir, 0700)
        end

        unless File.exist?(@config_file)
            File.open(@config_file, File::CREAT | File::RDWR, 0700) do |f|
                f.write(DEFAULT_CONFIG)
            end
        end

    end

end

end

if __FILE__ == $0
    require 'pp'
    conf = WikipediaFS::Config.instance
    p conf.article_cache_time, conf.sites
end
        