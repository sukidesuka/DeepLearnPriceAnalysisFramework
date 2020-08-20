import torch
import torch.nn as nn
import torch.nn.functional as F


class FullConnectedNetwork(nn.Module):
    def __init__(self, input_size, hidden_size, hidden_layer, output_size):
        """
        构建一个全连接神经网络
        Args:
            input_size:
            hidden_size:
            hidden_layer:
            output_size:
        """
        super(FullConnectedNetwork, self).__init__()
        # 普通的全连接神经网络
        self.layers = []        # 用来存神经网络层对象
        # 加入输入层
        self.layers.append(nn.Linear(input_size, hidden_size))
        for i in range(hidden_layer):
            # 加入指定层数的隐藏层
            self.layers.append(nn.Linear(hidden_size, hidden_size))
        # 加入输出层
        self.layers.append(nn.Linear(hidden_size, output_size))

    def forward(self, x):
        for i in range(len(self.layers)):
            x = F.softmax(self.layers[i](x))
        return x


class LSTMNetwork(nn.Module):
    def __init__(self, input_size, hidden_size, hidden_layers, output_size, drop_rate, batch_first=True):
        """
        構建一個LSTM神經網絡結構
        """
        super(LSTMNetwork, self).__init__()

        self.rnn = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=hidden_layers,
            dropout=drop_rate,
            batch_first=batch_first
        )
        self.hidden_out = nn.Linear(hidden_size, output_size)
        self.h_s = None
        self.h_c = None

    def forward(self, x):
        r_out, (h_s, h_c) = self.rnn(x)
        output = self.hidden_out(r_out)
        return output