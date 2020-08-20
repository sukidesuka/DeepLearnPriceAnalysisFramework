import torch
import torch.nn as nn
import torch.optim as optim
import learning
import database
import matplotlib.pylab as plt
import copy
import talib as ta
import numpy as np
from torch.utils.data import Dataset, DataLoader
from typing import List
from LogSystem import LogSystem


class MyDataset(Dataset):
    def __init__(self, data_x: List, data_y: List):
        """
        用於訓練黃金的數據集
        """
        # 將list轉爲tensor
        device = torch.device('cuda:0')
        self.data_x = torch.tensor(data_x).float().to(device)
        self.data_y = torch.tensor(data_y).float().to(device)

    def __getitem__(self, item):
        return self.data_x[item], self.data_y[item]

    def __len__(self):
        return len(self.data_x)


# 连接数据库以获取训练数据
price_db = database.PriceDatabase('price_db.csv')
df = price_db.get_df()
print(df)
# 仅保留收市价格
df = df[['date_y', 'date_m', 'date_d', 'gold_price', 'silver_price']]
print(df.tail(20))

# 将价格前向填充
df = df.fillna(method='ffill')
print(df.tail(20))

inputs = []
# 構建原始序列
inputs.append(df['gold_price'].values)
inputs.append(df['silver_price'].values)

# 构建出ma序列
inputs.append(ta.MA(df['gold_price'], timeperiod=5))
inputs.append(ta.MA(df['gold_price'], timeperiod=10))
inputs.append(ta.MA(df['gold_price'], timeperiod=20))
inputs.append(ta.MA(df['gold_price'], timeperiod=30))
inputs.append(ta.MA(df['gold_price'], timeperiod=60))
inputs.append(ta.MA(df['gold_price'], timeperiod=120))
inputs.append(ta.MA(df['gold_price'], timeperiod=240))
inputs.append(ta.MA(df['silver_price'], timeperiod=5))
inputs.append(ta.MA(df['silver_price'], timeperiod=10))
inputs.append(ta.MA(df['silver_price'], timeperiod=20))
inputs.append(ta.MA(df['silver_price'], timeperiod=30))
inputs.append(ta.MA(df['silver_price'], timeperiod=60))
inputs.append(ta.MA(df['silver_price'], timeperiod=120))
inputs.append(ta.MA(df['silver_price'], timeperiod=240))

# 构建出eam序列
inputs.append(ta.EMA(df['gold_price'], timeperiod=5))
inputs.append(ta.EMA(df['gold_price'], timeperiod=10))
inputs.append(ta.EMA(df['gold_price'], timeperiod=20))
inputs.append(ta.EMA(df['gold_price'], timeperiod=30))
inputs.append(ta.EMA(df['gold_price'], timeperiod=60))
inputs.append(ta.EMA(df['gold_price'], timeperiod=120))
inputs.append(ta.EMA(df['gold_price'], timeperiod=240))
inputs.append(ta.EMA(df['silver_price'], timeperiod=5))
inputs.append(ta.EMA(df['silver_price'], timeperiod=10))
inputs.append(ta.EMA(df['silver_price'], timeperiod=20))
inputs.append(ta.EMA(df['silver_price'], timeperiod=30))
inputs.append(ta.EMA(df['silver_price'], timeperiod=60))
inputs.append(ta.EMA(df['silver_price'], timeperiod=120))
inputs.append(ta.EMA(df['silver_price'], timeperiod=240))

# 构建出ball序列
upper_band, middle_band, lower_band = \
    ta.BBANDS(df['gold_price'], timeperiod=20)
inputs.append(upper_band)
inputs.append(middle_band)
inputs.append(lower_band)
upper_band, middle_band, lower_band = \
    ta.BBANDS(df['silver_price'], timeperiod=20)
inputs.append(upper_band)
inputs.append(middle_band)
inputs.append(lower_band)

# 將輸入數據的行和列進行轉置
inputs = np.array(inputs)
inputs = np.transpose(inputs)

# 構建輸出數據
outputs = np.array([[x] for x in df['gold_price']])

print(inputs.shape)
print(outputs.shape)

train_x = inputs[239:10000]
train_y = outputs[240:10001]
valid_x = inputs[10000: len(inputs) - 1]
valid_y = outputs[10001:]

# 轉爲數據集
train_dataset = MyDataset(train_x, train_y)
valid_dataset = MyDataset(valid_x, valid_y)

# 放入加載器
train_loader = DataLoader(dataset=train_dataset, batch_size=64, shuffle=False)
valid_loader = DataLoader(dataset=valid_dataset, batch_size=64, shuffle=False)

EPOCH = 2

# 設置設備
device = torch.device("cuda:0")
torch.manual_seed(0)

# 新建神经网络
net = learning.LSTMNetwork(input_size=len(train_x[0]), hidden_size=100, hidden_layers=5,
                           output_size=1, drop_rate=0.8).to(device)

print(net)

# 构建优化器
optimizer = optim.Adam(net.parameters(), lr=0.01)

# 构建损失函数
loss_func = nn.MSELoss()

# 定义学习率衰减点，训练到50%和75%时学习率缩小为原来的1/10
mult_step_scheduler = torch.optim.lr_scheduler.MultiStepLR(optimizer,
                             milestones=[EPOCH//2, EPOCH//4*3], gamma=0.1)

# 开始训练
train_loss = []
valid_loss = []
min_valid_loss = np.inf
for i in range(EPOCH):
    total_train_loss = []
    net.train()     # 進入訓練模式
    for step, (b_x, b_y) in enumerate(train_loader):
        b_x = b_x.view(-1, 1, len(train_x[0]))
        b_y = b_y
        prediction = net(b_x)
        loss = loss_func(prediction[:, -1, :], b_y[0])
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        total_train_loss.append(loss.item())
    train_loss.append(np.mean(total_train_loss))

    total_valid_loss = []
    net.eval()      # 進入驗證模式
    for step, (b_x, b_y) in enumerate(valid_loader):
        b_x = b_x.view(-1, 1, len(train_x[0]))
        b_y = b_y
        with torch.no_grad():
            prediction = net(b_x)
        loss = loss_func(prediction[:, -1, :], b_y[0])
        total_valid_loss.append(loss.item())
    valid_loss.append(np.mean(total_valid_loss))

    if valid_loss[-1] < min_valid_loss:
        torch.save({'epoch': i, 'model': net, 'train_loss': train_loss,
                    'valid_loss': valid_loss}, './LSTM.model')
        torch.save(optimizer, './LSTM.optim')
        min_valid_loss = valid_loss[-1]

    # 編寫日志
    log_string = ('iter: [{:d}/{:d}], train_loss:{:0.6f}, valid_loss:{:0.6f}, '
                  'best_valid_loss:{:0.6f}, lr:{:0.7f}').format((i+1), EPOCH,
                                                                train_loss[-1],
                                                                valid_loss[-1],
                                                                min_valid_loss,
                                                                optimizer.param_groups[0]['lr'])
    mult_step_scheduler.step()  # 学习率更新
    log = LogSystem('log.txt')
    log.write(log_string)





# plt.plot([x[6] for x in inputs])
# plt.show()

# plt.plot(df['gold_price'])
# plt.plot(df['silver_price'])
# # plt.show()





