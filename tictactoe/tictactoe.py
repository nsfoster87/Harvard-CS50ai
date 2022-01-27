"""
Tic Tac Toe Player
"""

import math
import copy

X = "X"
O = "O"
EMPTY = None


def initial_state():
    """
    Returns starting state of the board.
    """
    return [[EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY]]


def player(board):
    """
    Returns player who has the next turn on a board.
    """
    x_count = 0
    o_count = 0
    for row in board:
        for cell in row:
            if cell == X:
                x_count += 1
            elif cell == O:
                o_count += 1
    if o_count < x_count:
        return O
    return X


def actions(board):
    """
    Returns set of all possible actions (i, j) available on the board.
    """
    actions = set()
    for i in range(len(board)):
        for j in range(len(board[i])):
            if board[i][j] == EMPTY:
                actions.add((i, j))
    return actions


def result(board, action):
    """
    Returns the board that results from making move (i, j) on the board.
    """
    # if action not valid, raise exception
    if action not in actions(board):
        raise Exception("Not a valid action")

    new_board = copy.deepcopy(board)
    new_board[action[0]][action[1]] = player(board)
    return new_board


def winner(board):
    """
    Returns the winner of the game, if there is one.
    Specific to a 3x3 board
    """
    for i in range(len(board)):
        if board[0][i] == board[1][i] == board[2][i] != EMPTY:
            return board[0][i]
        if board[i][0] == board[i][1] == board[i][2] != EMPTY:
            return board[i][0]
    if board[0][0] == board[1][1] == board[2][2] != EMPTY:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != EMPTY:
        return board[0][2]
    return None



def terminal(board):
    """
    Returns True if game is over, False otherwise.
    """
    if winner(board) != None:
        return True
    for row in board:
        for cell in row:
            if cell == EMPTY:
                return False
    return True


def utility(board):
    """
    Returns 1 if X has won the game, -1 if O has won, 0 otherwise.
    """
    if winner(board) == X:
        return 1
    if winner(board) == O:
        return -1
    if winner(board) == None:
        return 0


def minimax(board):
    """
    Returns the optimal action for the current player on the board.
    """

    if terminal(board):
        return None

    optimal_action = list(actions(board))[0]
    opt_min_value = minValue(result(board, optimal_action))
    opt_max_value = maxValue(result(board, optimal_action))
    for action in actions(board):
        if player(board) == X:
            action_min_value = minValue(result(board, action))
            if action_min_value > opt_min_value:
                optimal_action = action
                opt_min_value = action_min_value
        if player(board) == O:
            action_max_value = maxValue(result(board, action))
            if action_max_value < opt_max_value:
                optimal_action = action
                opt_max_value = action_max_value
    return optimal_action


def maxValue(board):
    max_value = -math.inf
    if terminal(board):
        return utility(board)
    for action in actions(board):
        max_value = max(max_value, minValue(result(board, action)))
    return max_value

def minValue(board):
    min_value = math.inf
    if terminal(board):
        return utility(board)
    for action in actions(board):
        min_value = min(min_value, maxValue(result(board, action)))
    return min_value
