#!/usr/bin/python2
import time
import sys
sys.path.append("./")

from irc.bot import IRCBot

channels = ["#pricktest"]
bot = IRCBot('irc.freenode.net',
                6667,
                channels=channels,
                bot_nick='prickbot'
                )

def main():
    global bot
    bot.start()

    while bot.isAlive():
        time.sleep(3)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        bot.stop()
        exit(0)
