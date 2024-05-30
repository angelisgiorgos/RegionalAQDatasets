import warnings

warnings.filterwarnings('ignore')

import os
import numpy as np
import pandas as pd
import glob
import re
import torch
from sklearn.preprocessing import StandardScaler
from src.utils.timefeatures import time_features


class Dataset_AirQuality(torch.utils.data.Dataset):
    def __init__(self,
                 args,
                 root_path,
                 data_path='athens.csv',
                 flag='train',
                 size=None,
                 features='S',
                 target='NO2',
                 station_name=None,
                 scale=True,
                 timeenc=0,
                 seasonal_patterns=None,
                 freq='h'):
        # size [seq_len, label_len, pred_len]
        if size == None:
            self.seq_len = 24 * 4 * 4
            self.label_len = 24 * 4
            self.pred_len = 24 * 4
        else:
            self.seq_len = size[0]
            self.label_len = size[1]
            self.pred_len = size[2]

        assert flag in ['train', 'test', 'val']
        type_map = {'train': 0, 'val': 1, 'test': 2}
        self.set_type = type_map[flag]

        self.args = args
        self.features = features
        self.target = target
        self.scale = scale
        self.timeenc = timeenc
        self.freq = freq
        self.station_name = station_name

        self.root_path = root_path
        self.data_path = data_path
        self.seasonal_patterns = seasonal_patterns
        self.__read_data__()

    def __read_data__(self):
        self.scaler = StandardScaler()
        df_raw = pd.read_csv(os.path.join(self.root_path,
                                          self.data_path))

        if self.station_name is not None:
            df_raw = df_raw[df_raw["station_name"] == self.station_name]

        num_train = int(len(df_raw) * 0.7)
        num_test = int(len(df_raw) * 0.2)
        num_vali = len(df_raw) - num_train - num_test
        border1s = [0, num_train - self.seq_len, len(df_raw) - num_test - self.seq_len]
        border2s = [num_train, num_train + num_vali, len(df_raw)]
        border1 = border1s[self.set_type]
        border2 = border2s[self.set_type]

        if self.features == 'M':
            df_raw[self.target] = df_raw[self.target].interpolate()
            df_data = df_raw[self.target]
        elif self.features == 'MS':
            if isinstance(self.target, str):
                cols = [self.target]
            else:
                cols = self.target
            cols.extend(self.args.covariates)
            df_raw[cols] = df_raw[cols].interpolate()
            df_data = df_raw[cols]
        elif self.features == 'S':
            df_data = df_raw[[self.target]].interpolate()


        # scale data by the scaler that fits training data
        if self.scale:
            train_data = df_data[border1s[0]:border2s[0]]
            # train_data.values: turn pandas DataFrame into 2D numpy
            self.scaler.fit(train_data.values)
            data = self.scaler.transform(df_data.values)
        else:
            data = df_data.values

            # time stamp:df_stamp is a object of  and
        # has one column called 'date' like 2016-07-01 00:00:00
        df_stamp = df_raw[['Date']][border1:border2]

        # Since the date format is uncertain across different data file, we need to
        # standardize it so we call func 'pd.to_datetime'
        df_stamp['Date'] = pd.to_datetime(df_stamp.Date)

        if self.timeenc == 0:  # time feature encoding is fixed or learned
            df_stamp['month'] = df_stamp.Date.apply(lambda row: row.month, 1)
            df_stamp['day'] = df_stamp.Date.apply(lambda row: row.day, 1)
            df_stamp['weekday'] = df_stamp.Date.apply(lambda row: row.weekday(), 1)
            df_stamp['hour'] = df_stamp.Date.apply(lambda row: row.hour, 1)
            # now df_frame has multiple columns recording the month, day etc. time stamp
            # next we delete the 'date' column and turn 'DataFrame' to a list
            data_stamp = df_stamp.drop(['Date'], 1).values

        elif self.timeenc == 1:  # time feature encoding is timeF
            '''
             when entering this branch, we choose arg.embed as timeF meaning we want to 
             encode the temporal info. 'freq' should be the smallest time step, and has 
              options:[s:secondly, t:minutely, h:hourly, d:daily, b:business days, w:weekly, m:monthly], you can also use more detailed freq like 15min or 3h')
             So you should check the timestep of your data and set 'freq' arg. 
             After the time_features encoding, each date info format will be encoded into 
             a list, with each element denoting the relative position of this time point
             (e.g. Day of Week, Day of Month, Hour of Day) and each normalized within scope[-0.5, 0.5]
             '''
            data_stamp = time_features(pd.to_datetime(df_stamp['Date'].values), freq=self.freq)
            data_stamp = data_stamp.transpose(1, 0)

        # data_x and data_y are same copy of a certain part of data
        self.data_x = data[border1:border2]
        if self.features == "MS":
            self.data_y = data[border1:border2, 0]
            self.data_y = np.expand_dims(self.data_y, axis=1)
            print(self.data_x.shape, self.data_y.shape)
        else:
            self.data_y = data[border1:border2]
        self.data_stamp = data_stamp

    def __getitem__(self, index):
        s_begin = index
        s_end = s_begin + self.seq_len
        r_begin = s_end - self.label_len
        r_end = r_begin + self.label_len + self.pred_len

        seq_x = self.data_x[s_begin:s_end]
        seq_y = self.data_y[r_begin:r_end]
        seq_x_mark = self.data_stamp[s_begin:s_end]
        seq_y_mark = self.data_stamp[r_begin:r_end]

        return seq_x, seq_y, seq_x_mark, seq_y_mark

    def __len__(self):
        return len(self.data_x) - self.seq_len - self.pred_len + 1

    def inverse_transform(self, data):
        return self.scaler.inverse_transform(data)


if __name__ == '__main__':
    dataset = Dataset_AirQuality(
        root_path="D:/github-repos/AQ_Datasets/time-series",
        station_name="MAROUSI"
        )

    dataset.__read_data__()

    print(len(dataset.data_x))
