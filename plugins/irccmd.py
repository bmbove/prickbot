from base import ChatCmd


class IRCCmd(ChatCmd):

    def __init__(self, *args, **kwargs):
        self.avail_cmds = {
            'repeat': self.repeat,
            'join': self.chanjoin,
            'quit': self.servquit,
            'leave': self.chanpart,
            'say': self.say,
        }
        super(IRCCmd, self).__init__(self, *args, **kwargs)

    def repeat(self, msg):
        return [['say',self.channel, msg]] 

    def say(self, msg):
        msg_array = msg.split(" ")
        channel = msg_array[0]
        message = []
        skip = True
        for word in msg_array:
            if not skip:
                message.append(word)
            skip = False
        message = " ".join(message)
        return [['say',channel, message]] 

    def chanjoin(self, channel):
        if channel[0:1] == "#":
            return [['join', channel]]
        else:
            return [['say', self.channel, 'Invalid channel name']]

    def chanpart(self, channel):
        return [['part', channel]]

    def servquit(self, msg):
        return [['quit']]
