import pandas as pd
import threading
import ccxt
from datetime import datetime
from ccxt.base.errors import ExchangeError
import logging
from utils.Observable import Observable


class K:

    TIMESTAMP = 'timestamp'
    OPEN = 'open'
    HIGH = 'high'
    LOW = 'low'
    CLOSE = 'close'
    VOLUME = 'volume'
    BTC_VOLUME = 'btc_volume'
    COLUMNS = [TIMESTAMP, OPEN, HIGH, LOW, CLOSE, VOLUME, BTC_VOLUME]

    ks = dict()

    @staticmethod
    def k(exchange, symbol, period, contract_type):

        symbol = K.private_symbol(symbol)

        K.ks[period] = dict() if period not in K.ks.keys() else K.ks[period]

        if (exchange.name, symbol, contract_type) not in K.ks[period].keys():
            _k = _K(exchange, symbol, period, contract_type)
            K.ks[period][(exchange.name, symbol, contract_type)] = _k
            _k.start()

        return K.ks[period][(exchange.name, symbol, contract_type)]

    @staticmethod
    def private_symbol(symbol):
        return symbol if '/' not in symbol else symbol.lower().replace('/', '_')


class _K(Observable):

    MAX_LENGTH = 1000
    FAST = 2
    SLOW = 5

    def __init__(self, exchange, symbol, period, contract_type):
        Observable.__init__(self)
        self.exchange = exchange
        self.symbol = symbol
        self.period = period
        self.contract_type = contract_type
        self.name = 'K[%s/%s/%s/%s]' % (self.exchange.name, self.symbol, self.period, self.contract_type)
        self.last_period = None
        self.speed = _K.SLOW
        self.k = None
        self.started = False
        logging.info('New K instance %s' % self.name)

    def start(self):
        if not self.started:
            logging.info('%s: Started with %d seconds polling period' % (self.name, self.speed))
            self._start()
            self.started = True

    def _start(self):

        threading.Timer(self.speed, self._start).start()

        try:
            df = pd.DataFrame(self.exchange.public_get_future_kline({
                'symbol': self.symbol, 'type': self.period, 'contract_type': self.contract_type, 'size': 0,
                'since': self.last_period.name if self.last_period is not None else 0
            }), columns=K.COLUMNS)
            df.set_index(K.TIMESTAMP, inplace=True)
            self.append_data(df)
        except ExchangeError as e:
            logging.error("Error retrieving Kline for %s" % self.name)
            logging.info(str(e))
            return

    def append_data(self, df):
        if len(df) == 0:
            logging.warning('(%s) received data frame with length 0, skipped it' % self.name)
            return
        self.k = df.combine_first(self.k) if self.k is not None else df
        last_period = self.k.iloc[-1]
        self.k = self.k.tail(_K.MAX_LENGTH)
        new_k = True if (self.last_period is None) or (self.timestamp() != last_period.name) else False
        self.last_period = last_period
        logging.info('%s: Firing new K, timestamp = %d' % (self.name, self.timestamp()))
        self.fire(new_k=new_k)

    def data(self):
        return self.k

    def timestamp(self):
        return self.last_period.name

    def current(self):
        return self.last_period


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    def gaga(event):
        k = event.source
        print(datetime.now(), len(k.data()), k.timestamp(), k.current()[K.VOLUME], event.new_k)

    k = K.k(ccxt.okex(), symbol='eos_usd', period='1min', contract_type='quarter')
    k.subscribe(gaga)
    k.start()
