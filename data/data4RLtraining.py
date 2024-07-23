import pandas as pd

data = pd.read_csv("weather5room.csv").set_index("index")


start_time= pd.to_datetime('2015-01-01 00:00:00',format='%Y-%m-%d %H:%M:%S')
end_time = start_time + pd.to_timedelta("31532400 s")
index = pd.date_range(start_time, end=end_time, freq="3600 s")


data['index'] = index
data = data.set_index('index')




#create a january slice
heating_months = [10,11,12,1,2,3]
heating_df = data[data.index.month.isin(heating_months)]
heating_df.to_csv("weather5room_heating.csv")
#create a heating season slice


print(index)
