import random
from collections import ChainMap
from itertools import cycle


class GameOver(Exception):

    def __init__(self, **scores):
        super().__init__('Game over: {}'.format(scores))
        self.scores = scores

    @classmethod
    def victory(cls, labels, winner):
        return cls(**{label: int(label == winner) for label in labels})

    @classmethod
    def draw(cls, labels):
        return cls(**{label: 0 for label in labels})


class Forfeit(Exception):

    def __init__(self, loser, reason=None):
        super().__init__('{} forfeited! Reason: {}'.format(loser, reason))
        self.loser = loser


class MoveError(ValueError):
    pass


class InvalidLocation(MoveError):

    def __init__(self, loc):
        self.loc = loc
        super().__init__('invalid location: {}'.format(loc))


class AlreadyOccupied(MoveError):

    def __init__(self, loc, contents):
        self.loc = loc
        self.contents = contents
        super().__init__('{} already contains {}'.format(loc, contents))


class TicTacToeState:

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
            raise InvalidLocation(loc)

        if data is not None:
            raise AlreadyOccupied(loc, data)

        return self.__class__(self.board.new_child({loc: label}))

    def game_over(self):
        return self.full() or self.victory()

    def full(self):
        return all(data is not None for data in self.board.values())

    def victory(self):
        size = self.size()

        checks = [
            {(r, c) for (r, c) in self.board.keys() if r == c},
            {(r, c) for (r, c) in self.board.keys() if r == size - 1 - c},
            ]

        for i in range(size):
            checks.append({(r, c) for (r, c) in self.board.keys() if r == i})
            checks.append({(r, c) for (r, c) in self.board.keys() if c == i})

        for locs in checks:
            values = {self.board[loc] for loc in locs}
            if len(values) == 1 and values != {None}:
                return True

        return False


class Game:

    def __init__(self, initial_state, players, labels):
        self.states = [initial_state]
        self.players = players
        self.labels = labels
        self.turns = cycle(zip(players, labels))

    def setup(self):
        for player, label in zip(self.players, self.labels):
            player.setup(label)

    def current_state(self):
        return self.states[-1]

    def victory(self, winner):
        pass

    def draw(self, loser):
        pass

    def move(self):
        player, label = next(self.turns)
        state = self.current_state()

        try:
            move = player.get_move(state)
        except Exception as e:
            raise Forfeit(player, e)

        try:
            new_state = state.move(move, label)
        except MoveError as e:
            raise Forfeit(player, e)

        self.states.append(new_state)

        for player in self.players:
            try:
                player.observe(state, label, move, new_state)
            except Exception as e:
                raise Forfeit(player, e)

        if new_state.game_over():
            if new_state.victory():
                raise GameOver.victory(self.labels, label)
            else:
                raise GameOver.draw(self.labels)

        return new_state

    def play(self):
        print(self.current_state())
        self.setup()
        while True:
            try:
                self.move()
            except GameOver as result:
                return result.scores
            finally:
                print(self.current_state())


class Player:

    def __str__(self):
        return 'Player {}'.format(self.label)

    def setup(self, label):
        self.label = label

    def get_move(self, board):
        raise NotImplementedError

    def observe(self, board, label, move, new_board):
        pass


class TicTacToeGame(Game):

    @classmethod
    def new(cls, *players, labels='xo', size=3):
        return cls(TicTacToeState.new(size), players, labels)


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


def play():
    game = TicTacToeGame.new(RandomPlayer(), RandomPlayer())
    scores = game.play()
    print('Scores:', scores)


# Tests: run with py.test or nosetests


def assert_equal(a, b):
    assert a == b


def assert_true(a):
    assert a


def test_tictactoeboard():
    board_str = """\
        xox
        oxo
        ox.
        """
    board = TicTacToeState.from_str(board_str)
    yield assert_equal, str(board).split(), board_str.split()

    full_str = """\
        xox
        oxo
        oxx
        """
    full_board = TicTacToeState.from_str(full_str)
    moved_board = board.move((2, 2), 'x')
    yield assert_equal, str(moved_board), str(full_board)

    problem = """\
        o..
        xox
        .x.
        """
    problem_board = TicTacToeState.from_str(problem)
    yield assert_equal, problem_board.full(), False
    yield assert_equal, problem_board.victory(), False
    yield assert_equal, problem_board.game_over(), False

    yield assert_equal, full_board.full(), True
    yield assert_equal, board.full(), False

    yield assert_equal, full_board.victory(), True
    yield assert_equal, board.victory(), False

    yield assert_equal, full_board.game_over(), True
    yield assert_equal, board.game_over(), False
