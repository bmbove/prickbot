import urllib2
import re
import HTMLParser
import random


class BasicCmd():

    def __init__(self):
        self.msg_array = {}
        self.avail_cmds = {'quote':
                           [self.quote,
                            'Returns a quote from iheartquotes.com'],
                           'grab_title':
                           [self.grab_title,
                            'Grabs a url and returns title.'],
                           'roulette':
                           [self.roulette,
                            'Shoots someone at random.'],
                           'shoot':
                           [self.roulette,
                            'Shoots someone at random.'],
                           }
        self.rlte_track = {'chamber': [2, 1],
                           'loser': '',
                           }

    def run(self, msg_array, cmd):
        self.msg_array = msg_array
        if cmd in self.avail_cmds:
            cmd_run = self.avail_cmds[cmd][0]
            return cmd_run()

    def quote(self):

        channel = self.msg_array['entity']
        url = 'http://iheartquotes.com/api/v1/random?'
        url += 'max_lines=1&source=south_park'
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        return [['say', channel, response.readline().strip()]]

    def grab_title(self, url):

        if url[0:7] != "http://" and url[0:8] != "https://":
            url = "http://" + url
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        re_string = "<title>(.*?)<\/title>"
        p = re.compile(re_string, re.DOTALL | re.M)
        m = p.search(response.read())
        h = HTMLParser.HTMLParser()
        title = m.groups()[0].strip()
        title = title.replace("\n", "")
        title = title.replace("\r", "")
        title = title.replace("\t", "    ")
        title_s = "Title: %s" % h.unescape(title)
        return title_s

    def roulette(self):
        if not hasattr(self, 'roulette_in'):
            self.roulette_in = Roulette()
        return self.roulette_in.run(msg_array=self.msg_array)


class Roulette():

    def __init__(self):
        self.tracker = {}

    def run(self, msg_array):
        self.channel = msg_array['entity']
        self.msg_array = msg_array
        self.response = []
        if self.channel not in self.tracker:
            self.tracker[self.channel] = {
                'current_chamber': 6,
                'bullet_chamber': 1,
                'loser': '',
                'p_stats': {
                    msg_array['nick']: {
                        'deaths': 0,
                        'kills': 0,
                        'survivals': 0,
                        'trigger_pulls': 0,
                    }
                },
                'stats': {
                    'kills': 0,
                    'trigger_pulls': 0,
                }
            }
        if self.msg_array['param_str'] != '':
            if self.msg_array['param_l'][0] == 'stats':
                self.stats()
                return self.response

        self.reload()
        self.shoot()
        return self.response

    def reload(self):
        response = self.response
        chan_track = self.tracker[self.channel]
        current = chan_track['current_chamber']
        bullet = chan_track['bullet_chamber']
        if current > bullet:
            bullet = random.randint(1, 6)
            current = 1
            chan_track['current_chamber'] = current
            chan_track['bullet_chamber'] = bullet
            self.tracker[self.channel] = chan_track

            if chan_track['loser'] != '' and chan_track['loser'] != 'prickbot':
                loser = chan_track['loser']
                msg1 = "\001ACTION drags the remains of %s outside\001" % loser
                say = [['say', self.channel, msg1], ['delay', 1]]
                response.extend(say)
            msg2 = ("\001ACTION loads a single round into the cylinder,"
                    " gives it a spin, and snaps it shut\001")
            response.extend([['say', self.channel, msg2],
                             ['delay', 1],
                             ]
                            )
        self.tracker[self.channel] = chan_track
        self.response = response

    def shoot(self):
        response = self.response
        chan_track = self.tracker[self.channel]
        current = chan_track['current_chamber']
        bullet = chan_track['bullet_chamber']
        nick = self.msg_array['nick']

        if self.msg_array['param_str'] != '':
            victim = self.msg_array['param_l'][0]
        else:
            victim = nick

        if nick not in chan_track['p_stats']:
            chan_track['p_stats'][nick] = {
                'deaths': 0,
                'kills': 0,
                'survivals': 0,
                'trigger_pulls': 0,
            }
        if victim not in chan_track['p_stats']:
            chan_track['p_stats'][victim] = {
                'deaths': 0,
                'kills': 0,
                'survivals': 0,
                'trigger_pulls': 0,
            }

        if victim == 'prickbot':
            msg1 = ("\001ACTION draws the hammer back, rotating the cylinder to"
                    " chamber %s, and points the revolver at himself"
                    % (str(current)))
        else:
            msg1 = ("\001ACTION draws the hammer back, rotating the cylinder to"
                    " chamber %s, and points the revolver at %s"
                    % (str(current), victim))
        response.extend([['say', self.channel, msg1], ['delay', 2]])
        if current == bullet:
            if victim != 'prickbot':
                msg2 = "\001ACTION *BANG*\001"
                msg3 = "%s... you dead, son" % victim
                response.extend([['say', self.channel, msg2], ['delay', 2]])
                response.extend([['say', self.channel, msg3]])
            else:
                msg2 = "\001ACTION *BANG*\001"
                response.extend([['say', self.channel, msg2], ['delay', 1]])
                response.extend([['part', self.channel, 'shot in the face'], ['delay', 4]])
                response.extend([['join', self.channel]])
            chan_track['loser'] = victim
            chan_track['stats']['kills'] += 1
            chan_track['p_stats'][victim]['deaths'] += 1
            if nick != victim:
                chan_track['p_stats'][nick]['kills'] += 1
        else:
            msg2 = "\001ACTION *click*\001"
            response.extend([['say', self.channel, msg2], ['delay', 2]])
            if victim != 'prickbot':
                msg3 = "i'll allow you to live %s... for now" % victim
            else:
                msg3 = "nice try, %s" % nick
            response.extend([['say', self.channel, msg3]])
            chan_track['p_stats'][victim]['survivals'] += 1

        chan_track['current_chamber'] += 1
        chan_track['stats']['trigger_pulls'] += 1
        chan_track['p_stats'][nick]['trigger_pulls'] += 1

        self.tracker[self.channel] = chan_track
        self.response = response

    def stats(self):
        channel = self.msg_array['entity']
        stat_nicks = []
        stat_lines = []
        if len(self.msg_array['param_l']) > 1:
            nick = self.msg_array['param_l'][1]
            if nick not in self.tracker[channel]['p_stats'] and nick != 'all':
                return self.response.extend([['say',
                                              channel,
                                              'No stats for %s' % nick]])
            else:
                stat_nicks.append(nick)

        if len(stat_nicks) == 0:
            for nick in self.tracker[channel]['p_stats']:
                stat_nicks.append(nick)

        line1 = ("Nick              Deaths    Kills    "
                 "Survivals    Trigger Pulls")
        line2 = ("-------------------------------"
                 "--------------------------------")

        for nick in stat_nicks:
            stats = self.tracker[channel]['p_stats'][nick]
            while len(nick) < 16:
                nick += " "
            line3 = ("%s     %s       %s         "
                     "%s              %s " % (nick,
                                              str(stats['deaths']),
                                              str(stats['kills']),
                                              str(stats['survivals']),
                                              str(stats['trigger_pulls'])
                                              )
                     )
            stat_lines.append(line3)

        self.response.extend([['say', channel, line1]])
        self.response.extend([['say', channel, line2]])

        for line3 in stat_lines:
            self.response.extend([['say', channel, line3]])
