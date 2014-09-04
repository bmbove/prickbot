#!/usr/bin/python2
from irc import IRCBot

ttl = False

channels = ["#pricktest"]
bot = IRCBot('irc.gamesurge.net',
                6667,
                channels=channels,
                bot_nick='prick_new'
                )

def main():
    global bot
    bot.start()

    while bot.isAlive():
        pass

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        bot.stop()
        exit(0)
