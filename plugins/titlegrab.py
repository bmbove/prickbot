import HTMLParser
import re
import urllib
import urllib2
import json
from base import ChatThread


class GrabTitle(ChatThread):

    def main_action(self):
        url = self.url_matcher(self.message)
        if url:
            return [
                ['say', self.channel, self.shorten(url)],
                ['say', self.channel, self.grab_title(url)]
            ]

    def grab_title(self, url):

        if url[0:7] != "http://" and url[0:8] != "https://":
            url = "http://" + url
        response = self.grab_page(url)

        re_string = "<title>(.*?)<\/title>"
        p = re.compile(re_string, re.DOTALL | re.M)
        m = p.search(response)
        h = HTMLParser.HTMLParser()
        title = m.groups()[0].strip()
        title = title.replace("\n", "")
        title = title.replace("\r", "")
        title = title.replace("\t", "    ")
        title = title.decode('utf-8')
        title_s = "Title: %s" % h.unescape(title)
        return title_s

    #def shorten(self, url):
        #api_key = "67IH25B30B6A95B98DEC"
        #data = {
            #'format':'json',
            #'apikey':api_key,
            #'provider':'bit_ly',
            #'url':url
        #}
        #data_enc = urllib.urlencode(data)
        #post_url = 'http://tiny-url.info/api/v1/create'
        #response = urllib2.urlopen(post_url, data_enc).read()
        #rep_j = json.loads(response)
        #if rep_j['state'] == 'ok':
            #short = rep_j['shorturl']
        #else:
            #short = "(couldn't shorten)"
        #return "Short: " + short

    # custom url_shortener
    def shorten(self, url):
        try:
            data = {
                'url':url
            }
            data_enc = urllib.urlencode(data)
            post_url = 'http://www.abarone.com/new'
            response = urllib2.urlopen(post_url, data_enc).read()
            return "Short: " + response
        except:
            return "Short: (none)"
