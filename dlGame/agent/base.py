"""
@Author   :
@Time     : 2024/3/8 14:35
Function: 代理接口定义
"""
__all__ = [
    'Agent',
]


class Agent:
    def __init__(self):
        pass

    def select_move(self, game_state):
        raise NotImplementedError()

    def diagnostics(self):
        return {}