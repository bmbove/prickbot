import socket
import time
import re
import traceback
from threading import Thread, Event
from Queue import Queue
import plugins

class IRCBase(object):

    daemon = True
    _stop = Event()

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


class IRCBot(IRCBase, Thread):

    # ["join", channel_name]
    # ["part", channel_name]
    # ["quit"]
    # ["topic", channel_name, new_topic]
    # ["say", channel/nick, message]
    # ["who", channel/nick]
    # ["raw", command]

    connected = False
    reconnect = False
    sock = False
    joined = False
    bot_nick = "prickbot"
    channels = []
    chan_qs = {}
    sendq = Queue()
    daemon = False

    def __init__(self, server, port, *args, **kwargs):
        self.server = server
        self.port = port
        if "channels" in kwargs:
            self.channels = kwargs['channels']
        if "bot_nick" in kwargs:
            self.bot_nick = kwargs['bot_nick']

        super(IRCBot, self).__init__()

    def connect(self):
        if self.sock:
            self.sock.close()

        if not self.reconnect:
            print("Connecting to %s ..." % self.server)
        else:
            print("Reconnecting to %s in 30 seconds..." % self.server)
            self.joined = False
            time.sleep(30)

        self.sock = socket.socket()

        connected = False

        while not connected:
            try:
                self.sock.connect((self.server, self.port))
                connected = True
            except Exception, e:
                print traceback.format_exc()
                print e
                connected = False

        self.sock_write(
            "USER %s blah.net * :%s\r\n" %
            (self.bot_nick, self.bot_nick)
        )
        self.sock_write("NICK %s\r\n" % self.bot_nick)

        # timeout for cpu purposes
        self.sock.settimeout(0.1)
        self.connected = connected

    def run(self):
        while not self.stopped():
            if not self.connected:
                self.connect()

            message = ""

            while not self.sendq.empty():
            #if not self.sendq.empty():
                self.sendq_handle(self.sendq.get())
                self.sendq.task_done()
                self.sock.settimeout(0.1)


            # Grab 1 byte at a time until a full message is in the buffer
            while "\r\n" not in message:
                try:
                    message += str(self.sock.recv(1))
                except:
                    break

            if message != "":
                if(self.msg_handle(message)):
                    self.sock.settimeout(0.0)
                print(message.strip())

        for channel in self.chan_qs:
            self.destroy_thread(channel)
        self.quit_irc(None)
        self.sock.close()
        exit(0)

    def channel_join(self, msg):
        channel = msg[1]
        self.sock_write("JOIN %s" % channel)
        if channel not in self.chan_qs:
            self.create_thread(channel)

    def channel_leave(self, msg):
        channel = msg[1]
        if len(msg) > 2:
            reason = msg[2]
        else:
            reason = 'and I\'m out!'
        command = "PART %s :\"%s\"" % (channel, reason)
        self.sock_write(command)
        self.destroy_thread(channel)

    def who_list(self, msg):
        entity = msg[1]
        self.sock_write("WHO %s" % entity)

    def set_topic(self, msg):
        channel = msg[1]
        topic = msg[2]
        self.sock_write("TOPIC %s %s" % (channel, topic))

    def say(self, msg):
        entity = msg[1]
        message = msg[2]
        self.sock_write("PRIVMSG %s :%s" % (entity, message))

    def quit_irc(self, msg):
        self.sock_write("QUIT :I'll be back") 
        self.stop()

    def raw_send(self, msg):
        self.sock_write(msg[1])

    def discard(self, msg):
        pass

    def sock_write(self, to_send):
        to_send = to_send.encode('utf-8')
        print(to_send)
        self.sock.send(to_send + "\r\n")

    def sendq_handle(self, msg):
        cmds = {'say': self.say,
                'join': self.channel_join,
                'part': self.channel_leave,
                'topic': self.set_topic,
                'who': self.who_list,
                'quit': self.quit_irc,
                'raw': self.raw_send,
                'del': self.discard,
                }
        try:
            if msg[0] in cmds:
                command = cmds[msg[0]]
                command(msg)
        except Exception, e:
            print traceback.format_exc()
            print e

    def msg_handle(self, msg):

        # Check for Ping- respond with Pong and note the time
        message_list = msg.split(" ")
        if message_list[0] == "PING":
            self.sendq.put(['raw', "PONG %s" % message_list[1]])
            return True

        # If channels are passed in the init, join them now
        if "MOTD" in msg and self.joined is False:
            for channel in self.channels:
                self.sendq.put(['join', channel])
            self.joined = True
            return True

        m = self.parse_irc(msg)

        if m:
            message_dict = m.groupdict()
            # check if we have a parser thread
            # going for the channel/PM
            # and direct everything accordingly
            if message_dict['nick'] == self.bot_nick:
                return False
            if message_dict['entity'][0:1] == '#':
                channel = message_dict['entity']
            else:
                channel = message_dict['nick']
            if channel not in self.chan_qs:
                self.create_thread(channel)

            self.chan_qs[channel][0].put(msg)
            return True 
        else:
            return False

    def create_thread(self, channel):
        if channel in self.chan_qs:
            self.destory_thread(channel)
        chanq = Queue()
        parse_thread = IRCParse(channel, chanq, self.sendq)
        parse_thread.start()
        self.chan_qs[channel] = [chanq, parse_thread]

    def destroy_thread(self, channel):
        if channel in self.chan_qs:
            try:
                self.chan_qs[channel][1].stop()
                del self.chan_qs[channel][1]
                del self.chan_qs[channel][0]
            except:
                pass


class IRCParse(IRCBase, Thread):

    def __init__(self, channel, chanq, sendq, *args, **kwargs):
        self._stop = Event()
        self.channel = channel
        self.chanq = chanq
        self.sendq = sendq 
        self.commands = {}
        for key, command in plugins.avail_cmds.iteritems():
            self.commands[key] = command(channel=self.channel)
        super(IRCParse, self).__init__()


    def run(self):
        while not self.stopped():
            try:
                self.message = ""
                # wait for new stuff to read/parse
                self.message = self.chanq.get().strip()
                self.chanq.task_done()
                # parse response, formulate witty reply
                reply = self.parse_msg()
                # if we were clever enough, write reply to server
                if reply:
                    for cmd in reply:
                        self.sendq.put(cmd)
                else:
                    self.sendq.put(['del'])
            except Exception, e:
                print traceback.format_exc()
                print e
        exit(0)

    def parse_msg(self):
        m = self.parse_irc(self.message)

        if m:
            msg_d = m.groupdict()
            if msg_d['message'][0:1] == "!":
                msg_split = msg_d['message'].split(' ')
                command = msg_split[0][1:]
                params = msg_d['message'][len(command)+2:]
                if command in self.commands:
                    try:
                        return self.commands[command].run(
                            msg_d['nick'],
                            command,
                            params
                        )
                    except Exception, e:
                        print traceback.format_exc()
                        print e
                        return False
            else:
                url = self.url_matcher(msg_d['message'])
                if url:
                    return self.commands['title'].run(
                        msg_d['nick'],
                        'title',
                        url
                    )
        else:
            return False

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

    #def parse_msg(self):

        ## regex match various parts of message
        #re_str = (""
                  #"^:(?P<nick>(\S*))!~(?P<user>(\S*))@(?P<host>(\S*)) "
                  #"(?P<command>([A-Z+])*) (?P<entity>([&#-_A-z0-9]+)?) "
                  #":?(?P<message>(.+)?$)"
                  #)
        #p = re.compile(re_str)
        #m = p.match(self.msg)

        #if m:
            #msg_array = m.groupdict()
            #self.msg_array = msg_array
            #if self.bot_nick in msg_array['nick']:
                #return False
            #elif msg_array['message'][0:1] == "!":
                #msg_split = msg_array['message'].split(' ')
                #command = msg_split[0][1:]
                #self.msg_array['param_str'] = ''
                #self.msg_array['param_l'] = []
                #for i in range(1, len(msg_split)):
                    #self.msg_array['param_str'] += msg_split[i] + " "
                    #self.msg_array['param_l'].append(msg_split[i])
                #return self.interpret_command(command)
            #elif self.url_matcher():
                #url = self.url_matcher()
                #title = self.basic.grab_title(url)
                #cmd = ['say', msg_array['entity'], title]
                #return [cmd]
            #else:
                #return False
        #else:
            #return False

    #def interpret_command(self, command):
        #try:
            #cmd_list = {}
            #basic_list = self.basic.avail_cmds

            #for key, value in basic_list.iteritems():
                #cmd_list[key] = value[0]
            #if command in cmd_list:
                #response = self.basic.run(self.msg_array, command)
                #return response
        #except Exception, e:
            #print traceback.format_exc()
            #print e
            #return [['say', self.msg_array['entity'], e]]

    #def url_matcher(self):
        #message = self.msg_array['message']
        #re_str = (""
                  #"(?:https?://|www\.)"
                  #"[\w\-\@;\/?:&=%\$_.+!*\x27(),~#]+"
                  #"[\w\-\@;\/?&=%\$_+!*\x27()~]"
                  #)
        #p = re.compile(re_str)
        #m = p.search(message)
        #if m:
            #return m.group()
        #else:
            #return False
