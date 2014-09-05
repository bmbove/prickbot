from base import ChatCmd


class IRCCmd(ChatCmd):

    def __init__(self, *args, **kwargs):
        self.avail_cmds = {
            'repeat': self.repeat,
            'join': self.chanjoin,
            'quit': self.servquit,
            'leave': self.chanpart,
        }
        super(IRCCmd, self).__init__(self, *args, **kwargs)

    def repeat(self, msg):
        return [['say',self.channel, msg]] 

    def chanjoin(self, channel):
        if channel[0:1] == "#":
            return [['join', channel]]
        else:
            return [['say', self.channel, 'Invalid channel name']]

    def chanpart(self, channel):
        return [['part', channel]]

    def servquit(self, msg):
        return [['quit']]
