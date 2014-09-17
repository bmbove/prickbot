import urllib2
import re
import time
import string
import sys
import random
import traceback
from threading import Thread, Event
from Queue import Queue
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


Base = declarative_base()


class ChatCmd(object):
    
    avail_cmds = {}

    def __init__(self, *args, **kwargs):
        self.name = "Command"
        self.desc = "An IRC Bot sub-routine"

        if 'channel' in kwargs:
            self.channel = kwargs['channel']
        else:
            self.channel = ''

        if 'bot_nick' in kwargs:
            self.bot_nick = kwargs['bot_nick']
        else:
            self.bot_nick = ''

    def sqlinit(self):
        self.engine = create_engine('sqlite:///database.db')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker()
        Session.configure(bind=self.engine)
        self.session = Session()

    def run(self, nick, cmd, msg):
        try:
            self.cmd = cmd
            self.nick = nick
            self.msg = msg
            return self.avail_cmds[cmd](msg)
        except Exception, e:
            return ['say', self.channel, str(e)]


    def grab_page(self, url):

        ua = ("Mozilla/5.0 (X11; Linux x86_64; rv:31.0)"
            " Gecko/20100101 Firefox/31.0")
        headers = { 'User-Agent' : ua }
        req = urllib2.Request(url, None, headers)
        response = urllib2.urlopen(req)

        return response.read()

    def url_matcher(self, message):
        re_str = (""
                  "(?:https?://|www\.)"
                  "[\w\-\@;\/?:&=%\$_.+!*\x27(),~#]+"
                  "[\w\-\@;\/?&=%\$_+!*\x27()~]"
                  )
        p = re.compile(re_str)
        m = p.search(message)
        if m:
            return m.group()
        else:
            return False


class ChatThread(ChatCmd, Thread):

    daemon = True
    blocking = True
    threaded = True

    def __init__(self, recvq, sendq, *args, **kwargs):
        self._stop = Event()
        Thread.__init__(self)
        self.avail_cmds = {self.string_gen():str}
        self.recvq = recvq
        self.sendq = sendq
        super(ChatThread, self).__init__(self, *args, **kwargs)

    def string_gen(self):
        gen = ''.join(random.choice(string.ascii_lowercase) for i in range(12))
        return gen

    def run(self):
        while not self.stopped():
            try:
                self.message = ""
                # wait for new stuff to read/parse
                # don't wait if blocking is false
                if self.blocking:
                    self.message = self.recvq.get().strip()
                    self.recvq.task_done()
                elif not self.recvq.empty():
                    self.message = self.recvq.get().strip()
                    self.recvq.task_done()
                # parse response, formulate witty reply
                # run this every loop, no matter what
                reply = self.main_action()
                # if we were clever enough, write reply to server
                if reply:
                    for cmd in reply:
                        if cmd[0] == 'delay':
                            # sleep here instead of main thread
                            time.sleep(cmd[1])
                        else:
                            self.sendq.put(cmd)
                # take it easy in this loop
                time.sleep(0.1)
            except Exception, e:
                print traceback.format_exc()
                print e
        exit(0)

    def main_action(self):
        return False

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def parse_irc(self, message):
        re_str = (""
                  "^:(?P<nick>(\S*))!~(?P<user>(\S*))@(?P<host>(\S*)) "
                  "(?P<command>([A-Z+])*) (?P<entity>([&#-_A-z0-9]+)?) "
                  ":?(?P<message>(.+)?$)"
                  )
        p = re.compile(re_str)
        m = p.match(message)

        return m
