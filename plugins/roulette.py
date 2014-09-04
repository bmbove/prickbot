import random
from base import ChatCmd


class Roulette(ChatCmd):

    def __init__(self, *args, **kwargs):
        self.avail_cmds = {
            'shoot': self.shoot,
        }
        self.tracker = {
            'c_cham': 6,
            'b_cham': 1,
            'loser': '',
            'p_stats': {},
            'stats': {
                'kills': 0,
                'pulls': 0
            }
        }
        super(Roulette, self).__init__(self, *args, **kwargs)

    def reload(self):
        response = [] 
        tracker = self.tracker
        current = tracker['c_cham']
        bullet = tracker['b_cham']
        if current > bullet:
            bullet = random.randint(1, 6)
            current = 1
            tracker['c_cham'] = current
            tracker['b_cham'] = bullet

            if tracker['loser'] != '' and tracker['loser'] != self.bot_nick:
                loser = tracker['loser']
                msg1 = "\001ACTION drags the remains of %s outside\001" % loser
                say = [['say', self.channel, msg1], ['delay', 1]]
                response.extend(say)
            msg2 = ("\001ACTION loads a single round into the cylinder,"
                    " gives it a spin, and snaps it shut\001")
            response.extend([['say', self.channel, msg2],
                             ['delay', 1],
                             ]
                            )
            self.tracker = tracker 
        return response

    def stats_update(self, nick, victim, kill):

        tracker = self.tracker
        tracker['stats']['pulls'] += 1

        if nick not in tracker['p_stats']:
            tracker['p_stats'][nick] = {
                'deaths': 0,
                'kills': 0,
                'survivals': 0,
                'suicides': 0,
                'pulls': 0,
            }
        if victim not in tracker['p_stats']:
            tracker['p_stats'][victim] = {
                'deaths': 0,
                'kills': 0,
                'survivals': 0,
                'suicides': 0,
                'pulls': 0,
            }

        if kill:
            tracker['stats']['kills'] += 1
            tracker['p_stats'][nick]['pulls'] += 1
            if nick != victim:
                tracker['p_stats'][nick]['kills'] += 1
                tracker['p_stats'][victim]['deaths'] += 1
            else:
                tracker['p_stats'][nick]['suicides'] += 1
        else:
            if nick != victim:
                tracker['p_stats'][nick]['pulls'] += 1
                tracker['p_stats'][victim]['survivals'] += 1

        self.tracker = tracker

    def shoot(self, msg):

        if msg == 'stats':
            return self.stats()

        response = self.reload() 
        tracker = self.tracker
        current = tracker['c_cham']
        bullet = tracker['b_cham']
        nick = self.nick
        kill = False

        if msg != '':
            victim =  msg
        else:
            victim = nick

        if victim == self.bot_nick:
            victim_str = "himself"
        else:
            victim_str = victim

        msg1 = (
            "\001ACTION draws the hammer back, rotating the cylinder to"
            " chamber %s, and points the revolver at %s"
            % (str(current), victim_str)
        )
        response.extend([
            ['say', self.channel, msg1],
            ['delay', 2]
        ])

        if current == bullet:
            msg2 = "\001ACTION *BANG*\001"

            if victim != self.bot_nick: 
                msg3 = "%s... you dead, son" % victim
                response.extend([
                    ['say', self.channel, msg2],
                    ['delay', 2],
                    ['say', self.channel, msg3]
                ])
            else:
                msg2 = "\001ACTION *BANG*\001"
                response.extend([
                    ['say', self.channel, msg2],
                    ['delay', 1],
                    ['part', self.channel, 'shot in the face'],
                    ['delay', 4],
                    ['join', self.channel]
                ])
            tracker['loser'] = victim
            tracker['stats']['kills'] += 1
            kill = True
        else:
            msg2 = "\001ACTION *click*\001"
            if victim != self.bot_nick:
                msg3 = "I'll allow you to live %s... for now" % victim
            else:
                msg3 = "Nice try, %s" % nick

            response.extend([
                ['say', self.channel, msg2],
                ['delay', 2],
                ['say', self.channel, msg3]
            ])

        tracker['c_cham'] += 1
        self.tracker[self.channel] = tracker 
        self.stats_update(nick, victim, kill)
        return response

    def stats(self):
        channel = self.channel
        stat_nicks = []
        stat_lines = []
        response = []

        for nick in self.tracker['p_stats']:
            stat_nicks.append(nick)

        line1 = "%s%s%s%s%s%s" % (
            "Nick".ljust(16, ' '),
            "Deaths".center(8, ' '),
            "Kills".center(7, ' '),
            "Survivals".center(11, ' '),
            "Suicides".center(10, ' '),
            "Pulls".center(7, ' '),
        )

        line2 = "-".center(58, '-')

        for nick in stat_nicks:
            stats = self.tracker[channel]['p_stats'][nick]
            while len(nick) < 16:
                nick += " "
            line3 = "%s%s%s%s%s%s" % (
                nick.ljust(16, ' '),
                str(stats['deaths']).center(8, ' '),
                str(stats['kills']).center(7, ' '),
                str(stats['survivals']).center(11, ' '),
                str(stats['suicides']).center(10, ' '),
                str(stats['pulls']).center(7, ' ')
            )
            stat_lines.append(line3)

        response.extend([['say', channel, line1]])
        response.extend([['say', channel, line2]])

        for line3 in stat_lines:
            response.extend([['say', channel, line3]])

        return response
