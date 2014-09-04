import urllib2
import re
import HTMLParser
import random

class ChatCmd(object):
    
    name = "Command"
    desc = "An IRC Bot sub-routine"
    avail_cmds = ['title']

    def __init__(self, channel):
        self.channel = channel

    def grab_page(self, url):

        ua = ("Mozilla/5.0 (X11; Linux x86_64; rv:31.0)"
            " Gecko/20100101 Firefox/31.0")
        headers = { 'User-Agent' : ua }
        req = urllib2.Request(url, None, headers)
        response = urllib2.urlopen(req)

        return response.read()

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
        return title_s


class Repeat(ChatCmd):

    avail_cmds = ['repeat']

    def run(self, nick, cmd, msg):
        return [['say',self.channel, msg]] 

class BasicCmd():

    def __init__(self):
        self.msg_array = {}
        self.avail_cmds = {'quote':
                           [self.quote,
                            'Returns a quote from iheartquotes.com'],
                           'grab_title':
                           [self.grab_title,
                            'Grabs a url and returns title.'],
                           'roulette':
                           [self.roulette,
                            'Shoots someone at random.'],
                           'shoot':
                           [self.roulette,
                            'Shoots someone at random.'],
                           }
        self.rlte_track = {'chamber': [2, 1],
                           'loser': '',
                           }

    def run(self, msg_array, cmd):
        self.msg_array = msg_array
        if cmd in self.avail_cmds:
            cmd_run = self.avail_cmds[cmd][0]
            return cmd_run()

    def quote(self):

        channel = self.msg_array['entity']
        url = 'http://iheartquotes.com/api/v1/random?'
        url += 'max_lines=1&source=south_park'
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        return [['say', channel, response.readline().strip()]]

    def grab_title(self, url):

        if url[0:7] != "http://" and url[0:8] != "https://":
            url = "http://" + url
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        re_string = "<title>(.*?)<\/title>"
        p = re.compile(re_string, re.DOTALL | re.M)
        m = p.search(response.read())
        h = HTMLParser.HTMLParser()
        title = m.groups()[0].strip()
        title = title.replace("\n", "")
        title = title.replace("\r", "")
        title = title.replace("\t", "    ")
        title_s = "Title: %s" % h.unescape(title)
        return title_s

    def roulette(self):
        if not hasattr(self, 'roulette_in'):
            self.roulette_in = Roulette()
        return self.roulette_in.run(msg_array=self.msg_array)
