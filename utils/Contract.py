import threading
import ccxt
import time
import logging
from Observable import Observable
from Application import Application as App
from ccxt.base.errors import ExchangeError, RequestTimeout


class ContractException(Exception):
    pass


class Contract(Observable):

    class ContractType:
        THIS_WEEK = 'this_week'
        NEXT_WEEK = 'next_week'
        QUARTER = 'quarter'

    class OrderType:
        BUY = 1
        SELL = 2
        CLOSE_BUY = 3
        CLOSE_SELL = 4

    class Status:
        NONE = 'none'
        ORDERING = 'ordering'
        ORDERED = 'ordered'
        CANCELLING = 'cancelling'
        CANCELLED = 'cancelled'
        CLOSING = 'closing'
        CLOSED = 'closed'

    FEE_RATE = 0.0001

    def __init__(self, symbol, contract_type=ContractType.QUARTER, dry_run=False):
        Observable.__init__(self)
        self.id = None
        self.dry_run = dry_run

        for i in range(5):
            try:
                self.exchange = ccxt.okex({'API_KEY': App.config.get('OKEX', 'API_KEY'), 'SECRET': App.config.get('OKEX', 'SECRET')})
                self.exchange.load_markets()
                self.exchange.options['defaultContractType'] = contract_type
                break
            except ExchangeError as e:
                logging.error('Error loading exchange')
                logging.error(str(e))
        else:
            raise ContractException('Can not load exchange')

        self.symbol = symbol
        self.contract_type = contract_type

        self.status = Contract.Status.NONE
        self.order_type = None

        self.price = None
        self.cost = None
        self.margin = 0
        self.margin_rate = 0
        self.fee = 0
        self.guarantee = 20

        self.amount = 0
        self.filled = 0
        self.remaining = 0
        self.lever_rate = 10

        self.timestamp = None

    def order(self, order_type, price=None, amount=1):
        '''
        issue the order
        :param order_type: could be BUY_CONTRACT or SELL_CONTRACT
        :param price: no price is indicated, use best price queried from buy_1 or sell_1
        :param amount:
        :return:
        '''

        self.price = price
        self.amount = amount
        self.order_type = order_type

        if self.dry_run:
            (ask, bid, timestamp) = self._get_current_price()
            self.price = bid if self.order_type == Contract.OrderType.SELL else ask
            self.id = 0
            self.status = Contract.Status.ORDERED
            self.timestamp = timestamp
            self.filled = self.amount
            self.remaining = 0

            # 结帐
            if self.order_type == Contract.OrderType.BUY:
                self.margin += 10 * self.amount / self.price
                self.margin_rate = self.margin / self.guarantee
                self.fee += 10 * self.amount / self.price * Contract.FEE_RATE
            else:
                self.margin -= 10 * self.amount / self.price
                self.margin_rate = self.margin / self.guarantee
                self.fee += 10 * self.amount / self.price * Contract.FEE_RATE

            self.fire()

        else:
            result = self.exchange.create_order(symbol=self.symbol,
                                                type='market' if price is None else 'limit',
                                                side=order_type,
                                                amount=amount,
                                                price=price)

            if result['info']['result']:
                # result = {
                #     'info': {
                #         'result': True,
                #         'order_id': 1334377421751296
                #     },
                #     'id': '1334377421751296',
                #     'timestamp': 1535096983844,
                #     'datetime': '2018-08-24T07:49:43.844Z',
                #     'lastTradeTimestamp': None,
                #     'status': None,
                #     'symbol': 'EOS/USD',
                #     'type': 'limit',
                #     'side': 1,
                #     'price': 4.5,
                #     'amount': 1,
                #     'filled': None,
                #     'remaining': None,
                #     'cost': None,
                #     'trades': None,
                #     'fee': None
                # }
                self.id = result['id']
                self.remaining = amount
                self.status = Contract.Status.ORDERING
                threading.Thread(target=self.check).start()
                self.fire()
            else:
                raise ContractException('Returned failure during ordering order %s %s(%f)'
                                        % (self.order_type, self.symbol, self.amount))

    def cancel(self):

        if not (self.status == Contract.Status.ORDERING or self.status == Contract.Status.CLOSING):
            return

        for i in range(5):
            try:
                result = self.exchange.cancel_order(id=self.id, symbol=self.symbol)
                break
            except ExchangeError as e:
                logging.error('ExchangeError during cancelling the order')
                logging.error(str(e))
        else:
            raise ContractException('ExchangeError during cancelling the order')
        # result = {
        #     'result': True,
        #     'order_id': '1334802511049728'
        # }
        if result['result']:
            self.filled = 0 if self.status == Contract.Status.ORDERING else self.amount
            self.remaining = 0 if self.status == Contract.Status.CLOSING else self.amount
            self.status = Contract.Status.CANCELLING
            # self.fire() is invoked in check()
        else:
            raise ContractException('Returned failure during cancelling order %s %s(%f)'
                                    % (self.order_type, self.symbol, self.amount))

    def close(self, price=None):
        '''
        close the order
        :param price:
        :param amount: -1 if close all amount
        :return:
        '''
        if self.status == Contract.Status.ORDERING:
            self.cancel()

        while self.status == Contract.Status.ORDERING \
                or self.status == Contract.Status.CLOSING \
                or self.status == Contract.Status.CANCELLING:
            time.sleep(1)

        if self.status == Contract.Status.CLOSED or self.filled == 0:
            return

        self.price = price

        if self.order_type == Contract.OrderType.BUY:
            self.order_type = Contract.OrderType.CLOSE_BUY
        elif self.order_type == Contract.OrderType.SELL:
            self.order_type = Contract.OrderType.CLOSE_SELL

        if self.dry_run:
            (ask, bid, timestamp) = self._get_current_price()
            self.price = bid if self.order_type == Contract.OrderType.CLOSE_BUY else ask
            self.id = 0
            self.status = Contract.Status.CLOSED
            self.timestamp = timestamp
            self.filled = 0
            self.remaining = self.amount

            # 结帐
            if self.order_type == Contract.OrderType.CLOSE_SELL:
                self.margin += 10 * self.amount / self.price
                self.margin_rate = self.margin / self.guarantee
                self.fee += 10 * self.amount / self.price * Contract.FEE_RATE
            else:
                self.margin -= 10 * self.amount / self.price
                self.margin_rate = self.margin / self.guarantee
                self.fee += 10 * self.amount / self.price * Contract.FEE_RATE

            self.fire()

        else:
            result = self.exchange.create_order(symbol=self.symbol,
                                                type='market' if price is None else 'limit',
                                                side=self.order_type,
                                                amount=self.filled,
                                                price=price)
            # result = {
            #     'info': {
            #         'result': True,
            #         'order_id': 1334607754703874
            #     },
            #     'id': '1334607754703874',
            #     'timestamp': 1535100498284,
            #     'datetime': '2018-08-24T08:48:18.284Z',
            #     'lastTradeTimestamp': None,
            #     'status': None,
            #     'symbol': 'EOS/USD',
            #     'type': 'market',
            #     'side': 3,
            #     'price': None,
            #     'amount': 1,
            #     'filled': None,
            #     'remaining': None,
            #     'cost': None,
            #     'trades': None,
            #     'fee': None
            # }
            if result['info']['result']:
                self.id = result['id']
                self.status = Contract.Status.CLOSING
                self.timestamp = result['timestamp']
                threading.Thread(target=self.check).start()
                self.fire()
            else:
                raise ContractException('Returned failure during closing order %s %s(%f)'
                                        % (self.order_type, self.symbol, self.amount))

    def check(self):

        # will never check if in dry_run mode
        if self.dry_run:
            return

        while True:
            for i in range(5):
                try:
                    result = self.exchange.fetch_order(id=self.id, symbol=self.symbol)
                    break
                except RequestTimeout as e:
                    logging.error('error fetching order info')
                    logging.error(str(e))
            else:
                raise ContractException('RequestTimeout during fetching order info')
            # {
            #     'info': {
            #         'symbol': 'eos_usd',
            #         'lever_rate': 10,
            #         'amount': 1,
            #         'fee': 0,
            #         'contract_name': 'EOS0928',
            #         'unit_amount': 10,
            #         'type': 1,
            #         'price_avg': 0,
            #         'deal_amount': 0,
            #         'price': 4.5,
            #         'create_date': 1535096983000,
            #         'order_id': 1334377421751296,
            #         'status': 0
            #     },
            #     'id': '1334377421751296',
            #     'timestamp': 1535096983000,
            #     'datetime': '2018-08-24T07:49:43.000Z',
            #     'lastTradeTimestamp': None,
            #     'symbol': 'EOS/USD',
            #     'type': 'margin',
            #     'side': 'buy',
            #     'price': 4.5,
            #     'average': 0.0,
            #     'cost': 0.0,
            #     'amount': 1.0,
            #     'filled': 0.0,
            #     'remaining': 1.0,
            #     'status': 'open',
            #     'fee': None
            # }

            if self.status == Contract.Status.CANCELLING:
                self.status = Contract.Status.CANCELLED
                self.fire()
                break
            elif result['remaining'] > 0:
                # not done yet
                # print(result)
                time.sleep(3)
            else:
                # transaction is done
                self.timestamp = result['timestamp']
                self.lever_rate = result['info']['lever_rate']
                self.price = result['price']
                self.cost = result['cost']

                # 处理order的状态, 和remaining/filled
                if self.status == Contract.Status.ORDERING:
                    self.filled = result['filled']
                    self.remaining = result['remaining']
                    self.guarantee = self.amount * 10 / self.price / self.lever_rate
                    self.status = Contract.Status.ORDERED
                elif self.status == Contract.Status.CLOSING:
                    self.filled = result['remaining']
                    self.remaining = result['filled']
                    self.status = Contract.Status.CLOSED

                # 结帐
                if self.order_type == Contract.OrderType.BUY \
                        or self.order_type == Contract.OrderType.CLOSE_SELL:
                    self.margin += 10 * self.amount / self.price
                    self.margin_rate = self.margin / self.guarantee
                    self.fee += result['info']['fee']
                else:
                    self.margin -= 10 * self.amount / self.price
                    self.margin_rate = self.margin / self.guarantee
                    self.fee += result['info']['fee']

                self.fire()
                break

    def _get_current_price(self):
        try:
            ticker = self.exchange.fetch_ticker(self.symbol)
        except ExchangeError as e:
            logging.error(str(e) + '\nError during fetching ticker')
            raise ContractException('Error during fetching ticker')

        return ticker['ask'], ticker['bid'], ticker['timestamp']


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    type_c = [u'无效操作', u'开多', u'开空', u'平多', u'平空']

    def gaga(e):
        o = e.source
        currency = o.symbol[:3]
        if o.status == Contract.Status.ORDERING \
                or o.status == Contract.Status.CLOSING:
            print('%s_%s*%s*' % (o.symbol, o.contract_type, type_c[o.order_type]),
                  '$%.3f(%d张)' % (0 if o.price is None else o.price, o.amount))
        elif o.status == Contract.Status.ORDERED:
            print('%s_%s*%s*完成' % (o.symbol, o.contract_type, type_c[o.order_type]),
                  '$%.3f(%d张), 费用%.5f%s' % (o.price, o.amount, o.fee, currency))
        elif o.status == Contract.Status.CLOSED:
            print('%s_%s*%s*完成' % (o.symbol, o.contract_type, type_c[o.order_type]),
                  '$%.3f(%d张)' % (o.price, o.amount),
                  ', 利润%.5f%s (%s), 费用%.5f%s'
                  % (o.margin, currency, '{:.2%}'.format(o.margin_rate), o.fee, currency))
        elif o.status == Contract.Status.CANCELLED:
            print('%s_%s取消了*%s* $%.3f(%d张)' % (o.symbol, o.contract_type, type_c[o.order_type], o.price, o.amount))
        else:
            print('%s_%s错误的通知类型*%s*' % (o.symbol, o.contract_type, o.status))

    c = Contract(symbol='EOS/USD', contract_type=Contract.ContractType.QUARTER)
    c.subscribe(gaga)
    # c.order(Contract.OrderType.SELL, price=5)
    # time.sleep(20)
    # c.cancel()
    c.order(Contract.OrderType.SELL, price=5)
    time.sleep(10)
    # c.close(price=5)
    # time.sleep(10)
    # c.cancel()
    c.close()
