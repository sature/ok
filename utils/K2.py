import pandas as pd
import ccxt
import threading
import datetime as dt
import logging
import time
from ccxt.base.errors import ExchangeError


class Event(object):
    pass


class Observable(object):

    def __init__(self):
        self.callbacks = []
        pass

    def subscribe(self, callback):
        self.callbacks.append(callback)
        pass

    def fire(self, **attrs):
        e = Event()
        e.source = self
        for k, v in attrs.items():
            setattr(e, k, v)
        for fn in self.callbacks:
            fn(e)


class _K(Observable):

    latest_timestamp = None

    TIMESTAMP = 'timestamp'
    OPEN = 'open'
    HIGH = 'high'
    LOW = 'low'
    CLOSE = 'close'
    VOLUME = 'volume'
    BTC_VOLUME = 'btc_volume'
    COLUMNS = [TIMESTAMP, OPEN, HIGH, LOW, CLOSE, VOLUME]
    FUTURE_COLUMNS = [TIMESTAMP, OPEN, HIGH, LOW, CLOSE, VOLUME, BTC_VOLUME]

    MAX_LENGTH = 1440

    k = None

    def __init__(self, exchange, symbol, period, fast_mode=False):
        Observable.__init__(self)
        self.exchange = exchange
        self.symbol = symbol
        # check if it's coin/coin contract for coin/usd future contract
        underlines = [pos for pos, char in enumerate(symbol) if char == '_']
        if len(underlines) <= 1:
            self.future_contract_type = None
        else:
            self.future_symbol = symbol[:underlines[1]]
            self.future_contract_type = symbol[underlines[1]+1:]

        logging.info('Symbol=%s, Contract Type=%s' % (self.symbol, self.future_contract_type))

        self.period = period
        self.period_counts = exchange.parse_timeframe(period) * 1000

        self.fast_mode = fast_mode

    def data_frame(self, samples=1):
        return self.k.loc[len(self.k) - samples:]

    def update(self, till):
        till = self.align_timestamp(till)

        for i in range(self.exchange.parse_timeframe('2m')):
            try:
                if self.future_contract_type is None:
                    df = pd.DataFrame(self.exchange.fetch_ohlcv(self.symbol, self.period,
                                                                since=self.get_last_timestamp()),
                                      columns=self.COLUMNS)
                else:
                    df = pd.DataFrame(self.exchange.public_get_future_kline({
                            'symbol': self.symbol,
                            'type': self.get_future_period(),
                            'contract_type': self.future_contract_type,
                            'size': 0,
                            'since': self.get_last_timestamp()
                        }),
                        columns=self.FUTURE_COLUMNS)
                self.append_data(df)
            except ExchangeError as e:
                logging.info('(%s, %s, %s) Exchange Error' % (self.exchange.name, self.symbol, self.period))
                logging.info(str(e))
                continue

            if till <= self.get_last_timestamp():
                break
            logging.info('(%s, %s, %s) Expecting timestamp %s, Actual timestamp: %s' %
                         (self.exchange.name, self.symbol, self.period,
                          dt.datetime.fromtimestamp(till // 1000).strftime('%H:%M'),
                          dt.datetime.fromtimestamp(self.get_last_timestamp() // 1000).strftime('%H:%M')))
            time.sleep(1)
        else:
            logging.error('(%s, %s, %s) Tried more then 2 minutes to get latest K stripe' %
                          (self.exchange.name, self.symbol, self.period))

    def set_last_timestamp(self, df):
        self.latest_timestamp = df[self.TIMESTAMP][len(df) - 1]
        logging.info('(%s, %s, %s) Append data with timestamp %s' %
                     (self.exchange.name, self.symbol, self.period,
                      dt.datetime.fromtimestamp(self.get_last_timestamp()//1000).strftime("%Y-%m-%d %H:%M:%S")))

    def get_last_timestamp(self):
        return self.latest_timestamp

    def align_timestamp(self, timestamp):
        return timestamp - (timestamp % self.period_counts)

    def append_data(self, df):

        fire = False
        if self.future_contract_type is None and len(df) > 1:           # spot contract
            df = df.loc[1:]
            df.reset_index(level=0, inplace=True, drop=True)
            self.k = self.k.append(df) if self.k is not None else df
            fire = True
        elif self.future_contract_type is not None and len(df) > 0:     # future contract
            # remove the last one, which is working item,
            self.k = self.k.loc[:len(self.k)-2].append(df) if self.k is not None else df
            if len(df) > 1:
                fire = True
        else:
            return

        self.k.reset_index(level=0, inplace=True, drop=True)
        if len(self.k) > _K.MAX_LENGTH:
            self.k = self.k.loc[len(self.k) - _K.MAX_LENGTH:]
        self.k.reset_index(level=0, inplace=True, drop=True)
        self.set_last_timestamp(self.k)
        if fire:
            self.fire(exchange=self.exchange.name,
                      symbol=self.symbol,
                      period=self.period,
                      new_data=df, all_data=self.k)

    def get_future_period(self):
        if self.period.endswith('h'):
            return self.period + 'our'
        elif self.period.endswith('d'):
            return self.period + 'ay'
        elif self.period.endswith('w'):
            return self.period + 'eek'
        else: # by default minutes
            return self.period + 'in'


class K:

    TIMESTAMP = 'latest_timestamp'

    ks = dict({})         # instances of class _K, hierarchically indexed by period, exchange, symbol

    @staticmethod
    def k(exchange, symbol, period, fast_mode=False):
        '''
        Create a Kline monitor
        :param exchange:
        :param symbol:
        :param period:
        :param fast_mode:
        :return:
        '''
        if period not in K.ks.keys():
            K.ks[period] = dict()
            K.ks[period][K.TIMESTAMP] = None
        if exchange.name not in K.ks[period].keys():
            K.ks[period][exchange.name] = dict()
        if symbol not in K.ks[period][exchange.name].keys():
            K.ks[period][exchange.name][symbol] = _K(exchange, symbol, period)

        K.ks[period][exchange.name][symbol].fast_mode = fast_mode

        return K.ks[period][exchange.name][symbol]

    @staticmethod
    def start():

        if not hasattr(K, 'exchange'):
            K.exchange = ccxt.okex()
            K.exchange.load_markets()
        timestamp = None
        while timestamp is None:
            try:
                timestamp = K.exchange.fetch_ticker('BTC/USDT')['timestamp']
            except ExchangeError as e:
                logging.info('Exchange Error during get timestamp from exchange %s' % K.exchange.name)
                logging.info(str(e))
        seconds = (timestamp // 1000) % K.exchange.parse_timeframe('1m')
        threading.Timer(K.exchange.parse_timeframe('1m') - seconds, K.start).start()
        logging.info('***** Retrieved timestamp from %s is %s, %d seconds misaligned *****' %
                     (K.exchange.name,
                      dt.datetime.utcfromtimestamp(timestamp//1000).strftime('%Y-%m-%d %H:%M:%S'),
                      seconds))

        ''' Periodical procedure starts here'''
        for period in K.ks.keys():
            if K.get_timestamp(period) is None or K.timestamp_expired(period, timestamp):
                K.set_timestamp(period, timestamp)
                for exchange_name in K.ks[period].keys():
                    if exchange_name == K.TIMESTAMP:
                        continue
                    for symbol in K.ks[period][exchange_name].keys():
                        threading.Thread(target=K.ks[period][exchange_name][symbol].update,
                                         args=(timestamp, )).start()

    @staticmethod
    def set_timestamp(period, timestamp):
        K.ks[period][K.TIMESTAMP] = timestamp - (timestamp % (K.exchange.parse_timeframe(period) * 1000))

    @staticmethod
    def get_timestamp(period):
        return K.ks[period][K.TIMESTAMP]

    @staticmethod
    def timestamp_expired(period, timestamp):
        waits = K.exchange.parse_timeframe(period) * 1000
        return True if timestamp - K.get_timestamp(period) >= waits else False


def gaga(e):
    print('[%s]' % dt.datetime.now(),
          'Get notification for (%s, %s, %s).' % (e.exchange, e.symbol, e.period),
          'Updated length of candle stripes %d/%d' % (len(e.new_data), len(e.all_data)))
    print(e.all_data)
    print(e.new_data)


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    okex = ccxt.okex()

    # K.k(okex, 'EOS/USDT', '1m').subscribe(gaga)
    # K.k(okex, 'EOS/USDT', '3m').subscribe(gaga)
    # K.k(okex, 'BTC/USDT', '5m').subscribe(gaga)
    K.k(okex, 'eos_usd_quarter', '3m').subscribe(gaga)

    K.start()