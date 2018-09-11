
if __name__ == '__main__':
    import os
    import sys
    sys.path.append(os.path.split(os.path.realpath(__file__))[0] + '/..')

import logging
from utils import K
from Signal import Signal

logger = logging.getLogger('rich')


class DualThrust(Signal):

    N = 'N'
    K1 = 'K1'
    K2 = 'K2'

    def __init__(self, n=10, k1=0.5, k2=0.5):
        Signal.__init__(self)
        self.set_type(Signal.Type.BAND)
        self.set_name('Dual Thrust')
        self.params = dict({DualThrust.N: n, DualThrust.K1: k1, DualThrust.K2: k2})
        self.d = None
        self.type = Signal.Type.BAND
        logger.info('Created signal %s' % self.name)

    def track(self, event):
        # event
        # {
        #   source = K._K()
        #   new_k = True/False
        # }
        o = event.source
        if event.new_k or self.get_band() is None:
            self.update_band(o.data())
        if self.get_band() is None:
            logger.info('%s, cannot work out a band' % self.name)
            return
        self.set_signal(o.current()[K.CLOSE])

    def update_band(self, k):

        n = self.params[DualThrust.N]
        k1 = self.params[DualThrust.K1]
        k2 = self.params[DualThrust.K2]

        length = len(k)
        if length < n + 1:
            # length of k lines are not enough, reset to update boundary when next k coming
            logger.warning('k length = %d, which is not enough for boundary calculation.' % length)
            self.set_band(None)
            return

        ts = int(k.index[-1])
        opening = k.iloc[-1][K.OPEN]
        df = k.iloc[-(n+1):-1]
        deviation = max(df[K.HIGH].max() - df[K.CLOSE].min(), df[K.CLOSE].max() - df[K.LOW].min())
        self.set_band({
            Signal.Boundary.UPPER: opening + k1 * deviation,
            Signal.Boundary.MIDDLE: opening,
            Signal.Boundary.LOWER: opening - k2 * deviation
        }, timestamp=ts)

    def update_params(self, n, k1=1, k2=1):
        self.params = {DualThrust.N: n, DualThrust.K1: k1, DualThrust.K2: k2}
        logger.info('%s: set parameters as %s' % (self.name, self.params))


if __name__ == "__main__":

    from utils import App


    def gaga(e):
            print('DualThrust sign =', e.source.s)

    App.read_config(os.path.split(os.path.realpath(__file__))[0] + '/../global.conf')

    logging.basicConfig(level=logging.INFO)

    s = DualThrust(App.get_exchange('quarter'), symbol='eos_usd', period='1min')
    s.update_params(5, k1=0.4, k2=0.5)
    s.subscribe(gaga)
    s.start()

