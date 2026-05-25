"""
@Author   :
@Time     : 2024/3/8 14:45
Function: 基本编码器
"""
import importlib


class Encoder:
    def name(self):
        raise NotImplementedError()  # 将编码器名称输出到日志并保存下来

    def encode(self, game_state):  # 将围棋棋盘转换为数值数据
        raise NotImplementedError()

    def encode_point(self, point):
        raise NotImplementedError()  # 将棋盘上的一个交叉点转换为一个整数索引

    def decode_point_index(self, index):  # 将整数索引转换为棋盘上的交叉点
        raise NotImplementedError()

    def num_points(self):  # 棋盘上交叉点的总数, 即棋盘宽乘以棋盘高
        raise NotImplementedError()

    def shape(self):
        raise NotImplementedError() # 棋盘结构编码后的形状


def get_encoder_by_name(name, board_size):
    if isinstance(board_size, int):
        board_size = (board_size, board_size)
    module = importlib.import_module('dlGame.encoders.' + name)
    constructor = getattr(module, 'create')
    return constructor(board_size)
