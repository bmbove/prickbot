from irc import IRCBot

ttl = False

channels = ["#pricktest"]
bot = IRCBot('irc.freenode.net',
                6667,
                channels=channels)
bot.run()
