from utils import Observable
from utils import App
from flask import jsonify
import logging

logger = logging.getLogger('rich')


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

    id = 0
    signals = []

    def __init__(self, t=Type.BAND):
        Observable.__init__(self)
        self.k = None
        self.name = '-'
        self.band = None
        self.bands = []
        self.s = dict({Signal.BREAK: False, Signal.LEAK: False})
        self.params = dict({})
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

    def set_break(self, b):
        if b is True and self.s[Signal.LEAK] is True:
            self.s[Signal.LEAK] = False
        if self.s[Signal.BREAK] != b:
            self.s[Signal.BREAK] = b
            logger.info('%s: signal = {break=%r, leak=%r}' % (self.name, self.is_break(), self.is_leak()))
            self.fire()

    def is_break(self):
        return self.s[Signal.BREAK]

    def set_leak(self, l):
        if l is True and self.s[Signal.BREAK] is True:
            self.s[Signal.BREAK] = False
        if self.s[Signal.LEAK] != l:
            self.s[Signal.LEAK] = l
            logger.info('%s: signal = {break=%r, leak=%r}' % (self.name, self.is_break(), self.is_leak()))
            self.fire()

    def is_leak(self):
        return self.s[Signal.LEAK]

    def set_signal(self, current):
        if self.type == Signal.Type.BAND:
            self.set_break(current > self.band[Signal.Boundary.UPPER])
            self.set_leak(current < self.band[Signal.Boundary.LOWER])
        else:
            logger.warning('%s: set_signal() with unknown signal type %s' % (self.name, self.type))

    def set_band(self, b, timestamp=0):
        if self.type == Signal.Type.BAND:
            self.band = b
            logger.info('[%s]%s: updated band to %d: [%.3f,%.3f,%.3f]'
                        % (self.id, self.name, timestamp,
                           self.band[Signal.Boundary.LOWER],
                           self.band[Signal.Boundary.MIDDLE],
                           self.band[Signal.Boundary.UPPER])
                        )
            if (self.band is not None) and (timestamp != 0):
                self._add_bands(self.band, timestamp)

    def get_band(self):
        return self.band

    def _add_bands(self, band, timestamp):
        band['timestamp'] = timestamp
        if len(self.bands) > 0 and self.bands[-1]['timestamp'] == timestamp:
            self.bands.pop()
        self.bands.append(band)
        if len(self.bands) > self.k.MAX_LENGTH:
            del self.bands[0]

    def track(self, e):
        logging.warning('%s: track() shall be override.' % self.name)
        pass

    def update_boundary(self):
        pass

    def get_dict(self):
        return dict({
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'parameters': self.params,
            'keywords': list(self.band.keys()),
            'data': self.bands,
            'intensity': 0
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
