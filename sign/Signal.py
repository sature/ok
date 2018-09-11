from utils import Observable
from utils import App
from flask import jsonify
import logging


class Signal(Observable):

    class Type:
        BAND = 'Band'
        MA = 'Moving Average'

    class Boundary:
        UPPER = 'upper'
        MIDDLE = 'middle'
        LOWER = 'lower'

    BREAK = 'break'
    LEAK = 'leak'
    BREAK_RATIO = 'break_ratio'
    LEAK_RATIO = 'leak_ratio'

    id = 0
    signals = []

    def __init__(self, t=Type.BAND):
        Observable.__init__(self)
        self.k = None
        self.name = '-'
        self.b = dict({Signal.Boundary.UPPER: None, Signal.Boundary.MIDDLE: None, Signal.Boundary.LOWER: None})
        self.s = dict({Signal.BREAK: False, Signal.LEAK: False, Signal.BREAK_RATIO: 0, Signal.LEAK_RATIO: 0})
        self.p = dict({})
        self.boundaries = []
        self.id = Signal.id
        Signal.id += 1
        self.type = t
        self.name = 'signal-%d' % self.id
        Signal.signals.append(self)

    def start(self, k):
        self.k = k
        self.k.subscribe(self.track)
        self.k.start()

    def stop(self):
        self.k.unsubscribe(self.track)
        self.k = None

    def set_type(self, t):
        self.type = t
        self.name = '%s-%d' % (t, self.id)

    def set_name(self, name):
        self.name = name

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

    def set_boundary(self, timestamp, b):
        self.b[Signal.Boundary.UPPER] = b[Signal.Boundary.UPPER]
        self.b[Signal.Boundary.MIDDLE] = b[Signal.Boundary.MIDDLE]
        self.b[Signal.Boundary.LOWER] = b[Signal.Boundary.LOWER]

    def set_ratio(self, current):
        self.s[Signal.BREAK_RATIO] = (current - self.get_middle()) / (self.get_upper() - self.get_middle())
        self.s[Signal.LEAK_RATIO] = (current - self.get_middle()) / (self.get_lower() - self.get_middle())

    def track(self, e):
        logging.warning('%s: track() shall be override.' % self.name)
        pass

    def update_boundary(self):
        pass

    def add_boundary(self, timestamp, signal):
        if self.boundaries[-1]['timestamp'] == timestamp:
            self.boundaries.pop()
        self.boundaries.append({'timestamp': timestamp, 'signal': signal})

    def get_dict(self):
        return dict({
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'parameters': self.p,
        })

    @staticmethod
    def get_signal_dict(sid):
        for s in Signal.signals:
            if s.id == sid:
                return s.get_dict()
        else:
            return dict({})

    @staticmethod
    @App.webapp.route('/signal', methods=['GET'])
    def rest_get_signals():
        return jsonify([s.get_dict() for s in Signal.signals])

    @staticmethod
    @App.webapp.route('/signal/<sid>', methods=['GET'])
    def rest_get_signal(sid):
        return jsonify(Signal.get_signal_dict(int(sid)))
