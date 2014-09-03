import socket
import time
import re
import traceback
from threading import Thread
from Queue import Queue
from command import BasicCmd
import urllib2
import HTMLParser


class IRCBot():

    def __init__(self, server, port, *args, **kwargs):
        self.reconnect = False
        self.sock = False
        self.server = server
        self.port = port
        #self.botqueue = botqueue
        self.connected = False
        self.joined = False
        self.bot_nick = "prickbot_n"
        self.channels = []
        self.send_q = Queue()
        if "channels" in kwargs:
            self.channels = kwargs['channels']

    def connect(self):

        if self.sock:
            self.sock.close()

        if self.reconnect:
            print("Reconnecting to %s in 30 seconds..." % self.server)
            self.joined = False
            self.last_ping = time.time()
            time.sleep(30)
        else:
            print("Connecting to %s ..." % self.server)

        s = socket.socket()
        connected = False
        while not connected:
            try:
                s.connect((self.server, self.port))
                connected = True
            except Exception, e:
                print traceback.format_exc()
                print e
                connected = False

        user_str = "USER %s blah.net * :%s" % (self.bot_nick, self.bot_nick)
        nick_str = "NICK %s" % self.bot_nick

        s.send(user_str + "\r\n")
        s.send(nick_str + "\r\n")
        s.settimeout(0.0)
        self.sock = s
        self.connected = connected

    def run(self):
        while True:
            if not self.connected:
                self.connect()

            if not self.send_q.empty():
                self.sock.send(self.send_q.get().encode('utf-8'))
                self.send_q.task_done()

            message = ""
            # Grab 1 byte at a time until a full message is in the buffer
            while "\r\n" not in message:
                # if there's nothing to receive, break outta here
                try:
                    message += str(self.sock.recv(1))
                except:
                    break

            if "/MOTD" in message and self.joined is False:
                for channel in self.channels:
                    self.send_q.put("JOIN %s\r\n" % channel)
                self.joined = True

            # if we've got a message, handle it
            if message != "":
                parser = IRCParse(self.send_q, message, self.bot_nick)
                parser.start()



class IRCParse(Thread):

    def __init__(self, send_q, message, nick, *args, **kwargs):
        self.send_q = send_q 
        self.bot_nick = nick
        self.message = message.strip()
        super(IRCParse, self).__init__()

    def run(self):
        try:
            print self.message
            self.message_handle(self.message)
        except Exception, e:
            print traceback.format_exc()
            print e

    def say(self, msg):
        entity = msg[1]
        message = msg[2]
        m_message = []
        while len(message) > 450:
            m_message.append(message[0:450])
            message = message[450:]
        m_message.append(message)
        for message in m_message:
            leader = ":%s!~%s@%s PRIVMSG %s :%s" % (
                self.bot_nick,
                self.bot_nick,
                self.bot_nick,
                entity,
                message
            )
            print(leader)
            self.send_q.put("PRIVMSG %s :%s\r\n" % (entity, message))

    def message_handle(self, message):
        # Check for Ping- response with Pong and note the time
        message_list = message.split(" ")
        if message_list[0] == "PING":
            self.send_q.put("PONG %s\r\n" % message_list[1])
            return True 

        re_str = (
            ""
            "^:(?P<nick>(\S*))!~(?P<user>(\S*))@(?P<host>(\S*)) "
            "(?P<command>([A-Z+])*) (?P<entity>([&#-_A-z0-9]+)?) "
            ":?(?P<message>(.+)?$)"
        )

        p = re.compile(re_str)
        m = p.match(self.message)

        if m:
            self.message_dict = m.groupdict()  
            if self.bot_nick in self.message_dict['nick']:
                return False
            elif self.url_matcher():
                url = self.url_matcher()
                title = self.grab_title(url)
                self.say(['say', self.message_dict['entity'], title]) 
                return True
        else:
            return False

    def url_matcher(self):
        message = self.message_dict['message']
        re_str = (""
                  "(?:https?://|www\.)"
                  "[0-9\.\w\-\@;\/?:&=%\$_.+!*\x27(),~#]+"
                  "[0-9\.\w\-\@;\/?&=%\$_+!*\x27()~]"
                  )
        p = re.compile(re_str)
        m = p.search(message)
        if m:
            return m.group()
        else:
            return False

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
        title_s = "Title: %s" % h.unescape(title.decode('utf-8'))
        return title_s

    def grab_page(self, url):

        ua = ("Mozilla/5.0 (X11; Linux x86_64; rv:31.0)"
            " Gecko/20100101 Firefox/31.0")
        headers = { 'User-Agent' : ua }
        req = urllib2.Request(url, None, headers)
        response = urllib2.urlopen(req)

        return response.read()
