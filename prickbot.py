from Queue import Queue
from irc import IRCBot, IRCParse

writeq = Queue()
readq = Queue()
ttl = False


def main():
    global writeq, readq
    channels = ["#pricktest"]
    bot = IRCBot('irc.freenode.net',
                 6667,
                 readq,
                 writeq,
                 channels=channels)
    bot.start()

    parser = IRCParse(readq, writeq)
    parser.start()

    while not ttl:
        pass
    exit(0)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        writeq.put(["quit"])
        ttl = True
        raise
        exit(0)
