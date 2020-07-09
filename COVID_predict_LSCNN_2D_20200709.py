import pandas as pd
import datetime
from datetime import datetime
from tensorflow.keras.layers import Conv2D, Dense, \
    Input, LSTM, TimeDistributed,Bidirectional, concatenate, Flatten, MaxPool2D
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam,Nadam
from sklearn.preprocessing import scale
import numpy as np
import matplotlib.pyplot as plt

data= pd.read_csv('dataset/covid_19_data.csv')
df_data= pd.DataFrame(data)
grouped_by_date= df_data.groupby('ObservationDate')

# 일자별 누적합
cum_confirmed_by_date= grouped_by_date.sum().Confirmed
cum_death_by_date= grouped_by_date.sum().Deaths
cum_recovered_by_date= grouped_by_date.sum().Recovered

# 일일합계 구하기
confirmed_list= []
for idx in range(len(cum_confirmed_by_date)):
    if idx==0:
        confirmed_list.append(cum_confirmed_by_date[0])
    else:
        confirmed_list.append(cum_confirmed_by_date[idx]-cum_confirmed_by_date[idx-1])

confirmed_by_date= pd.Series(confirmed_list, index= cum_confirmed_by_date.index)


death_list= []
for idx in range(len(cum_death_by_date)):
    if idx==0:
        death_list.append(cum_death_by_date[0])
    else:
        death_list.append(cum_death_by_date[idx]-cum_death_by_date[idx-1])

death_by_date= pd.Series(death_list, index= cum_death_by_date.index)

recovered_list= []
for idx in range(len(cum_death_by_date)):
    if idx==0:
        recovered_list.append(cum_recovered_by_date[0])
    else:
        recovered_list.append(cum_recovered_by_date[idx]-cum_recovered_by_date[idx-1])

recovered_by_date= pd.Series(recovered_list, index= cum_recovered_by_date.index)

by_date_df= pd.concat([confirmed_by_date,death_by_date,recovered_by_date],axis= 1)
by_date_df.columns= ['confirmed','death','recovered']
scaled_df= scale(by_date_df, axis=0)

# LSCNN(conv2d)
nStep= 20
input_list= []
for i in range(nStep, len(by_date_df)):
    input_list.append(np.array(scaled_df[i-nStep:i]).reshape(-1,20,3))

output_list= []
for i in range(nStep+1, len(by_date_df)+1):
    output_list.append(np.array(scaled_df[i-nStep:i]).reshape(-1,20,3))
    
input_array_LSTM= np.array(input_list).reshape(-1,20,3)

input_list= []
for i in range(nStep, len(by_date_df)):
    input_list.append(np.array(scaled_df[i-nStep:i]).reshape(-1,20,3))

output_list= []
for i in range(nStep+1, len(by_date_df)+1):
    output_list.append(np.array(scaled_df[i-nStep:i]).reshape(-1,20,3))
    
input_array_CNN_2D= np.array(input_list).reshape(-1,20,3,1)
output_array_2D= np.array(output_list).reshape(-1,3)[-147:]
test_array_LSTM= np.array(output_list).reshape(-1,20,3)
test_array_CNN_2D= np.array(output_list).reshape(-1,20,3,1)

# LSCNN modeling
nInput_LSTM = 3
nOutput_LSTM = 3
nStep_LSTM = 20
nHidden_LSTM = 32

nStep_CNN = 20
nFeature_CNN = 3
nChannel_CNN= 1

LSTM_x = Input(batch_shape=(None, nStep_LSTM, 3))
CNN_2D_x = Input(batch_shape = (None, nStep_CNN, nFeature_CNN, nChannel_CNN))

xLstm1 = LSTM(nHidden_LSTM, return_sequences=True)(LSTM_x)
xLstm2 = Bidirectional(LSTM(nHidden_LSTM), merge_mode='concat')(xLstm1)
xFlat_LSTM= Flatten()(xLstm2)

xConv = Conv2D(filters=30, kernel_size=3, strides=1, padding = 'valid', activation='relu')(CNN_2D_x)
xPool = MaxPool2D(pool_size=(2,2), strides=1, padding='same')(xConv)
xFlat_CNN = Flatten()(xPool)
xFlatDense_CNN = Dense(64, activation= 'linear')(xFlat_CNN)

Output_LSCNN = Dense(3, activation='linear')(concatenate([xFlat_LSTM,xFlatDense_CNN]))
model = Model([LSTM_x, CNN_2D_x], Output_LSCNN)
model.compile(loss='mse', optimizer=Adam(lr=0.001))

model.fit([input_array_LSTM, input_array_CNN_2D],output_array_2D, epochs=100)

pred_LSCNN_2D= model.predict([test_array_LSTM,test_array_CNN_2D])
pred_LSCNN_2D= pred_LSCNN_2D[-20:,:]

ax1 = np.arange(1, len(scaled_df) + 1)
ax2 = np.arange(len(scaled_df), len(scaled_df) + len(pred_LSCNN_2D))
plt.figure(figsize=(8, 3))
plt.plot(ax1, scaled_df, label='Time series', linewidth=1)
plt.plot(ax2, pred_LSCNN_2D, label='Estimate')
plt.axvline(x=ax1[-1],  linestyle='dashed', linewidth=1)
plt.title('LSCNN_2D')
plt.legend()
plt.show()