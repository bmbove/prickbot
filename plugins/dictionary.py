import HTMLParser
import re
from base import ChatCmd

class Define(ChatCmd):

    def __init__(self, *args, **kwargs):
        self.avail_cmds = { 'define': self.definition } 
        super(Define, self).__init__(self, *args, **kwargs)

    def definition(self, msg):

        def_list = self.webster_lookup(msg)
        if def_list:
            define_str = "%s - %s" % (msg, def_list[0])
            return [['say', self.channel, define_str]]

        # not in webster... better check urban dictionary
        cmd_ret = []

        def_list = self.urban_dictionary_lookup(msg)

        if not def_list:
            define_str = "Coudln't define %s. Quit making words up." % msg
            return [['say', self.channel, define_str]]

        for def_item in def_list[0]:
            cmd_ret.append(['say', self.channel, def_item])

        if def_list[1] != "":
            for ex in def_list[1:]:
                cmd_ret.append(['say', self.channel, ex])

        return cmd_ret

    def webster_lookup(self, word):

        h = HTMLParser.HTMLParser()
        defined = ""
        example = ""
        url = "http://www.webster-dictionary.org/definition/"
        url = url + word.replace(' ', '+')
        response = self.grab_page(url)

        if response is None:
            return False

        re_string = "<td valign=top><b>1.<\/b><\/td><td>(.*?)<\/td>"
        p = re.compile(re_string, re.DOTALL | re.M)
        m = p.search(response)
        if m is not None:
            defined = re.sub('<[^<]+?>', '', m.groups()[0].strip())
            defined = h.unescape(defined)
        else:
            return False

        return [defined, example] 

    def urban_dictionary_lookup(self, word):

        h = HTMLParser.HTMLParser()
        defined = ""
        example = ""

        url = "http://www.urbandictionary.com/define.php?term="
        url = url + word.replace(' ', '+')
        response = self.grab_page(url)
        if response is None:
            return False

        re_string = "<div class=\'meaning\'>(.*?)<\/div>"
        p = re.compile(re_string, re.DOTALL | re.M)
        m = p.search(response)
        if m is not None:
            defined = re.sub('<[^<]+?>', '', m.groups()[0].strip())
            defined = h.unescape(defined)
            defined = defined.split('\r')
        else:
            return False

        re_string2 = "<div class=\'example\'>(.*?)<\/div>"
        p2 = re.compile(re_string2, re.DOTALL | re.M)
        m2 = p2.search(response)
        if m2 is not None:
            example = re.sub('<[^<]+?>', ' ', m2.groups()[0].strip())
            example = example.replace('\n', '  ').replace('\r', '  ')
            example = h.unescape(example)

        print(defined, example)
        return [defined, example]
