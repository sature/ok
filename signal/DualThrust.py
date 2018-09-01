from utils.K import K
from signal.Signal import Signal
import logging


class DualThrust(Signal):

    N = 'N'
    K1 = 'K1'
    K2 = 'K2'

    def __init__(self, exchange, symbol, period='1h', contract_type='quarter'):
        Signal.__init__(self, exchange, symbol, period, contract_type)
        self.set_name('DT(%s,%s,%s,%s)' % (exchange.name, symbol, period, contract_type))
        self.p = dict({DualThrust.N: 1, DualThrust.K1: 1, DualThrust.K2: 1})
        self.d = None

    def track(self, event):
        # event
        # {
        #   source = K._K()
        #   new_k = True/False
        # }
        o = event.source
        if event.new_k or self.get_upper() is None or self.get_lower() is None:
            self.update_boundary(o.data())
        if self.get_upper() is None or self.get_lower() is None:
            logging.info('%s, cannot work out a boundary' % self.name)
            return

        current = o.current()[K.CLOSE]

        self.set_break(current > self.get_upper())
        self.set_leak(current < self.get_lower())
        self.set_ratio(current)

        logging.info('%s: Price = %.3f, Signal = {break=(%r, %s), leak=(%r, %s)}'
                     % (self.name, current,
                        self.is_break(), '{:.1%}'.format(self.get_break_ratio()),
                        self.is_leak(), '{:.1%}'.format(self.get_leak_ratio())))

    def update_boundary(self, k):
        length = len(k)
        if length < self.p[DualThrust.N] + 1:
            # length of k lines are not enough, reset to update boundary when next k coming
            logging.warning('k length = %d, which is not enough for boundary calculation.' % length)
            self.set_upper(None)
            self.set_lower(None)
            self.set_middle(None)
            self.b = {'upper': None, 'lower': None}
            return

        opening = k.iloc[-1][K.OPEN]
        df = k.iloc[-self.p[DualThrust.N]-1:-1]
        deviation = max(df[K.HIGH].max() - df[K.CLOSE].min(), df[K.CLOSE].max() - df[K.LOW].min())
        self.set_upper(opening + self.p[DualThrust.K1] * deviation)
        self.set_lower(opening - self.p[DualThrust.K2] * deviation)
        self.set_middle(opening)

        logging.info('%s: updated boundary to (%.3f<----%.3f---->%.3f)'
                     % (self.name, self.get_lower(), self.get_middle(), self.get_upper()))

    def set_parameters(self, n, k1=1, k2=1):
        self.p = {DualThrust.N: n, DualThrust.K1: k1, DualThrust.K2: k2}
        logging.info('%s: set parameters as %s' %(self.name, self.p))


if __name__ == "__main__":

    import ccxt

    def gaga(e):
            print('DualThrust signal =', e.signal)

    logging.basicConfig(level=logging.INFO)

    s = DualThrust(ccxt.okex(), symbol='eos_usd', period='1min', contract_type='quarter')
    s.set_parameters(5, k1=0.4, k2=0.5)
    s.subscribe(gaga)
    s.start()

