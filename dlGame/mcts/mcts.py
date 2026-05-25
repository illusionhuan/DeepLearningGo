"""
@Author   : mz
@Time     : 2024/1/9 9:54
Function: 蒙特卡洛树
"""
import math
import random
import time

from dlGame import agent
from dlGame.gotypes import Player

__all__ = [
    'MCTSAgent',
]

from dlGame.utils import COLS


class MCTSNode(object):
    def __init__(self, game_state, parent=None, move=None):
        self.game_state = game_state
        self.parent = parent
        self.move = move
        self.win_counts = {
            Player.black: 0,
            Player.white: 0,
        }
        self.num_rollouts = 0
        self.children = []
        self.unvisited_moves = game_state.legal_moves()

    #   向树中添加节点
    def add_random_child(self):
        index = random.randint(0, len(self.unvisited_moves) - 1)
        new_move = self.unvisited_moves.pop(index)
        new_game_state = self.game_state.apply_move(new_move)
        new_node = MCTSNode(new_game_state, self, new_move)
        self.children.append(new_node)
        return new_node

    # 更新推演统计信息
    def record_win(self, winner):
        self.win_counts[winner] += 1
        self.num_rollouts += 1

    # 检测棋局中是否还有合法动作尚未添加到树中
    def can_add_child(self):
        return len(self.unvisited_moves) > 0

    # 检测是否到达终盘
    def is_terminal(self):
        return self.game_state.is_over()

    # 返回某一方在推演中的胜率
    def winning_frac(self, player):
        return float(self.win_counts[player]) / float(self.num_rollouts)


class MCTSAgent(agent.Agent):
    def __init__(self, num_rounds, temperature):
        agent.Agent.__init__(self)
        self.num_rounds = num_rounds
        self.temperature = temperature

    def select_move(self, game_state):
        root = MCTSNode(game_state)

        for i in range(self.num_rounds):
            node = root
            while (not node.can_add_child()) and (not node.is_terminal()):
                node = self.select_child(node)

            # 添加一个新的子节点
            if node.can_add_child():
                node = node.add_random_child()

            # 从这个节点模拟一个游戏
            winner = self.simulate_random_game(node.game_state)

            # 将分数返回到树上
            while node is not None:
                node.record_win(winner)
                node = node.parent

        scored_moves = [
            (child.winning_frac(game_state.next_player), child.move, child.num_rollouts)
            for child in root.children
        ]
        scored_moves.sort(key=lambda x: x[0], reverse=True)
        for s, m, n in scored_moves[:5]:
            if m.is_pass:
                move_str = 'passes'
            elif m.is_resign:
                move_str = 'resigns'
            else:
                move_str = '%s%d' % (COLS[m.point.col - 1], m.point.row)
            print('%s - %.3f (%d)' % (move_str, s, n))

        best_move = None
        best_pct = -1.0
        for child in root.children:
            child_pct = child.winning_frac(game_state.next_player)
            if child_pct > best_pct:
                best_pct = child_pct
                best_move = child.move
        print('Select move %s with win pct %.3f' % (best_move, best_pct))
        return best_move

    def select_child(self, node):
        # 根据树的置信上限指标选择子项
        total_rollouts = sum(child.num_rollouts for child in node.children)
        log_rollouts = math.log(total_rollouts)

        best_score = -1
        best_child = None

        for child in node.children:
            win_percentage = child.winning_frac(node.game_state.next_player)
            exploration_factor = math.sqrt(log_rollouts / child.num_rollouts)
            uct_score = win_percentage + self.temperature * exploration_factor
            if uct_score > best_score:
                best_score = uct_score
                best_child = child
        return best_child

    @staticmethod
    def simulate_random_game(game):
        bots = {
            Player.black: agent.FastRandomBot(),
            Player.white: agent.FastRandomBot(),
        }
        while not game.is_over():
            # time.sleep(0.5)
            bot_move = bots[game.next_player].select_move(game)
            game = game.apply_move(bot_move)
        return game.winner()
