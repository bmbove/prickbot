import random
from base import ChatCmd


class HangMan(ChatCmd):

    def __init__(self, *args, **kwargs):
        self.avail_cmds = {
            'hangman': self.reset,
            'guess': self.process_guess,
            'solve': self.solve,
        }
        super(HangMan, self).__init__(self, *args, **kwargs)
        self.reset(None)

    def reset(self, msg):

        line = ''
        while not line or "'" in line: 
            afile = open('/usr/share/dict/cracklib-small', 'r')
            line = next(afile)
            for num, aline in enumerate(afile):
                if random.randrange(num + 2): continue
                line = aline.strip()
            afile.close()

        board = ''
        while len(board) != len(line):
            board = board + "_"

        self.tracker = {
            'word': line,
            'draw': '[         ]',
            'letters': '',
            'board': board,
            'solved': False,
        }

        return self.draw_game()

    def process_guess(self, guess):

        guess = guess[0]

        draw = self.tracker['draw']  
        word = self.tracker['word']
        new_board = self.tracker['board']
        if new_board == word:
            self.reset(None)

        if len(guess) == 1 and guess[0].isalpha():
            if guess in word:
                locs = self.find_letters(word, guess) 
                for i in locs:
                    new_board = new_board[0:i] + guess + new_board[i+1:] 
                self.tracker['board'] = new_board
                if new_board == word:
                    return self.solve(word)
            else:
                self.tracker['letters'] += guess
                self.shift_board()
        return self.draw_game()

    def shift_board(self):
        guesses = len(self.tracker['letters'])
        new_draw = ['[']

        if guesses < 11:
            for i in range(0, guesses-1):
                new_draw.append("=")
            while len(new_draw) < 10:
                new_draw.append(" ")
            new_draw.append("]")

        new_draw = ''.join(new_draw)

        self.tracker['draw'] = new_draw 
            
    def find_letters(self, word, ch):
        return [i for i, letter in enumerate(word) if letter == ch] 

    def solve(self, solution):
        word = self.tracker['word']
        draw = self.tracker['draw']  
        letters = self.tracker['letters']

        if solution == word:
            self.tracker['solved'] = True
        else:
            self.tracker['letters'] += "$"
            self.shift_board()

        return self.draw_game()

    def draw_game(self):
        response = []

        draw = self.tracker['draw']  
        board = self.tracker['board']
        letters = self.tracker['letters']
        guesses = len(self.tracker['letters'])
        word = self.tracker['word']
        solved = self.tracker['solved']

        if guesses == 10 or solved: 
            msg = "%s    %s    %s" % (draw, word, letters)
            response.extend([
                ['say', self.channel, msg],
                ['delay', 1],
            ])
            if solved:
                response.extend([
                    ['say', self.channel, "You must be very proud of yourself"]
                ])
            else:
                response.extend([
                    ['say', self.channel, 'Game Over, Loser.' ]
                ])
            self.reset(None)
        else:
            msg = "%s    %s    %s" % (draw, board, letters)
            response.extend([['say', self.channel, msg]])

        return response 
