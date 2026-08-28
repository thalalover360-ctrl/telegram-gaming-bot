import random

def check_ttt_winner(b):
    wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
    for x, y, z in wins:
        if b[x] == b[y] == b[z] and b[x] != " ": return b[x]
    return "Draw" if " " not in b else None

def minimax(b, depth, is_max):
    res = check_ttt_winner(b)
    if res == "O": return 10 - depth
    if res == "X": return depth - 10
    if res == "Draw": return 0
    best = -1000 if is_max else 1000
    for i in range(9):
        if b[i] == " ":
            b[i] = "O" if is_max else "X"
            val = minimax(b, depth + 1, not is_max)
            b[i] = " "
            best = max(best, val) if is_max else min(best, val)
    return best

def get_best_ai_move(board, diff):
    empty = [i for i, v in enumerate(board) if v == " "]
    if diff == "easy" or (diff == "medium" and random.random() < 0.5):
        return random.choice(empty)
    best_val, best_move = -1000, empty[0]
    for i in empty:
        board[i] = "O"
        move_val = minimax(board, 0, False)
        board[i] = " "
        if move_val > best_val: best_val, best_move = move_val, i
    return best_move
  
