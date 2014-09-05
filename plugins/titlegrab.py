import HTMLParser
import re
from base import ChatThread


class GrabTitle(ChatThread):

    def main_action(self):
        url = self.url_matcher(self.message)
        if url:
            return [['say', self.channel, self.grab_title(url)]]

    def grab_title(self, url):

        if url[0:7] != "http://" and url[0:8] != "https://":
            url = "http://" + url
        response = self.grab_page(url)

        re_string = "<title>(.*?)<\/title>"
        p = re.compile(re_string, re.DOTALL | re.M)
        m = p.search(response)
        h = HTMLParser.HTMLParser()
        title = m.groups()[0].strip()
        title = title.replace("\n", "")
        title = title.replace("\r", "")
        title = title.replace("\t", "    ")
        title = title.decode('utf-8')
        title_s = "Title: %s" % h.unescape(title)
        return title_s
