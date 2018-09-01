from utils.Observable import Observable
from utils.K import K
import logging


class Signal(Observable):

    class Boundary:
        UPPER = 'upper'
        MIDDLE = 'middle'
        LOWER = 'lower'

    BREAK = 'break'
    LEAK = 'leak'
    BREAK_RATIO = 'break_ratio'
    LEAK_RATIO = 'leak_ratio'

    def __init__(self, exchange, symbol, period='1h', contract_type='quarter'):
        Observable.__init__(self)
        self.exchange = exchange
        self.symbol = symbol
        self.period = period
        self.contract_type = contract_type
        self.name = 'Signal[-]'
        self.b = dict({Signal.Boundary.UPPER: None, Signal.Boundary.MIDDLE: None, Signal.Boundary.LOWER: None})
        self.s = dict({Signal.BREAK: False, Signal.LEAK: False, Signal.BREAK_RATIO: 0, Signal.LEAK_RATIO: 0})

    def set_name(self, n):
        self.name = 'Signal[%s]' % n

    def set_break(self, b, ratio=0):
        if b is True and self.s[Signal.LEAK] is True:
            self.s[Signal.LEAK] = False
        self.s[Signal.BREAK_RATIO] = ratio
        if self.s[Signal.BREAK] != b:
            self.s[Signal.BREAK] = b
            self.fire()

    def is_break(self):
        return self.s[Signal.BREAK]

    def set_leak(self, l, ratio=0):
        if l is True and self.s[Signal.BREAK] is True:
            self.s[Signal.BREAK] = False
        self.s[Signal.LEAK_RATIO] = ratio
        if self.s[Signal.LEAK] != l:
            self.s[Signal.LEAK] = l
            self.fire()

    def is_leak(self):
        return self.s[Signal.LEAK]

    def set_ratio(self, current):
        self.s[Signal.BREAK_RATIO] = (current - self.get_middle()) / (self.get_upper() - self.get_middle())
        self.s[Signal.LEAK_RATIO] = (current - self.get_middle()) / (self.get_lower() - self.get_middle())

    def get_break_ratio(self):
        return self.s[Signal.BREAK_RATIO]

    def get_leak_ratio(self):
        return self.s[Signal.LEAK_RATIO]

    def set_upper(self, b):
        self.b[Signal.Boundary.UPPER] = b

    def get_upper(self):
        return self.b[Signal.Boundary.UPPER]

    def set_middle(self, b):
        self.b[Signal.Boundary.MIDDLE] = b

    def get_middle(self):
        return self.b[Signal.Boundary.MIDDLE]

    def set_lower(self, b):
        self.b[Signal.Boundary.LOWER] = b

    def get_lower(self):
        return self.b[Signal.Boundary.LOWER]

    def set_ratio(self, current):
        self.s[Signal.BREAK_RATIO] = (current - self.get_middle()) / (self.get_upper() - self.get_middle())
        self.s[Signal.LEAK_RATIO] = (current - self.get_middle()) / (self.get_lower() - self.get_middle())

    def start(self):
        k = K.k(self.exchange, symbol=self.symbol, period=self.period, contract_type=self.contract_type)
        k.subscribe(self.track)
        k.start()

    def track(self, event):
        logging.warning('%s: track() shall be override.' % self.name)
        pass

    def update_boundary(self):
        pass
