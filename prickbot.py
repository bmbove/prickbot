from irc import IRCBot

ttl = False

channels = ["#pricktest"]
bot = IRCBot('irc.freenode.net',
                6667,
                channels=channels,
                bot_nick='prick_new'
                )

def main():
    global bot, ttl
    bot.start()

    while not ttl:
        pass

    exit(0)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        bot.stop()
        ttl = True
        exit(0)
