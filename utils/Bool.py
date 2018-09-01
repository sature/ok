import pandas as pd


class Bool:

    kline = None

    def __init__(self, exchange, symbol, period='1m'):

        self.kline = pd.DataFrame(exchange.fetch_ohlcv(symbol, period),
                                  columns=['timestamp', 'opening', 'high', 'low', 'closing', 'volume'],
                                  dtype=float)

    def boll(self, instances=20):
        k = self.kline.loc[len(self.kline)-instances:]
        mean = k['closing'].mean()
        std = k['closing'].std(ddof=1)

        return {'mean': mean, 'lower': mean-std, 'upper': mean+std}
