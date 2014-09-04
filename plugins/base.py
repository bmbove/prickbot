import urllib2
import re
import HTMLParser
import random

class ChatCmd(object):
    
    name = "Command"
    desc = "An IRC Bot sub-routine"
    avail_cmds = []

    def __init__(self, channel):
        self.channel = channel

    def grab_page(self, url):

        ua = ("Mozilla/5.0 (X11; Linux x86_64; rv:31.0)"
            " Gecko/20100101 Firefox/31.0")
        headers = { 'User-Agent' : ua }
        req = urllib2.Request(url, None, headers)
        response = urllib2.urlopen(req)

        return response.read()



class Basics(ChatCmd):

    avail_cmds = [
        'repeat',
        'title',
        'join',
        'quit',
        'leave',
    ]

    def run(self, nick, cmd, msg):
        return {
            'repeat': self.repeat,
            'title': self.grab_title,
            'join': self.chanjoin,
            'quit': self.servquit,
            'leave': self.chanpart,
        }[cmd](msg)


    def repeat(self, msg):
        return [['say',self.channel, msg]] 

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
        title_s = "Title: %s" % h.unescape(title)
        return [['say', self.channel, title_s]]

    def chanjoin(self, channel):
        return [['join', channel]]

    def chanpart(self, channel):
        return [['part', channel]]

    def servquit(self, msg):
        return [['quit']]
