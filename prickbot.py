#!/usr/bin/python2
import time
import sys
sys.path.append("./")

from irc.bot import IRCBot

channels = ["#edensucks cornfest"]
bot = IRCBot('irc.freenode.net',
                6667,
                channels=channels,
                bot_nick='prickbot'
                )

channels_e = ["#panlv", "#panlvwar goomba"]
bot_e = IRCBot('irc.gamesurge.net',
                6667,
                channels=channels_e,
                bot_nick='prickbot'
                )

def main():
    global bot, bot_e
    bot.start()
    bot_e.start()

    while bot.isAlive() and bot_e.isAlive():
        time.sleep(3)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        bot.stop()
        bot_e.stop()
        exit(0)
