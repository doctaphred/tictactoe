import random
from collections import ChainMap
from itertools import cycle


class GameOver(Exception):
    winner = None


class Victory(GameOver):

    def __init__(self, winner):
        self.winner = winner
        super().__init__('Winner: {}'.format(winner))


class TicTacToeBoard:

    def __init__(self, board):
        self.board = board

    @classmethod
    def new(cls, size):
        locs = {(row, col) for row in range(size) for col in range(size)}
        board = ChainMap({loc: None for loc in locs})
        return cls(board)

    @classmethod
    def from_str(cls, board_str):
        board = {}
        for row, line in enumerate(board_str.split()):
            for col, player in enumerate(line):
                board[(row, col)] = player if player != '.' else None
        return cls(ChainMap(board))

    def size(self):
        return int(len(self.board) ** 0.5)

    def __str__(self):
        size = self.size()
        stuff = []
        for row in range(size):
            for col in range(size):
                stuff.append(self.board[(row, col)] or '.')
            stuff.append('\n')
        return ''.join(stuff)

    def move(self, loc, label):
        try:
            data = self.board[loc]
        except KeyError:
            raise ValueError('invalid location: {}'.format(loc))

        if data is not None:
            raise ValueError('{} already contains {}'.format(loc, data))

        return self.__class__(self.board.new_child({loc: label}))

    def game_over(self):
        return self.full() or self.victory()

    def full(self):
        return all(data is not None for data in self.board.values())

    def victory(self):
        size = self.size()

        checks = [
            {(r, c) for (r, c) in self.board.keys() if r == c},
            {(r, c) for (r, c) in self.board.keys() if r == size - c},
            ]

        for i in range(size):
            checks.append({(r, c) for (r, c) in self.board.keys() if r == i})
            checks.append({(r, c) for (r, c) in self.board.keys() if c == i})

        for locs in checks:
            values = {self.board[loc] for loc in locs}
            if len(values) == 1 and values != {None}:
                return True

        return False


class TicTacToe:

    def __init__(self, board, players):
        self.board = board
        self.players = players
        self.turns = cycle(players)
        self.active_player = next(self.turns)

    @classmethod
    def new(cls, size, players):
        return cls(TicTacToeBoard.new(size), players)

    def move(self):
        loc = self.active_player.get_move(self.board)
        label = self.active_player.label
        self.board = self.board.move(loc, label)
        if self.board.game_over():
            if self.board.victory():
                raise Victory(self.active_player)
            else:
                raise GameOver

        self.active_player = next(self.turns)

    def play(self):
        print(self.board)
        while True:
            try:
                self.move()
            except Victory as victory:
                return victory.winner
            except GameOver:
                return None
            finally:
                print(self.board)


class Player:

    def __init__(self, label):
        self.label = label

    def __str__(self):
        return self.label

    def get_move(self, board):
        raise NotImplementedError


class RandomPlayer(Player):

    def get_move(self, board):
        locs = list(board.board.keys())
        random.shuffle(locs)
        for loc in locs:
            try:
                board.move(loc, self.label)
            except ValueError:
                pass
            else:
                return loc
        raise ValueError('No valid move found')


# Tests: run with py.test or nosetests


def assert_equal(a, b):
    assert a == b


def test_tictactoeboard():
    board_str = """\
        xox
        oxo
        ox.
        """
    board = TicTacToeBoard.from_str(board_str)
    yield assert_equal, str(board).split(), board_str.split()

    full_str = """\
        xox
        oxo
        oxx
        """
    full_board = TicTacToeBoard.from_str(full_str)
    moved_board = board.move((2, 2), 'x')
    yield assert_equal, str(moved_board), str(full_board)

    yield assert_equal, full_board.full(), True
    yield assert_equal, board.full(), False

    yield assert_equal, full_board.victory(), True
    yield assert_equal, board.victory(), False

    yield assert_equal, full_board.game_over(), True
    yield assert_equal, board.game_over(), False
