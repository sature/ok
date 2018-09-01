
if __name__ == '__main__':
    import os,sys
    sys.path.append(os.path.split(os.path.realpath(__file__))[0] + '/..')
    print(sys.path)

import Strategy as S
from utils import Contract
import logging


class Chase(S):
    '''
    buy when price breaks upper boundary and sell when price leaks lower boundary
    '''

    def __init__(self, amount=1):
        S.__init__(self)
        self.status = 'clean_hands' # clean_hands/holding_buy/holding_sell
        self.amount = amount
        self.holding = 0
        self.actions = dict({
            # (break, leak)
            (True, False): dict({'clean_hands': [Contract.OrderType.BUY],
                                 'holding_buy': [],
                                 'holding_sell': [Contract.OrderType.CLOSE_SELL, Contract.OrderType.BUY]}),
            (False, True): dict({'clean_hands': [Contract.OrderType.SELL],
                                 'holding_buy': [Contract.OrderType.CLOSE_BUY, Contract.OrderType.SELL],
                                 'holding_sell': []}),
            (True, True): dict({'clean_hands': [], 'holding_buy': [], 'holding_sell': []}),
            (False, False): dict({'clean_hands': [], 'holding_buy': [], 'holding_sell': []}),
        })
        self.set_name('Chase(%d)' % self.amount)
        logging.info('Create Strategy %s' % self.name)

    def check(self, event):

        s = event.source

        for act in self.actions[(s.is_break(), s.is_leak())][self.status]:
            logging.info('Strategy(Chase) is doing %d' % act)
            if act in [Contract.OrderType.BUY, Contract.OrderType.SELL]:
                self.contract = Contract(s.symbol, s.contract_type, dry_run=True)
                self.contract.subscribe(self.contract_result)
                self.contract.order(act, price=None, amount=self.amount)
                self.status = 'holding_buy' if act == Contract.OrderType.BUY else 'holding_sell'
            elif act in [Contract.OrderType.CLOSE_BUY, Contract.OrderType.CLOSE_SELL]:
                self.contract.close(price=None)
                self.contract = None
                self.status = 'clean_hands'

    def contract_result(self, e):
        o = e.source
        currency = o.symbol[:3]
        type_c = [u'无效操作', u'开多', u'开空', u'平多', u'平空']
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


if __name__ == "__main__":

    import ccxt
    from signal.DualThrust import DualThrust
    from utils.ApiKey import ApiKey

    logging.basicConfig(level=logging.INFO)

    chase = Chase()
    s = DualThrust(ccxt.okex(ApiKey.PARAMETER), "EOS/USD", period='1min', contract_type='quarter')
    s.set_parameters(n=10, k1=0.5, k2=0.5)
    chase.add_signal(s)

