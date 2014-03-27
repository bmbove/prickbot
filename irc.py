import socket
import time
import re
import traceback
from threading import Thread
from command import BasicCmd
# from plugins import *


class IRCBot(Thread):

    # Usage- requires server, port, a read queue and a write queue.
    # Messages from the server will be added to the read queue, with
    # each message ending in typical IRC \r\n
    # Messages put into the write queue are things that need to be
    # sent to the server. The handler function for the write queue
    # accepts a set of commands, each in a list:
    # ["join", channel_name]
    # ["part", channel_name]
    # ["quit"]
    # ["topic", channel_name, new_topic]
    # ["say", channel/nick, message]
    # ["who", channel/nick]
    # It will send arbitrary commands with:
    # ["raw", command] (no \r\n is needed on the end of the command
    # ["delay", time] sleeps for time seconds
    # The init can also take a list of channels to autojoin once a
    # connection to the server is established.
    # Thread will attempt to auto-reconnect on ping timeout

    def __init__(self, server, port, readq, writeq, *args, **kwargs):
        # Decides whether to delay in connecting
        self.reconnect = False
        # socket for irc communication
        self.sock = False
        # server address
        self.server = server
        # server port
        self.port = port
        # whether we're connected or not
        self.connected = False
        # read queue - messages from the server
        # and stuff we may want to display
        self.readq = readq
        # write queue - we try to send everything
        # in here to the server in one way or another
        self.writeq = writeq
        # whether we've joined the initial channels
        self.joined = False
        # last time we responded to a ping from the server
        self.last_ping = time.time()
        # set nickname
        self.bot_nick = "prickbot"
        # build a list of channels to join initially
        self.channels = []
        if "channels" in kwargs:
            self.channels = kwargs['channels']

        parser = IRCParse(readq, writeq, bot_nick=self.bot_nick)
        parser.start()

        super(IRCBot, self).__init__()

    def connect(self):
        if self.sock:
            self.sock.close()
        s = socket.socket()
        if self.reconnect:
            msg = "Reconnecting to %s in 30 seconds..." % self.server
            self.readq.put(msg)
            self.joined = False
            self.last_ping = time.time()
            time.sleep(30)
        else:
            msg = "Connecting to %s ..." % self.server
            self.readq.put(msg)
        connected = False

        while not connected:
            try:
                s.connect((self.server, self.port))
                connected = True
            except Exception, e:
                print traceback.format_exc()
                print e
                connected = False

        user_str = "USER " + self.bot_nick + " blah.net * :" + self.bot_nick
        nick_str = "NICK " + self.bot_nick

        s.send(user_str + "\r\n")
        s.send(nick_str + "\r\n")
        s.settimeout(0.0)
        self.sock = s
        self.connected = connected

    def run(self):
        self.exitapp = False
        while not self.exitapp:
            if not self.connected:
                self.connect()

            message = ""

            if not self.writeq.empty():
                self.writeq_handle(self.writeq.get())
                self.writeq.task_done()

            # Grab 1 byte at a time until a full message is in the buffer
            while "\r\n" not in message:
                # if there's nothing to receive, break outta here
                try:
                    new_msg = self.sock.recv(1)
                    message = message + str(new_msg)
                except:
                    break
            # if we've got a message, handle it
            if message != "":
                self.readq.put(message)
                self.readq_handle(message)
        exit(0)

    def channel_join(self, msg):
        channel = msg[1]
        self.readq.put("Joining %s" % channel)
        self.sock.send("JOIN %s\r\n" % channel)

    def channel_leave(self, msg):
        channel = msg[1]
        if len(msg) > 2:
            reason = msg[2]
        else:
            reason = 'and I\'m out!'
        self.readq.put("Leaving %s" % channel)
        command = "PART %s :\"%s\"\r\n" % (channel, reason)
        self.readq.put(command)
        self.sock.send(command)

    def who_list(self, msg):
        entity = msg[1]
        self.readq.put("Getting WHO listing for %s" % entity)
        self.sock.send("WHO %s\r\n" % entity)

    def set_topic(self, msg):
        channel = msg[1]
        topic = msg[2]
        self.readq.put("Setting new topic for %s: %s" % (channel, topic))
        self.sock.send("TOPIC %s %s\r\n" % (channel, topic))

    def say(self, msg):
        entity = msg[1]
        message = msg[2]
        name = self.bot_nick
        # print out what we're saying, useful for logging
        leader = ":%s!~%s@%s PRIVMSG %s :%s" % (name,
                                                name,
                                                name,
                                                entity,
                                                message)
        self.readq.put(leader)
        self.sock.send("PRIVMSG %s :%s\r\n" % (entity, message))

    def quit_irc(self, msg):
        self.sock.send("QUIT :I'll be back" + "\r\n")
        self.readq.put("exit")
        self.exitapp = True

    def raw_send(self, msg):
        self.sock.send(msg[1] + "\r\n")

    def delay(self, msg):
        time.sleep(msg[1])

    def writeq_handle(self, msg):
        cmds = {'say': self.say,
                'join': self.channel_join,
                'part': self.channel_leave,
                'topic': self.set_topic,
                'who': self.who_list,
                'quit': self.quit_irc,
                'raw': self.raw_send,
                'delay': self.delay,
                }
        try:
            if msg[0] in cmds:
                command = cmds[msg[0]]
                command(msg)
        except Exception, e:
            print traceback.format_exc()
            print e

    def readq_handle(self, msg):

        # Check for Ping- response with Pong and note the time
        message_list = msg.split(" ")
        if message_list[0] == "PING":
            self.sock.send("PONG " + message_list[1] + "\r\n")
            self.readq.put("PONG")
            self.last_ping = time.time()

        lp_time = time.time() - self.last_ping
        # if we haven't been pinged in over 5 min, we probably
        # lost connection. Set some stuff to try to reconnect
        if lp_time > 330:
            msg = "Lost Connection - Ping timeout: %s seconds" % str(lp_time)
            self.readq.put(msg)
            self.connected = False
            self.reconnect = True

        # If channels are passed in the init, join them now
        if "/MOTD" in msg and self.joined is False:
            for channel in self.channels:
                self.writeq.put(['join', channel])
                self.joined = True


class IRCParse(Thread):

    def __init__(self, readq, writeq, *args, **kwargs):
        # read queue - messages from the server
        # and stuff we may want to display
        self.readq = readq
        # write queue - we try to send everything
        # in here to the server in one way or another
        self.writeq = writeq
        # latest message string from IRC server
        self.msg = ''
        # bot nickname
        if 'bot_nick' in kwargs:
            self.bot_nick = kwargs['bot_nick']
        else:
            self.bot_nick = 'prickbot'
        # start up instance of basic commands
        self.basic = BasicCmd()
        super(IRCParse, self).__init__()

    def run(self):
        self.exitapp = False
        while not self.exitapp:
            try:
                self.msg = ""
                # check for new stuff to read/parse
                if not self.readq.empty():
                    self.msg = self.readq.get().strip()
                    self.readq.task_done()
                    print self.msg
                    # exit the thread if told to do so
                    if self.msg == "exit":
                        self.exitapp = True
                    # parse response, formulate witty reply
                    reply = self.parse_msg()
                    # if we were clever enough, write reply to server
                    if reply:
                        for cmd in reply:
                            self.writeq.put(cmd)
            except Exception, e:
                print traceback.format_exc()
                print e
        exit(0)

    def parse_msg(self):

        # regex match various parts of message
        re_str = (""
                  "^:(?P<nick>(\S*))!~(?P<user>(\S*))@(?P<host>(\S*)) "
                  "(?P<command>([A-Z+])*) (?P<entity>([&#-_A-z0-9]+)?) "
                  ":?(?P<message>(.+)?$)"
                  )
        p = re.compile(re_str)
        m = p.match(self.msg)

        if m:
            msg_array = m.groupdict()
            self.msg_array = msg_array
            if self.bot_nick in msg_array['nick']:
                return False
            elif msg_array['message'][0:1] == "!":
                msg_split = msg_array['message'].split(' ')
                command = msg_split[0][1:]
                self.msg_array['param_str'] = ''
                self.msg_array['param_l'] = []
                for i in range(1, len(msg_split)):
                    self.msg_array['param_str'] += msg_split[i] + " "
                    self.msg_array['param_l'].append(msg_split[i])
                return self.interpret_command(command)
            elif self.url_matcher():
                url = self.url_matcher()
                title = self.basic.grab_title(url)
                cmd = ['say', msg_array['entity'], title]
                return [cmd]
            else:
                return False
        else:
            return False

    def interpret_command(self, command):
        try:
            cmd_list = {}
            basic_list = self.basic.avail_cmds

            for key, value in basic_list.iteritems():
                cmd_list[key] = value[0]
            if command in cmd_list:
                response = self.basic.run(self.msg_array, command)
                return response
        except Exception, e:
            print traceback.format_exc()
            print e
            return [['say', self.msg_array['entity'], e]]

    def url_matcher(self):
        message = self.msg_array['message']
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
