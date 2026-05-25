"""
@Author   :
@Time     : 2024/3/8 15:15
Function: alphago网络模型
"""
from io import StringIO

from keras.models import Sequential
from keras.layers import Dense, Flatten, Conv2D
from keras.utils import plot_model
import sys

def alphago_model(input_shape, is_policy_net=False,  # 这个布尔值选项用来在初始化时指定是策略网络还是价值网络
                  num_filters=192,  # 除最后一个卷积层外，所有层的过滤器数量都相同
                  first_kernel_size=5,
                  other_kernel_size=3):  # 第一层的核心尺寸为5, 其他层都是3
    model = Sequential()
    model.add(
        Conv2D(num_filters, first_kernel_size, input_shape=input_shape,
               padding='same', data_format='channels_first', activation='relu'))

    for i in range(2, 12):
        model.add(
            Conv2D(num_filters, other_kernel_size, padding='same',
                   data_format='channels_first', activation='relu'))

    # 策略网络
    if is_policy_net:
        model.add(
            Conv2D(filters=1, kernel_size=1, padding='same',
                   data_format='channels_first', activation='softmax'))
        model.add(Flatten())
        return model

    # 价值网络
    else:
        model.add(
            Conv2D(num_filters, other_kernel_size, padding='same',
                   data_format='channels_first', activation='relu'))
        model.add(
            Conv2D(filters=1, kernel_size=1, padding='same',
                   data_format='channels_first', activation='relu'))
        model.add(Flatten())
        model.add(Dense(256, activation='relu'))
        model.add(Dense(1, activation='tanh'))
        return model


if __name__ == '__main__':
    input_shape = (49, 19, 19)
    # alphago_sl_policy = alphago_model(input_shape, is_policy_net=True)

    # 模型编译
    # alphago_sl_policy.compile('sgd', 'categorical_crossentropy', metrics=['accuracy'])

    # plot_model(alphago_sl_policy, to_file='policy_model.png', show_shapes=True, show_layer_names=True)

    alphago_value_network = alphago_model(input_shape)
    # # plot_model(alphago_value_network, to_file='value_model.png', show_shapes=True, show_layer_names=True)
    # alphago_value_network.summary()
    # 捕获标准输出


    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()

    alphago_value_network.summary()

    # 获取保存的输出并写入文件
    with open('value_summary.txt', 'w') as f:
        f.write(mystdout.getvalue())

        # 恢复标准输出
    sys.stdout = old_stdout

    # 关闭StringIO对象
    mystdout.close()