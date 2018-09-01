import pandas as pd
import datetime
import os.path
import threading
from utils.Shout import Shout


class CandleSticksStore:

    def __init__(self, exchange, symbol):
        self.exchange = exchange
        self.symbol = symbol
        self.filename = 'data/OHLCV/OHLCV_%s.xlsx'
        self.filename_format = '{0:%Y-%m-%d}'

    '''
    start(self)
    Pull 1m candle sticks from website every 12hours and save in xlsx format 
    '''
    def start(self):

        threading.Timer(60*60*1, self.start).start()

        df = pd.DataFrame(self.exchange.fetch_ohlcv(self.symbol),
                          columns=['timestamp', 'opening', 'high', 'low', 'closing', 'volume'])
        df.set_index('timestamp')
        df.timestamp += 1000 * 60 * 60 * 8  # UTC+8
        df = df.loc[:len(df)-2]     # remove the last item which may not the last value of the minute

        aday = 1000 * 60 * 60 * 24
        timestamp_today_starting = df.at[len(df)-1, 'timestamp'] // aday * aday
        index_of_day_starting = df.index[df['timestamp'] == timestamp_today_starting].tolist()[0]
        df_yesterday = df.loc[:index_of_day_starting-1]
        df_today = df.loc[index_of_day_starting:]
        yesterday = datetime.datetime.fromtimestamp((timestamp_today_starting - aday) / 1e3)
        today = datetime.datetime.fromtimestamp(timestamp_today_starting / 1e3)

        ''' update yesterday's record '''
        file = self.filename % self.filename_format.format(yesterday)
        if os.path.exists(file):
            ''' file exists, open to append data '''
            df_saved_yesterday = pd.read_excel(file)
            last_timestamp = df_saved_yesterday.iloc[len(df_saved_yesterday)-1]['timestamp']
            df_incremental_yesterday = df_yesterday.loc[df_yesterday.index[df_yesterday['timestamp'] > last_timestamp]]
            df_updated_yesterday = df_saved_yesterday.append(df_incremental_yesterday, ignore_index=True)
            if len(df_incremental_yesterday) > 0:
                df_updated_yesterday.to_excel(file, '1m', engine='xlsxwriter')
                Shout.send('KStore: Updated %d/%d records on %s' % (len(df_incremental_yesterday), len(df_updated_yesterday), file))
                if len(df_updated_yesterday) == 60 * 24:    # a day
                    self.generate_all_periods_candle_sticks_charts(yesterday)
        else:
            ''' file doesn't exist, write down a new one '''
            df_yesterday.to_excel(file, '1m', engine='xlsxwriter')
            Shout.send('KStore: Updated %d/%d records on %s' % (len(df_yesterday), len(df_yesterday), file))

        ''' update today's record '''
        file = self.filename % self.filename_format.format(today)
        if os.path.exists(file):
            ''' file exists, open to append data '''
            df_saved_today = pd.read_excel(file)
            last_timestamp = df_saved_today.iloc[len(df_saved_today)-1]['timestamp']
            df_incremental_today = df_today.loc[df_today.index[df_today['timestamp'] > last_timestamp]]
            df_updated_today = df_saved_today.append(df_incremental_today, ignore_index=True)
            if len(df_incremental_today) > 0:
                df_updated_today.to_excel(file, '1m', engine='xlsxwriter')
                Shout.send('KStore: Updated %d/%d records on %s' % (len(df_incremental_today), len(df_updated_today), file))
        else:
            ''' file doesn't exist, write down a new one '''
            df_today.to_excel(file, '1m', engine='xlsxwriter')
            Shout.send('KStore: Updated %d/%d records on %s' % (len(df_today), len(df_today), file))

    def generate_all_periods_candle_sticks_charts(self, day):
        Shout.send('generate other periods candle sticks charts here')

