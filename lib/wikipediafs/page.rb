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

require 'uri'
require 'net/https'

require 'rexml/document'
require 'rexml/streamlistener'

require "gettext"

module WikipediaFS

class User
    include GetText

    def initialize(site)
        @log = Logger.instance

        @host = site.host
        @basename = site.basename
        @port = site.port
        @https = !site.https.nil?
        @username = site.username
        @password = site.password
        @httpauth_username = site.httpauth_username
        @httpauth_password = site.httpauth_password

        @login_path = site.basename + "?title=Special:Userlogin" + \
                      "&action=submit&returnto=Special:Userlogin"

        proxy = ENV['http_proxy']

        if proxy.nil?
            @proxy_host = nil
            @proxy_port = nil
        else
            proxy = URI.parse(proxy)
            @proxy_host = proxy.host
            @proxy_port = proxy.port
        end

    end

    def login
        params = {"wpName" => @username,
                  "wpPassword" => @password,
                  "wpLoginattempt" => "Identification",
                  "wpRemember" => "1"}
                
        
        headers = {"Content-type" => "application/x-www-form-urlencoded",
                   "User-agent" => "WikipediaFS"}

        http = Net::HTTP.new(@host, @port, @proxy_host, @proxy_port)
        http.use_ssl = @https
        http.verify_mode = OpenSSL::SSL::VERIFY_NONE
        
        req = Net::HTTP::Post.new(@login_path, headers)
        req.set_form_data(params)

        unless @httpauth_username.nil? or @httpauth_password.nil?
            req.basic_auth(@httpauth_username, @httpauth_password)
        end
        
        resp = http.request(req)
        
        case resp
        when Net::HTTPSuccess, Net::HTTPRedirection

            @cookies = []
    
            resp.each_header do |k, v|
                if k == "set-cookie"
                    @cookies = v.scan(/(\S+=\S+);/i)
                    @log.debug(v)
                end
            end
    
            #@cookies.collect! { |c| c.first }
    
             if @cookies.length == 4
                @cookies.pop
                @cookie_string = @cookies.join("; ")
                @log.info(_("Logged in successfully"))
            else
                @log.error(_("Could not login to %s") % @host)
                @cookie_string = nil;
            end
        else
            @log.error(_("Could not login to %s (%s)") % [@host, resp.code])
            @log.error(_("Response body was %s\n\n") % resp.body)
        end
        
        @cookie_string
    end
end

class Page
    include GetText

    include REXML::StreamListener

    attr_reader :wp_edit_time, :wp_wp_start_time, :wp_edit_token

    def initialize(site, page_name)
        @log = Logger.instance
        @conf = Config.instance

        @host = site.host
        @basename = site.basename
        @port = site.port
        @https = !site.https.nil?
        @httpauth_username = site.httpauth_username
        @httpauth_password = site.httpauth_password
        @cookie_string = site.cookie_string

        @page_name = page_name

        @edit_path = "%s?title=%s&action=edit" % [@basename, @page_name]
        @submit_path = "%s?title=%s&action=submit" % [@basename, @page_name]

        @in_textarea = false
        @wp_edit_time = 0
        @wp_start_time = 0
        @wp_edit_token = nil

        @last_get = 0

        proxy = ENV['http_proxy']

        if proxy.nil?
            @proxy_host = nil
            @proxy_port = nil
        else
            proxy = URI.parse(proxy)
            @proxy_host = proxy.host
            @proxy_port = proxy.port
        end
    end

    def get
        return @str if Time.now.to_i - @last_get < @conf.article_cache_time

        headers = {}

        unless @cookie_string.nil?
            headers["Cookie"] = @cookie_string            
        end

        http = Net::HTTP.new(@host, @port, @proxy_host, @proxy_port)
        http.use_ssl = @https
        http.verify_mode = OpenSSL::SSL::VERIFY_NONE
        
        req = Net::HTTP::Get.new(@edit_path, headers)

        unless @httpauth_username.nil? or @httpauth_password.nil?
            req.basic_auth(@httpauth_username, @httpauth_password)
        end
        
        resp = http.request(req)

        REXML::Document.parse_stream(resp.body, self)

        @last_get = Time.now.to_i

        @str.strip!
    end
    alias :str :get

    def set(new_str)
        summaries = str.scan(/(\[\[Summary:(.*)\]\])/i)
        if summaries.length > 0
            summary_tag, summary = summaries.last
            new_str.gsub(summary_tag, "")
        else
            summary = " "
        end
       
        # wpEdittime is empty if the article is a new article
        params = {"wpTextbox1" => new_str,
                  "wpSummary" => summary,
                  "wpEdittime" => @wp_edit_time, 
                  "wpStarttime" => @wp_start_time,
                  "wpSave" => 1}
        
        # Needed for logged in edition
        unless @wp_edit_token.nil?
            params["wpEditToken"] = @wp_edit_token
        end
                       
        headers = {"Content-type" => "application/x-www-form-urlencoded",
                   "User-agent" => "WikipediaFS"}
        
        unless @cookie_string.nil?
            headers["Cookie"] = @cookie_string
        end
        begin
        http = Net::HTTP.new(@host, @port, @proxy_host, @proxy_port)
        http.use_ssl = @https
        http.verify_mode = OpenSSL::SSL::VERIFY_NONE
        
        req = Net::HTTP::Post.new(@submit_path, headers)
        req.set_form_data(params)

        unless @httpauth_username.nil? or @httpauth_password.nil?
            req.basic_auth(@httpauth_username, @httpauth_password)
        end
        
        resp = http.request(req)
        rescue => e
            @log.info(_("Error %s") % e.to_s)
        end

        case resp
        when Net::HTTPSuccess, Net::HTTPRedirection
            @log.info(_("Page updated successfully"))
        else
            @log.error(_("Login error (%s)") % resp.code)
            @log.error(_("Response body was %s\n\n") % resp.body)        
        end
        
        # Force to recache the article next time
        @last_get = 0
    end
    alias :str= :set
    
    # Methods called when XHTML is parsed

    def tag_start(name, attrs)
        if name == "textarea"
            @str = ""
            @in_textarea = true 
        elsif name == "input" and attrs.has_key? "name"
            if attrs["name"] == "wpEdittime"
                @wp_edit_time = attrs["value"]
            elsif attrs["name"] == "wpEditToken"
                @wp_edit_token = attrs["value"]
            elsif attrs["name"] == "wpStarttime"
                @wp_start_time = attrs["value"]
            end
        end
    end

    def tag_end(name)
        @in_textarea = false if name == "textarea"
    end

    def text(txt)
        @str += txt if @in_textarea
    end

end

end

if __FILE__ == $0
    require './config'
    require './logger'

    site = WikipediaFS::Config::Site.new
    site.host = "www.mblondel.org"
    site.basename = "/mediawiki/index.php"
    site.username = ARGV[0]
    site.password = ARGV[1]
    site.https = true
    site.port = 443

    #user = WikipediaFS::User.new(site)
    #site.cookie_string = user.login

    page = WikipediaFS::Page.new(site, "Japon")
    p page.get
    p page.get
    #page.set(page.str + " " + rand.to_s)
end