"""
@Author   :
@Time     : 2024/4/8 9:19
Function: 围棋AI网页
"""
import logging
import time
from datetime import datetime

from flask import Flask, request, jsonify, send_from_directory
from dlGame import goboard, gotypes
from dlGame.agent import FastRandomBot, is_point_an_eye
from dlGame.goboard import Move
from dlGame.gosgf import Sgf_game
from dlGame.gotypes import Point
from dlGame.utils import coords_from_point
from dlGame.utils import point_from_coords

from dlGame.agent import load_prediction_agent, load_policy_agent, AlphaGoMCTS
from dlGame.rl import load_value_agent
import h5py
import os

# 获取当前文件的绝对路径
current_file_path = os.path.abspath(__file__)

# 获取当前文件所在的目录（examples）
current_dir = os.path.dirname(current_file_path)

if __name__ == '__main__':
    here = os.path.dirname(__file__)
    static_path = os.path.join(here, 'static')
    app = Flask(__name__, static_folder=static_path, static_url_path='/static')

    col = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's']
    row = ['s', 'r', 'q', 'p', 'o', 'n', 'm', 'l', 'k', 'j', 'i', 'h', 'g', 'f', 'e', 'd', 'c', 'b', 'a']

    # 获取当前日期
    today = datetime.now().strftime("%m%d-%H%M")

    filename = today + '.sgf'

    with open(filename, 'w', encoding='utf-8') as file:
        file.write('(;GM[1]FF[4]CA[UTF-8]RU[Chinese]SZ[19]KM[7.5]\n')
    sgf_set = set()

    UPLOAD_FOLDER = 'uploads'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # 确保上传目录存在
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    sl_policy = current_dir + '/alphago_sl_policy.h5'
    rl_policy = current_dir + '/alphago_rl_policy.h5'
    value_policy = current_dir + '/alphago_value.h5'

    fast_policy = load_prediction_agent(h5py.File(sl_policy, 'r'))
    strong_policy = load_policy_agent(h5py.File(rl_policy, 'r'))
    value = load_value_agent(h5py.File(value_policy, 'r'))

    Random_Bot = FastRandomBot()
    Alphago_Bot = AlphaGoMCTS(strong_policy, fast_policy, value)

    sgf_list = list()


    @app.route('/')
    def welcome():
        file_path = os.path.join(static_path, 'Alphago.html')
        if os.path.isfile(file_path):
            return send_from_directory(static_path, 'Alphago.html')
        else:
            return "File Not Found", 404

    # alphaGo机器人
    @app.route('/select-move/alphagoBot', methods=['POST'])
    def alphagoBot_move():
        content = request.json
        board_size = content['board_size']
        game_state = goboard.GameState.new_game(board_size)

        for move in content['moves']:
            if move == 'pass':
                next_move = goboard.Move.pass_turn()
            elif move == 'resign':
                next_move = goboard.Move.resign()
            else:
                next_move = goboard.Move.play(point_from_coords(move))
            game_state = game_state.apply_move(next_move)

        bot_move = Alphago_Bot.select_move(game_state)

        if bot_move.is_pass:
            bot_move_str = 'pass'
        elif bot_move.is_resign:
            bot_move_str = 'resign'
        else:
            bot_move_str = coords_from_point(bot_move.point)
        return jsonify({
            'bot_move': bot_move_str,
            'diagnostics': Alphago_Bot.diagnostics()
        })


    # 保存棋谱
    @app.route('/saveSGF', methods=['POST'])
    def save_SGF():
        content = request.json

        for move in content['moves']:
            sgf_set.add(move)
        count = 0

        with open(filename, 'a', encoding='utf-8') as file:
            for move in sgf_set:
                move = move.lower()
                if len(move) == 3:
                    c = chr(ord(move[0]) - 1)
                    r = int(move[1:3]) - 1
                else:
                    c = chr(ord(move[0]) - 1)
                    r = int(move[1:2]) - 1
                if count % 2 == 0:
                    file.write(";B[" + c + row[r] + "]\n")
                else:
                    file.write(";W[" + c + row[r] + "]\n")
                count += 1
            file.write(")")
        return jsonify({'message': 'File save successfully.'}), 200


    # 上传SGF棋谱
    @app.route('/upload', methods=['POST'])
    def upload_file():
        if 'file' not in request.files:
            return jsonify({'error': 'No file part in the request'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if file:
            filename = file.filename
            sgf_list.append(filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            return jsonify({'message': 'File uploaded successfully.'}), 200


    # 加载SGF棋谱
    @app.route('/loadSGF', methods=['POST'])
    def loadSGF():
        move_list = list()
        sgf_filename = "uploads/" + str(sgf_list[-1])
        with open(sgf_filename, 'rb') as sgf_file:
            sgf_content = sgf_file.read()

        sgf_game = Sgf_game.from_string(sgf_content)
        for item in sgf_game.main_sequence_iter():

            color, move_tuple = item.get_move()
            if color is not None and move_tuple is not None:
                row, col = move_tuple
                point = Point(row + 1, col + 1)
                move = Move.play(point)
                bot_move_str = coords_from_point(move.point)
                move_list.append(bot_move_str)
        return jsonify({
            'list': move_list,
            'diagnostics': Random_Bot.diagnostics()
        })


    # AI自我对弈
    @app.route('/selfPlay', methods=['POST'])
    def selfPlay():
        move_list = list()
        content = request.json
        board_size = content['board_size']
        game_state = goboard.GameState.new_game(board_size)

        bots = {
            gotypes.Player.black: Random_Bot,
            # gotypes.Player.black: Alphago_Bot,
            gotypes.Player.white: Alphago_Bot,
        }
        for i in range(20):
            bot_move = bots[game_state.next_player].select_move(game_state)
            if game_state.is_valid_move(Move.play(bot_move.point)) and \
                    not is_point_an_eye(game_state.board,
                                        bot_move.point,
                                        game_state.next_player):
                pass
            else:
                bot_move.is_pass = True
            game_state = game_state.apply_move(bot_move)
            bot_move_str = coords_from_point(bot_move.point)
            move_list.append(bot_move_str)

        return jsonify({
            'list': move_list,
            'diagnostics': Random_Bot.diagnostics()
        })


    app.run()
