"""
@Author   : mz
@Time     : 2023/12/27 14:33
Function: 简易版围棋机器人v1
"""
import random

import numpy

from dlGame.agent.base import Agent
from dlGame.agent.helpers import is_point_an_eye
from dlGame.goboard import Move
from dlGame.gotypes import Point

__all__ = ['RandomBot']


class RandomBot(Agent):
    def select_move(self, game_state):
        """选择一个随机的有效动作"""
        candidates = []
        for r in range(1, game_state.board.num_rows + 1):
            for c in range(1, game_state.board.num_cols + 1):
                candidate = Point(row=r, col=c)
                if game_state.is_valid_move(Move.play(candidate)) and \
                        not is_point_an_eye(game_state.board, candidate, game_state.next_player):
                    candidates.append(candidate)
        if not candidates:
            return Move.pass_turn()

        return Move.play(random.choice(candidates))