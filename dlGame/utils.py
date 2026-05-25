"""
@Author   :
@Time     : 2024/3/8 14:54
Function: 棋盘工具类
"""
import platform
import subprocess

from dlGame import gotypes
import numpy as np

COLS = 'ABCDEFGHJKLMNOPQRST'
STONE_TO_CHAR = {
    None: ' . ',
    gotypes.Player.black: ' x ',
    gotypes.Player.white: ' o ',
}


#  打印出动作
def print_move(player, move):
    if move.is_pass:
        move_str = 'passes'
    elif move.is_resign:
        move_str = 'resigns'
    else:
        move_str = '%s%d' % (COLS[move.point.col - 1], move.point.row)
    # return player, move_str
    print('%s %s' % (player, move_str))


# 显示出棋盘和棋子
def print_board(board):
    for row in range(board.num_rows, 0, -1):
        bump = " " if row <= 9 else ""
        line = []
        for col in range(1, board.num_cols + 1):
            stone = board.get(gotypes.Point(row=row, col=col))
            line.append(STONE_TO_CHAR[stone])
        print('%s%d %s' % (bump, row, ''.join(line)))
    print('    ' + '  '.join(COLS[:board.num_cols]))


# #   打印棋盘
# def print_board(board):
#     for row in range(board.num_rows, 0, -1):
#         bump = " " if row <= 9 else ""
#         line = []
#         for col in range(1, board.num_cols + 1):
#             stone = board.get(gotypes.Point(row=row, col=col))
#             line.append(STONE_TO_CHAR[stone])
#         print('%s%d %s' % (bump, row, ''.join(line)))
#     print('    ' + '  '.join(COLS[:board.num_cols]))


#   人工输入坐标
def point_from_coords(coords):
    col = COLS.index(coords[0]) + 1
    row = int(coords[1:])
    return gotypes.Point(row=row, col=col)


def coords_from_point(point):
    return '%s%d' % (
        COLS[point.col - 1],
        point.row
    )


def clear_screen():
    if platform.system() == "Windows":
        subprocess.Popen("cls", shell=True).communicate()
    else:
        print(chr(27) + "[2J")


class MoveAge():
    def __init__(self, board):
        self.move_ages = - np.ones((board.num_rows, board.num_cols))

    def get(self, row, col):
        return self.move_ages[row, col]

    def reset_age(self, point):
        self.move_ages[point.row - 1, point.col - 1] = -1

    def add(self, point):
        self.move_ages[point.row - 1, point.col - 1] = 0

    def increment_all(self):
        self.move_ages[self.move_ages > -1] += 1