"""
@Author   :
@Time     : 2024/3/8 14:47
Function: 棋子类
"""
import enum
from collections import namedtuple


# 棋手
class Player(enum.Enum):
    black = 1
    white = 2

    # 交替落子
    @property
    def other(self):
        return Player.black if self == Player.white else Player.white


#  使用命名元组棋盘上的交叉点
class Point(namedtuple('Point', 'row col')):
    def neighbors(self):
        return [
            Point(self.row - 1, self.col),
            Point(self.row + 1, self.col),
            Point(self.row, self.col - 1),
            Point(self.row, self.col + 1),
        ]