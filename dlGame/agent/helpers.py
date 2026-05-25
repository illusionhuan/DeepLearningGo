"""
@Author   :
@Time     : 2024/3/8 14:41
Function: 判断是否有眼
"""
from dlGame.gotypes import Point

__all__ = [
    'is_point_an_eye',
]

# 判断是否有眼
def is_point_an_eye(board, point, color):
    if board.get(point) is not None:  # 眼必须是一个空点
        return False
    for neighbor in point.neighbors():  # 所有相邻的点都必须是己方的棋子
        if board.is_on_grid(neighbor):
            neighbor_color = board.get(neighbor)
            if neighbor_color != color:
                return False
    friendly_corners = 0  # 如果这个空点位于棋盘内部，己方棋子至少要控制4个对角相邻点中的3个;而如果空点在边缘，则必须控制所有的对角相邻点
    off_board_corners = 0
    corners = [
        Point(point.row - 1, point.col - 1),
        Point(point.row - 1, point.col + 1),
        Point(point.row + 1, point.col + 1),
        Point(point.row + 1, point.col - 1),
    ]
    for corner in corners:
        if board.is_on_grid(corner):
            corner_color = board.get(corner)
            if corner_color == color:
                friendly_corners += 1
        else:
            off_board_corners += 1
    if off_board_corners > 0:
        return off_board_corners + friendly_corners == 4  # 空点在边缘或角落
    return friendly_corners >= 3  # 空点在棋盘内部
