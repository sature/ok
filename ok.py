import ccxt
from utils.Shout import Shout
from utils.K2 import K

# Shout.login();
Shout.send("程序启动！");

market_symbol = 'EOS/USDT'
okex = ccxt.okex({'apiKey': '3bc75ab2-37d6-43bc-b7f7-733999eff040', 'secret': 'C6B6B482C796E804F45CE715CAA4FCD3'})
okex.load_markets()

# List all the markets of the exchange
# symbols = []
# for market in okex.fetch_markets():
#     symbols.append(market['symbol'])
# print(symbols)

# Order book
# print(okex.fetch_order_book(market_symbol, 5))

# Market Price
# orderbook = okex.fetch_order_book(market_symbol)
# bid = orderbook['bids'][0][0] if len(orderbook['bids']) > 0 else None
# ask = orderbook['asks'][0][0] if len(orderbook['asks']) > 0 else None
# spread = (ask - bid) if (bid and ask) else None
# print(okex.id, 'market price', {'bid': bid, 'ask': ask, 'spread': spread})

# Price ticker
# print(okex.id, 'price ticker', okex.fetch_ticker(market_symbol))
okex.options['defaultContractType'] = 'quarter'
print(okex.id, 'price ticker', okex.fetch_ticker("EOS/USD"))

# Candlestick charts
# CandleSticksStore(okex, market_symbol).start()

# Trades
# trade = okex.fetch_trades(market_symbol)
# print(okex.id, len(trade), trade)

# Balance
# balance = okex.fetch_balance()
# print(okex.id, 'my EOS balance:', balance['EOS'])
#
# print(okex.id, 'user info:', okex.private_post_future_userinfo())

# print(Bool(okex, market_symbol, '1m').boll(20))
# DualThrust(okex, market_symbol).check(5)

# all_data = pd.read_hdf('eth_1min_data.h5')
# all_data.reset_index(inplace=True, drop=True)
# print(all_data)
#

# df = pd.read_excel('eth_1min_k.xlsx', sheet_name='Sheet1') \
#         .append(pd.read_excel('eth_1min_k.xlsx', sheet_name='Sheet2'))
#
# period_df = pd.read_excel('eth_1min_k.xlsx', sheet_name='Sheet1') \
#               .append(pd.read_excel('eth_1min_k.xlsx', sheet_name='Sheet2')) \
#               .resample(rule='15T', on='candle_begin_time', label='left', closed='left') \
#               .agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'})
#
# # print(period_df)
#
# N = 20
# for n in range(N, len(period_df)-1):
#     signal = DualThrust(okex, market_symbol).signal(
#         period_df.loc[n-N:n], N, K1=1, K2=1, opening=period_df['open'][n], current=period_df['close'][0])
#     print(signal)
# print(period_df.rolling(20))

# print(okex.privatePostFutureUserinfo())

# K.start()
# dual_thrust = Strategy(okex, market_symbol, '1m', para={'N': 20})
#
# print(dual_thrust.k)
