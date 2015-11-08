import json
from base import ChatCmd

class Movie(ChatCmd):

    def __init__(self, *args, **kwargs):
        self.avail_cmds = {'movie': self.lookup}
        super(Movie, self).__init__(self, *args, **kwargs)

    def lookup(self, title):
        url = "http://www.omdbapi.com/?t=%s" % title.replace(' ', '+')
        data = json.loads(self.grab_page(url))

        if not data:
            return ['say', self.channel, 'Error connecting to database']

        if data['Response'] == 'False':
            if 'Error' in data:
                return [['say', self.channel, 'Movie not found']]
            else:
                return [['say', self.channel, 'Error searching imdb']]
        else:
            line1 = '%s (%s) - %s. Rating: %s/10' % (
                data['Title'],
                data['Year'],
                data['Director'],
                data['imdbRating']
            )
            line2 = data['Actors']
            line3 = data['Plot'] 
            return [
                ['say', self.channel, line1],
                ['delay', 1],
                ['say', self.channel, line2],
                ['delay', 1],
                ['say', self.channel, line3],
            ]
